"""
Kerala Voter List Scraper
Automates voter list data extraction from sec.kerala.gov.in
"""
import json
import time
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from captcha_solver import CaptchaSolver


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VoterListScraper:
    """Scrapes voter list data from Kerala SEC website"""

    def __init__(self, config_path='config.json', polling_stations_map_path='polling_stations_map.json'):
        """
        Initialize the scraper

        Args:
            config_path: Path to configuration file
            polling_stations_map_path: Path to pre-discovered polling stations map
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.base_url = self.config['base_url']
        self.form_url = self.config['form_url']
        self.output_dir = Path(self.config['output_directory'])
        self.delay = self.config['delay_between_requests']
        self.max_retries = self.config['max_captcha_retries']
        self.language = self.config['language']
        self.district = self.config['district']
        self.local_body = self.config['local_body']

        # Create output directory
        self.output_dir.mkdir(exist_ok=True)

        # Initialize captcha solver
        self.captcha_solver = CaptchaSolver()

        # Load pre-discovered polling stations map
        self.polling_stations_map = self.load_polling_stations_map(polling_stations_map_path)

        # Statistics
        self.stats = {
            'wards_processed': 0,
            'polling_stations_processed': 0,
            'voters_scraped': 0,
            'errors': 0
        }

    def load_polling_stations_map(self, map_path):
        """
        Load pre-discovered polling stations map from JSON file

        Args:
            map_path: Path to polling_stations_map.json

        Returns:
            Dictionary with polling stations organized by ward
        """
        try:
            with open(map_path, 'r') as f:
                data = json.load(f)

            logger.info(f"Loaded polling stations map from {map_path}")
            logger.info(f"Discovery timestamp: {data.get('discovery_timestamp')}")
            logger.info(f"Total wards in map: {data.get('total_wards')}")
            logger.info(f"Total polling stations in map: {data.get('total_polling_stations')}\n")

            # Convert to dictionary keyed by ward value for easy lookup
            map_dict = {}
            for ward in data['wards']:
                map_dict[ward['value']] = {
                    'text': ward['text'],
                    'polling_stations': ward['polling_stations']
                }

            return map_dict

        except FileNotFoundError:
            logger.error(f"Polling stations map not found at {map_path}")
            logger.error("Please run discover_polling_stations.py first!")
            raise
        except Exception as e:
            logger.error(f"Error loading polling stations map: {e}")
            raise

    def solve_captcha_with_retry(self, page):
        """
        Solve captcha with retry logic

        Args:
            page: Playwright page object

        Returns:
            Solved captcha text or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Solving captcha (attempt {attempt + 1}/{self.max_retries})")

                # Get captcha text
                captcha_text = self.captcha_solver.solve_from_page(page)

                if captcha_text and len(captcha_text) >= 4:
                    logger.info(f"Captcha solved: {captcha_text}")
                    return captcha_text
                else:
                    logger.warning(f"Captcha solution too short: {captcha_text}")

                    # Reload captcha
                    reload_btn = page.locator('.gcaptcha-reload')
                    if reload_btn.is_visible():
                        reload_btn.click()
                        time.sleep(1)

            except Exception as e:
                logger.error(f"Error solving captcha: {e}")

                # Try to reload captcha
                try:
                    reload_btn = page.locator('.gcaptcha-reload')
                    if reload_btn.is_visible():
                        reload_btn.click()
                        time.sleep(1)
                except:
                    pass

        logger.error("Failed to solve captcha after all retries")
        return None

    def extract_voter_data(self, page):
        """
        Extract voter data from the results page

        Args:
            page: Playwright page object

        Returns:
            List of voter records
        """
        try:
            # Wait for results to load (increased timeout for slow pages)
            # But check every second for invalid captcha or results
            max_wait_time = 60  # seconds
            check_interval = 1  # seconds (optimized for faster detection)
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                time.sleep(check_interval)
                elapsed_time += check_interval

                result_div = page.locator('.voters_list_search_result')

                # Check if div is visible
                if result_div.is_visible():
                    result_html = result_div.inner_html()

                    # Check for invalid captcha message
                    if 'invalid' in result_html.lower() and 'captcha' in result_html.lower():
                        logger.warning("Invalid captcha detected - captcha rejected by server")
                        return []

                    # Check if we have actual data
                    if len(result_html) > 1000:  # Substantial content
                        logger.info(f"Results loaded after {elapsed_time} seconds")
                        break

            # Get final result HTML
            result_div = page.locator('.voters_list_search_result')
            result_html = result_div.inner_html()

            # Check if there's an error message or no data
            if 'No data' in result_html or 'not found' in result_html.lower():
                logger.warning("No voter data found in results")
                return []

            # Check again for invalid captcha
            if 'invalid' in result_html.lower() and 'captcha' in result_html.lower():
                logger.warning("Invalid captcha - captcha rejected by server")
                return []

            # Extract voter table data with proper column headers using optimized JavaScript
            voters = page.evaluate("""() => {
                const voters = [];
                const tables = document.querySelectorAll('.voters_list_search_result table');

                tables.forEach(table => {
                    // Extract headers
                    const headerElements = table.querySelectorAll('th');
                    const headers = [];
                    headerElements.forEach(th => {
                        const text = th.innerText.trim();
                        if (text) headers.push(text);
                    });

                    // Use default headers if none found
                    const finalHeaders = headers.length > 0 ? headers : Array.from({length: 10}, (_, i) => `column_${i}`);

                    // Extract data rows
                    const rows = table.querySelectorAll('tr');

                    for (let i = 1; i < rows.length; i++) {  // Skip header row
                        const cells = rows[i].querySelectorAll('td');

                        if (cells.length >= 3) {
                            const cellTexts = Array.from(cells).map(cell => cell.innerText.trim());

                            // Skip header rows with "WARD:" or "POLLING STATION:"
                            const hasHeaderText = cellTexts.some(text =>
                                text.includes('WARD:') || text.includes('POLLING STATION:')
                            );
                            if (hasHeaderText) continue;

                            // Create voter record
                            const voterData = {};
                            cellTexts.forEach((text, idx) => {
                                const key = idx < finalHeaders.length ? finalHeaders[idx] : `column_${idx}`;
                                voterData[key] = text;
                            });

                            voters.push(voterData);
                        }
                    }
                });

                return voters;
            }""")

            logger.info(f"Extracted {len(voters)} voter records")
            return voters

        except Exception as e:
            logger.error(f"Error extracting voter data: {e}")
            return []

    def scrape_polling_station(self, page, ward, polling_station):
        """
        Scrape voter list for a specific polling station

        Args:
            page: Playwright page object
            ward: Ward dictionary with 'value' and 'text'
            polling_station: Polling station dictionary with 'value' and 'text'

        Returns:
            List of voter records
        """
        try:
            logger.info(f"Scraping polling station: {polling_station['text']}")

            # Navigate to form page
            page.goto(self.form_url)
            page.wait_for_load_state('networkidle')
            time.sleep(1)

            # Select district (force=True for hidden selects)
            page.locator('#view_voters_list_district').select_option(value=self.district, force=True)
            time.sleep(1)  # Wait for AJAX to populate local bodies

            # Select local body (force=True for hidden selects)
            page.locator('#view_voters_list_localBody').select_option(value=self.local_body, force=True)
            time.sleep(1)  # Wait for AJAX to populate wards

            # Select ward (force=True for hidden selects)
            page.locator('#view_voters_list_ward').select_option(value=ward['value'], force=True)
            time.sleep(1)  # Wait for AJAX to populate polling stations

            # Select polling station (force=True for hidden selects)
            page.locator('#view_voters_list_pollingStation').select_option(value=polling_station['value'], force=True)
            time.sleep(0.5)

            # Select language (force=True for hidden selects)
            page.locator('#view_voters_list_language').select_option(value=self.language, force=True)
            time.sleep(0.5)

            # Solve captcha
            captcha_text = self.solve_captcha_with_retry(page)
            if not captcha_text:
                logger.error("Failed to solve captcha, skipping this polling station")
                self.stats['errors'] += 1
                return []

            # Fill captcha
            page.fill('#view_voters_list_captcha', captcha_text)
            time.sleep(0.5)

            # Submit form
            page.click('button.btn-pgfsv3')
            # Wait for AJAX to complete (results checking loop handles the rest)
            time.sleep(2)

            # Extract voter data
            voters = self.extract_voter_data(page)

            # Add metadata to each voter record
            for voter in voters:
                voter['ward'] = ward['text']
                voter['polling_station'] = polling_station['text']
                voter['scrape_timestamp'] = datetime.now().isoformat()

            # Save to CSV immediately for this polling station
            if voters:
                self.save_to_csv(voters, ward['text'], polling_station['text'])

            self.stats['polling_stations_processed'] += 1
            self.stats['voters_scraped'] += len(voters)

            return voters

        except Exception as e:
            logger.error(f"Error scraping polling station {polling_station['text']}: {e}")
            self.stats['errors'] += 1
            return []

    def scrape_ward(self, page, ward):
        """
        Scrape all polling stations in a ward with retry logic

        Args:
            page: Playwright page object
            ward: Ward dictionary with 'value' and 'text'
        """
        logger.info(f"Starting to scrape ward: {ward['text']}")

        try:
            # Get polling stations from pre-loaded map
            ward_data = self.polling_stations_map.get(ward['value'])
            if not ward_data:
                logger.error(f"Ward {ward['text']} not found in polling stations map!")
                return

            polling_stations = ward_data['polling_stations']

            if not polling_stations:
                logger.warning(f"No polling stations found for ward {ward['text']}")
                return

            logger.info(f"Found {len(polling_stations)} polling stations in map for {ward['text']}")

            # Track successes and failures
            failed_polling_stations = []
            successful_count = 0

            # First pass: try all polling stations
            for ps in polling_stations:
                voters = self.scrape_polling_station(page, ward, ps)

                if voters and len(voters) > 0:
                    successful_count += 1
                else:
                    failed_polling_stations.append(ps)
                    logger.warning(f"Failed to scrape: {ps['text']}")

                # Delay between requests
                time.sleep(self.delay)

            # Retry failed polling stations (increased retries to ensure all data is captured)
            max_retries = 6
            for retry_attempt in range(max_retries):
                if not failed_polling_stations:
                    break

                logger.info(f"Retrying {len(failed_polling_stations)} failed polling stations (attempt {retry_attempt + 1}/{max_retries})")
                still_failing = []

                for ps in failed_polling_stations:
                    logger.info(f"Retry: {ps['text']}")
                    voters = self.scrape_polling_station(page, ward, ps)

                    if voters and len(voters) > 0:
                        successful_count += 1
                        logger.info(f"Retry successful: {ps['text']}")
                    else:
                        still_failing.append(ps)

                    time.sleep(self.delay)

                failed_polling_stations = still_failing

            # Log summary for this ward
            total_ps = len(polling_stations)
            logger.info(f"\nWard {ward['text']} Summary:")
            logger.info(f"  Total polling stations: {total_ps}")
            logger.info(f"  Successfully scraped: {successful_count}")
            logger.info(f"  Failed: {len(failed_polling_stations)}")
            if failed_polling_stations:
                logger.warning(f"  Failed polling stations:")
                for ps in failed_polling_stations:
                    logger.warning(f"    - {ps['text']}")

            self.stats['wards_processed'] += 1

        except Exception as e:
            logger.error(f"Error scraping ward {ward['text']}: {e}")
            self.stats['errors'] += 1

    def save_to_csv(self, data, ward_name, polling_station_name):
        """
        Save voter data to CSV file for a specific polling station

        Args:
            data: List of voter dictionaries
            ward_name: Name of the ward (for directory)
            polling_station_name: Name of polling station (for filename)
        """
        if not data:
            logger.warning(f"No data to save for {polling_station_name}")
            return

        # Clean names for directory and filename
        clean_ward_name = ward_name.replace('/', '_').replace(' ', '_')
        clean_ps_name = polling_station_name.replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')

        # Create ward subdirectory
        ward_dir = self.output_dir / clean_ward_name
        ward_dir.mkdir(exist_ok=True)

        # Create filename without timestamp (polling station number makes it unique)
        filename = f"{clean_ps_name}.csv"
        filepath = ward_dir / filename

        # Convert to DataFrame and save
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8')

        logger.info(f"Saved {len(data)} records to {filepath}")

    def run(self):
        """
        Main scraping process
        """
        logger.info("Starting Kerala Voter List Scraper")
        logger.info(f"Total wards to process: {len(self.config['wards'])}")

        # Calculate total polling stations from map
        total_ps_in_map = sum(len(ward_data['polling_stations'])
                              for ward_data in self.polling_stations_map.values())
        logger.info(f"Total polling stations to scrape: {total_ps_in_map}\n")

        start_time = time.time()

        with sync_playwright() as p:
            # Launch browser (headless=False needed for proper page loading)
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            try:
                # Process each ward
                for ward in self.config['wards']:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"Processing ward {self.stats['wards_processed']+1}/{len(self.config['wards'])}")
                    logger.info(f"Ward: {ward['text']}")
                    logger.info(f"{'='*60}\n")

                    # Scrape the ward (saves individual polling stations)
                    self.scrape_ward(page, ward)

                    # Progress update
                    logger.info(f"\nProgress: {self.stats['wards_processed']}/{len(self.config['wards'])} wards")
                    logger.info(f"Total voters scraped so far: {self.stats['voters_scraped']}")

            except KeyboardInterrupt:
                logger.warning("Scraping interrupted by user")

            finally:
                browser.close()

        # Final statistics
        elapsed_time = time.time() - start_time
        logger.info(f"\n{'='*60}")
        logger.info("Scraping completed!")
        logger.info(f"{'='*60}")
        logger.info(f"Wards processed: {self.stats['wards_processed']}/{len(self.config['wards'])}")
        logger.info(f"Polling stations processed: {self.stats['polling_stations_processed']}")
        logger.info(f"Total voters scraped: {self.stats['voters_scraped']}")
        logger.info(f"Errors encountered: {self.stats['errors']}")
        logger.info(f"Total time: {elapsed_time:.2f} seconds")
        logger.info(f"Output directory: {self.output_dir.absolute()}")
        logger.info(f"{'='*60}\n")