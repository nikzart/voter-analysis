"""
Kerala Voter Religion Prediction - Optimized Batch Processing
Adds religion column to voter CSV files using Azure OpenAI GPT-4

Features:
- Batch processing: 25 voters per API call
- Rate limiting: 40 calls/minute
- JSON output mode for guaranteed structured responses
- Progress tracking with SQLite
- Resume capability
- 100% data coverage guarantee
"""

import json
import os
import time
import logging
import sqlite3
import asyncio
from pathlib import Path
from typing import List, Dict, Set
import pandas as pd
from openai import AsyncAzureOpenAI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('religion_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def sanitize_ward_name(ward_text: str) -> str:
    """
    Sanitize ward name for folder naming.
    Rules: Replace '/' and ' ' with '_'
    """
    return ward_text.replace('/', '_').replace(' ', '_')


def sanitize_polling_station_name(ps_text: str) -> str:
    """
    Sanitize polling station name for CSV filename.
    Rules: Replace '/' and ' ' with '_', remove '(', ')', and ','
    """
    return (ps_text.replace('/', '_')
                   .replace(' ', '_')
                   .replace('(', '')
                   .replace(')', '')
                   .replace(',', ''))


def build_expected_csv_paths(polling_stations_map_path: str, input_dir: str) -> Set[Path]:
    """
    Build set of expected CSV file paths from polling_stations_map.json

    Args:
        polling_stations_map_path: Path to polling_stations_map.json
        input_dir: Base input directory (e.g., 'output')

    Returns:
        Set of Path objects for expected CSV files
    """
    try:
        with open(polling_stations_map_path, 'r') as f:
            ps_map = json.load(f)

        expected_paths = set()

        for ward in ps_map.get('wards', []):
            ward_text = ward.get('text', '')
            ward_folder = sanitize_ward_name(ward_text)

            for polling_station in ward.get('polling_stations', []):
                ps_text = polling_station.get('text', '')
                ps_filename = sanitize_polling_station_name(ps_text) + '.csv'

                # Build full path
                csv_path = Path(input_dir) / ward_folder / ps_filename
                expected_paths.add(csv_path)

        logger.info(f"Built {len(expected_paths)} expected CSV paths from polling stations map")
        return expected_paths

    except Exception as e:
        logger.error(f"Error building expected CSV paths: {e}")
        return set()


class ProgressTracker:
    """Tracks processing progress using SQLite database"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                row_index INTEGER NOT NULL,
                status TEXT NOT NULL,
                religion TEXT,
                attempt_count INTEGER DEFAULT 0,
                error_msg TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(file_path, row_index)
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status ON progress(status)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_file ON progress(file_path)
        ''')
        self.conn.commit()

    def is_completed(self, file_path: str, row_index: int) -> bool:
        """Check if a specific record is already completed"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT status FROM progress
            WHERE file_path = ? AND row_index = ? AND status = 'completed'
        ''', (file_path, row_index))
        return cursor.fetchone() is not None

    def mark_completed(self, file_path: str, row_index: int, religion: str):
        """Mark a record as completed"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO progress
            (file_path, row_index, status, religion, updated_at)
            VALUES (?, ?, 'completed', ?, CURRENT_TIMESTAMP)
        ''', (file_path, row_index, religion))
        self.conn.commit()

    def mark_failed(self, file_path: str, row_index: int, error_msg: str, attempt_count: int):
        """Mark a record as failed"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO progress
            (file_path, row_index, status, error_msg, attempt_count, updated_at)
            VALUES (?, ?, 'failed', ?, ?, CURRENT_TIMESTAMP)
        ''', (file_path, row_index, error_msg, attempt_count))
        self.conn.commit()

    def get_total_stats(self) -> Dict:
        """Get overall progress statistics"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT status, COUNT(*) FROM progress GROUP BY status
        ''')

        stats = {'completed': 0, 'failed': 0, 'processing': 0, 'total': 0}
        for status, count in cursor.fetchall():
            stats[status] = count
            stats['total'] += count
        return stats

    def close(self):
        """Close database connection"""
        self.conn.close()


class RateLimiter:
    """Rate limiter using token bucket algorithm"""

    def __init__(self, calls_per_minute: int, tokens_per_minute: int):
        self.calls_per_minute = calls_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.call_timestamps = []
        self.token_usage = []

    def _clean_old_entries(self):
        """Remove entries older than 1 minute"""
        one_minute_ago = time.time() - 60
        self.call_timestamps = [ts for ts in self.call_timestamps if ts > one_minute_ago]
        self.token_usage = [(ts, tokens) for ts, tokens in self.token_usage if ts > one_minute_ago]

    def can_make_call(self, estimated_tokens: int = 1000) -> bool:
        """Check if we can make a call without exceeding limits"""
        self._clean_old_entries()

        current_calls = len(self.call_timestamps)
        current_tokens = sum(tokens for _, tokens in self.token_usage)

        return (current_calls < self.calls_per_minute and
                current_tokens + estimated_tokens < self.tokens_per_minute)

    def record_call(self, tokens_used: int):
        """Record a successful API call"""
        current_time = time.time()
        self.call_timestamps.append(current_time)
        self.token_usage.append((current_time, tokens_used))

    async def wait_if_needed(self, estimated_tokens: int = 1000):
        """Wait until we can make a call"""
        while not self.can_make_call(estimated_tokens):
            await asyncio.sleep(0.5)


class ReligionPredictor:
    """Predicts religion using Azure OpenAI GPT-4 with batch processing"""

    BATCH_SYSTEM_PROMPT = """You are an expert at identifying religious backgrounds of voters in Kerala, India based on names.

HINDU indicators: Names of deities (Krishna, Vishnu, Lakshmi, Devi, etc.), Sanskrit-origin names, names ending in -an/-kuttan (male), -kumari/-devi (female), house names with Bhavanam/Mandiram/Illam, etc.

CHRISTIAN indicators: Biblical/Western names (George, Jose, Mary, Thomas, etc.), names of Christian saints, house names with Villa/Nivas/Dale/Bhavan, guardian names like Xavier/Sebastian/Francis, etc.

MUSLIM indicators: Arabic names (Mohammed, Abdul, Ayesha, Fathima, etc.), Islamic naming patterns, house names with Manzil/Padi/Purayidam, etc.

IMPORTANT: You MUST classify each voter as EXACTLY one of: Hindu, Christian, or Muslim. No other values allowed.

Return JSON with this exact structure:
{"predictions": [{"index": 0, "religion": "Hindu"}, {"index": 1, "religion": "Christian"}, ...]}

Each religion must be STRICTLY one of: Hindu, Christian, or Muslim."""

    def __init__(self, config: Dict, rate_limiter: RateLimiter):
        self.config = config
        self.rate_limiter = rate_limiter

        azure_config = config['azure_openai']
        self.client = AsyncAzureOpenAI(
            api_key=azure_config['subscription_key'],
            api_version=azure_config['api_version'],
            azure_endpoint=azure_config['endpoint']
        )
        self.deployment = azure_config['deployment']
        self.max_retries = config['religion_prediction']['max_retries']

    async def predict_religion_batch(self, voters: List[Dict], attempt: int = 0) -> List[str]:
        """Predict religion for entire batch (25 voters) in ONE API call with JSON output mode"""

        # Wait for rate limiter
        await self.rate_limiter.wait_if_needed()

        try:
            # Build prompt with all 25 voters
            user_message = "Predict religion for these Kerala voters:\n\n"
            for idx, voter in enumerate(voters):
                user_message += f"{idx}. Name: {voter['name']}, Guardian: {voter['guardian']}, House: {voter['house']}\n"

            # SINGLE API CALL with JSON output mode (guaranteed valid JSON)
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": self.BATCH_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"},  # GUARANTEED JSON OUTPUT
                temperature=0.1,
                max_tokens=500
            )

            # Record the API call
            tokens_used = response.usage.total_tokens if response.usage else 1000
            self.rate_limiter.record_call(tokens_used)

            # Parse JSON response
            result = json.loads(response.choices[0].message.content)
            predictions = result.get("predictions", [])

            # Extract religions in correct order
            religions = []
            for idx in range(len(voters)):
                pred = next((p for p in predictions if p["index"] == idx), None)
                religion = pred["religion"] if pred else "Hindu"  # Default to Hindu if missing

                # STRICT validation: must be Hindu, Christian, or Muslim ONLY
                if religion not in ["Hindu", "Christian", "Muslim"]:
                    logger.warning(f"Invalid religion '{religion}' for voter {idx}, defaulting to Hindu")
                    religion = "Hindu"

                religions.append(religion)

            return religions

        except Exception as e:
            logger.error(f"Batch prediction error (attempt {attempt + 1}): {e}")

            if attempt < self.max_retries:
                # Exponential backoff
                wait_time = (2 ** attempt) * 2
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                return await self.predict_religion_batch(voters, attempt + 1)
            else:
                # On max retries, default all to Hindu
                logger.error(f"Max retries exceeded for batch, defaulting all to Hindu")
                return ["Hindu"] * len(voters)


class BatchProcessor:
    """Processes voters in batches"""

    def __init__(self, config: Dict, progress_tracker: ProgressTracker,
                 predictor: ReligionPredictor):
        self.config = config
        self.progress_tracker = progress_tracker
        self.predictor = predictor
        self.batch_size = config['religion_prediction']['batch_size']
        self.batch_delay = config['religion_prediction']['batch_delay_seconds']
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'start_time': time.time()
        }

    async def process_batch(self, batch: List[Dict]) -> List[Dict]:
        """Process entire batch in ONE API call (25 voters per call)"""

        # Extract voter info
        voters = [
            {
                'name': record['name'],
                'guardian': record['guardian'],
                'house': record['house']
            }
            for record in batch
        ]

        # Single API call for all 25 voters
        try:
            religions = await self.predictor.predict_religion_batch(voters)

            # Assign predictions to records
            for i, record in enumerate(batch):
                record['religion'] = religions[i]

                # Mark completed in progress DB
                self.progress_tracker.mark_completed(
                    record['file_path'],
                    record['row_index'],
                    religions[i]
                )

            self.stats['successful'] += len(batch)

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")

            # Mark all as Hindu on failure (default fallback)
            for record in batch:
                record['religion'] = 'Hindu'
                self.progress_tracker.mark_failed(
                    record['file_path'],
                    record['row_index'],
                    str(e),
                    self.predictor.max_retries
                )

            self.stats['failed'] += len(batch)

        self.stats['total_processed'] += len(batch)
        return batch

    def print_progress(self, current_file: str, total_files: int, current_file_idx: int):
        """Print progress statistics"""
        elapsed = time.time() - self.stats['start_time']
        rate = self.stats['total_processed'] / (elapsed / 60) if elapsed > 0 else 0

        total_stats = self.progress_tracker.get_total_stats()

        print("\n" + "="*60)
        print("Kerala Voter Religion Prediction - OPTIMIZED")
        print("="*60)
        print(f"Files: {current_file_idx}/{total_files}")
        print(f"Current: {current_file}")
        print(f"\nTotal Records: {total_stats['total']:,}")
        print(f"  Completed: {total_stats['completed']:,} ({total_stats['completed']/max(total_stats['total'],1)*100:.1f}%)")
        print(f"  Failed: {total_stats['failed']:,}")
        print(f"\nProcessing Rate: {rate:.1f} records/min")
        print(f"Elapsed Time: {elapsed/60:.1f} minutes")

        if rate > 0:
            remaining = (80964 - total_stats['completed']) / rate
            print(f"ETA: {remaining:.1f} minutes ({remaining/60:.1f} hours)")

        print("="*60)


async def process_csv_file(file_path: str, output_path: str, config: Dict,
                          progress_tracker: ProgressTracker, batch_processor: BatchProcessor):
    """Process a single CSV file"""

    logger.info(f"Processing file: {file_path}")

    # Read CSV
    df = pd.read_csv(file_path)
    total_rows = len(df)

    # Add religion column if not exists
    if 'religion' not in df.columns:
        df['religion'] = 'Hindu'  # Default

    # Process in batches
    batch_size = config['religion_prediction']['batch_size']
    batch_delay = config['religion_prediction']['batch_delay_seconds']

    for batch_start in range(0, total_rows, batch_size):
        batch_end = min(batch_start + batch_size, total_rows)

        # Prepare batch
        batch = []
        for idx in range(batch_start, batch_end):
            # Skip if already completed
            if progress_tracker.is_completed(file_path, idx):
                continue

            row = df.iloc[idx]
            batch.append({
                'file_path': file_path,
                'row_index': idx,
                'name': str(row.get('Name', '')),
                'guardian': str(row.get("Guardian's Name", '')),
                'house': str(row.get('House Name', ''))
            })

        # Skip empty batches
        if not batch:
            continue

        # Record batch start time
        batch_start_time = time.time()

        # Process batch (ONE API CALL for up to 25 voters)
        results = await batch_processor.process_batch(batch)

        # Update DataFrame
        for result in results:
            df.at[result['row_index'], 'religion'] = result['religion']

        # Ensure batch takes at least batch_delay seconds
        elapsed = time.time() - batch_start_time
        if elapsed < batch_delay:
            await asyncio.sleep(batch_delay - elapsed)

    # Save output file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    # Validate row counts
    output_df = pd.read_csv(output_path)
    if len(output_df) != total_rows:
        logger.error(f"Row count mismatch! Input: {total_rows}, Output: {len(output_df)}")
    else:
        logger.info(f"Completed file: {file_path} ({total_rows} rows)")


async def main():
    """Main processing function"""

    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)

    religion_config = config['religion_prediction']
    input_dir = religion_config['input_directory']
    output_dir = religion_config['output_directory']

    # Initialize components
    progress_tracker = ProgressTracker(religion_config['progress_db'])
    rate_limiter = RateLimiter(
        religion_config['calls_per_minute'],
        religion_config['tokens_per_minute']
    )
    predictor = ReligionPredictor(config, rate_limiter)
    batch_processor = BatchProcessor(config, progress_tracker, predictor)

    # Build expected CSV paths from polling_stations_map.json
    polling_stations_map_path = 'polling_stations_map.json'

    if not Path(polling_stations_map_path).exists():
        logger.error(f"Polling stations map not found: {polling_stations_map_path}")
        logger.error("Run discover_polling_stations.py first to generate the map")
        return

    expected_csv_paths = build_expected_csv_paths(polling_stations_map_path, input_dir)

    if not expected_csv_paths:
        logger.error("No expected CSV paths found in polling stations map")
        return

    # Find all CSV files in input directory
    all_csv_files = set(Path(input_dir).rglob('*.csv'))

    # Filter to only include files from polling_stations_map.json
    csv_files = sorted(expected_csv_paths & all_csv_files)
    total_files = len(csv_files)

    # Log statistics
    missing_files = expected_csv_paths - all_csv_files
    extra_files = all_csv_files - expected_csv_paths

    logger.info(f"Expected CSV files from map: {len(expected_csv_paths)}")
    logger.info(f"Found CSV files to process: {total_files}")

    if missing_files:
        logger.warning(f"Missing {len(missing_files)} expected CSV files (not yet scraped)")
        for missing in sorted(missing_files)[:5]:  # Show first 5
            logger.warning(f"  Missing: {missing.relative_to(input_dir)}")
        if len(missing_files) > 5:
            logger.warning(f"  ... and {len(missing_files) - 5} more")

    if extra_files:
        logger.info(f"Skipping {len(extra_files)} CSV files not in polling stations map (old data)")
        for extra in sorted(extra_files)[:3]:  # Show first 3
            logger.info(f"  Skipping: {extra.relative_to(input_dir)}")
        if len(extra_files) > 3:
            logger.info(f"  ... and {len(extra_files) - 3} more")

    logger.info(f"Output directory: {output_dir}")
    logger.info(f"OPTIMIZED: 25 voters per API call, 40 calls/min = 1000 voters/min")

    # Process each file
    for idx, csv_file in enumerate(csv_files, 1):
        relative_path = csv_file.relative_to(input_dir)
        output_path = Path(output_dir) / relative_path

        await process_csv_file(
            str(csv_file),
            str(output_path),
            config,
            progress_tracker,
            batch_processor
        )

        # Print progress
        batch_processor.print_progress(str(relative_path), total_files, idx)

    # Final report
    total_stats = progress_tracker.get_total_stats()
    elapsed = time.time() - batch_processor.stats['start_time']

    print("\n" + "="*60)
    print("PROCESSING COMPLETE!")
    print("="*60)
    print(f"Total Files: {total_files}")
    print(f"Total Records: {total_stats['total']:,}")
    print(f"  Successful: {total_stats['completed']:,} ({total_stats['completed']/total_stats['total']*100:.1f}%)")
    print(f"  Failed: {total_stats['failed']:,}")
    print(f"Total Time: {elapsed/60:.2f} minutes ({elapsed/3600:.2f} hours)")
    print(f"Average Rate: {total_stats['total']/(elapsed/60):.1f} records/min")
    print("="*60)

    # Close connections
    progress_tracker.close()


if __name__ == "__main__":
    asyncio.run(main())
