import pandas as pd
import re
from openai import AzureOpenAI, AsyncAzureOpenAI
import os
from dotenv import load_dotenv
import asyncio
import json
import time

# Load environment variables from .env.local file
load_dotenv('.env.local')

# Azure OpenAI Configuration
endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT', 'https://coven.cognitiveservices.azure.com/')
model_name = os.environ.get('AZURE_OPENAI_MODEL', 'gpt-5-mini')
deployment = os.environ.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-5-mini')
subscription_key = os.environ.get('AZURE_OPENAI_KEY', '')
api_version = os.environ.get('AZURE_OPENAI_API_VERSION', '2024-12-01-preview')

if not subscription_key:
    print("Warning: AZURE_OPENAI_KEY not found in .env.local file.")
    print("Malayalam transliteration will not work without Azure credentials.")
    print("Copy .env.local.example to .env.local and add your credentials.")

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
) if subscription_key else None

async_client = AsyncAzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
) if subscription_key else None

# Tracking for report
report_data = {
    'total_records': 0,
    'missing_sec_ids': [],
    'duplicates': [],
    'malayalam_transliterations': [],
    'ward_format_changes': [],
    'spacing_fixes': 0,
    'gender_age_splits': 0,
    'gender_age_errors': [],
    'religion_inferences': 0,
    'religion_distribution': {'Hindu': 0, 'Christian': 0, 'Muslim': 0},
    'religion_api_calls': 0,
    'religion_processing_time': 0
}

def transliterate_malayalam(text):
    """Use Azure OpenAI to transliterate Malayalam text to Latin script"""
    if not client:
        print(f"  Skipping transliteration (no Azure credentials): {text}")
        return text

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a Malayalam transliteration expert. Transliterate Malayalam text to Latin script accurately."},
                {"role": "user", "content": f"Transliterate this Malayalam text to Latin script: {text}. Provide ONLY the transliteration, no explanation."}
            ],
            max_completion_tokens=100
        )
        transliteration = response.choices[0].message.content.strip()
        return transliteration
    except Exception as e:
        print(f"Error transliterating Malayalam: {e}")
        return text

def standardize_ward_number(ward_str):
    """Standardize ward/house number format to 3-digit/number"""
    if pd.isna(ward_str) or ward_str == '':
        return ward_str

    ward_str = str(ward_str).strip()
    match = re.match(r'^(\d+)/(\d+)$', ward_str)

    if match:
        ward_num = match.group(1)
        house_num = match.group(2)

        # Zero-pad ward number to 3 digits
        if len(ward_num) < 3:
            standardized = f"{ward_num.zfill(3)}/{house_num}"
            if standardized != ward_str:
                report_data['ward_format_changes'].append({
                    'original': ward_str,
                    'standardized': standardized
                })
            return standardized

    return ward_str

def clean_spacing(text):
    """Remove extra spaces and normalize whitespace"""
    if pd.isna(text) or text == '':
        return text

    original = str(text)
    # Replace multiple spaces with single space
    cleaned = re.sub(r'\s+', ' ', original.strip())

    if cleaned != original:
        report_data['spacing_fixes'] += 1

    return cleaned

def detect_malayalam(text):
    """Check if text contains Malayalam characters"""
    if pd.isna(text):
        return False
    malayalam_range = r'[\u0D00-\u0D7F]'
    return bool(re.search(malayalam_range, str(text)))

def split_gender_age(gender_age_str):
    """Split 'Gender / Age' column into separate Gender and Age values"""
    if pd.isna(gender_age_str) or gender_age_str == '':
        return None, None

    # Pattern: {Gender} / {Age}
    # Example: "M / 60" or "F / 56"
    match = re.match(r'([MF])\s*/\s*(\d+)', str(gender_age_str).strip())

    if match:
        gender = match.group(1)  # 'M' or 'F'
        age = int(match.group(2))  # Convert to integer
        report_data['gender_age_splits'] += 1
        return gender, age
    else:
        # If pattern doesn't match, record error
        report_data['gender_age_errors'].append({
            'value': gender_age_str,
            'error': 'Could not parse gender/age format'
        })
        return None, None

async def infer_religion_batch(batch_records, retry_count=0, max_retries=2):
    """Infer religion for a batch of records using Azure OpenAI with JSON output"""
    if not async_client:
        print("  Skipping religion inference (no Azure credentials)")
        return {record['serial_no']: 'Unknown' for record in batch_records}

    try:
        # Prepare batch data for the prompt
        batch_text = "\n".join([
            f"{record['serial_no']}. Name: {record['name']}, Guardian: {record['guardian']}"
            for record in batch_records
        ])

        response = await async_client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are an expert in Kerala, India naming conventions. You must respond ONLY with valid JSON. Classify each person's religion (Hindu, Christian, or Muslim) based on their name and guardian's name. Kerala has significant populations of all three religions.\n\nChristian indicators: Biblical names (John, Mary, Thomas, Joseph, Francis, etc.), surnames ending in '-son'.\nMuslim indicators: Arabic names (Muhammad, Abdul, Fathima, Ayisha, Jaleel, etc.), 'Beevi', 'Khan'.\nHindu indicators: Sanskrit names (Krishna, Rama, Lakshmi, Devi, etc.), names ending in '-an', '-kumar', 'Nair', 'Pillai'."},
                {"role": "user", "content": f"Classify the religion for each person. Respond with ONLY a JSON object in this exact format:\n{{\"religions\": [{{\"serial_no\": 1, \"religion\": \"Hindu\"}}, {{\"serial_no\": 2, \"religion\": \"Christian\"}}]}}\n\nPeople to classify:\n{batch_text}"}
            ],
            max_completion_tokens=2000
        )

        # Parse JSON response
        content = response.choices[0].message.content

        if not content or content.strip() == '':
            if retry_count < max_retries:
                print(f"  Retrying batch starting at {batch_records[0]['serial_no']} (attempt {retry_count + 2}/{max_retries + 1})")
                await asyncio.sleep(1)  # Small delay before retry
                return await infer_religion_batch(batch_records, retry_count + 1, max_retries)
            else:
                print(f"  Warning: Empty response from API for batch starting at {batch_records[0]['serial_no']} after {max_retries + 1} attempts")
                return {record['serial_no']: 'Unknown' for record in batch_records}

        content = content.strip()

        # Try to extract JSON if wrapped in markdown code blocks
        if content.startswith('```'):
            # Remove markdown code blocks
            content = content.replace('```json', '').replace('```', '').strip()

        result = json.loads(content)
        report_data['religion_api_calls'] += 1

        # Convert to dictionary
        religion_dict = {
            int(item['serial_no']): item['religion']
            for item in result['religions']
        }

        return religion_dict

    except json.JSONDecodeError as e:
        print(f"  JSON parse error for batch starting at {batch_records[0]['serial_no']}: {e}")
        print(f"  Response content: {content[:200] if 'content' in locals() else 'No content'}")
        return {record['serial_no']: 'Unknown' for record in batch_records}
    except Exception as e:
        print(f"  Error inferring religion for batch starting at {batch_records[0]['serial_no']}: {e}")
        return {record['serial_no']: 'Unknown' for record in batch_records}

async def process_religions_parallel(df, batch_size=50, max_parallel=4):
    """Process religion inference in parallel batches"""
    print("\nInferring religions using Azure AI...")
    print(f"Processing {len(df)} records in batches of {batch_size} with {max_parallel} parallel calls...")

    start_time = time.time()

    # Prepare all batches
    all_batches = []
    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i:i+batch_size]
        batch_records = [
            {
                'serial_no': int(row['Serial No.']),
                'name': row['Name'],
                'guardian': row["Guardian's Name"]
            }
            for _, row in batch_df.iterrows()
        ]
        all_batches.append(batch_records)

    total_batches = len(all_batches)
    print(f"Total batches: {total_batches}")

    # Process batches in groups of max_parallel
    all_results = {}
    for batch_group_idx in range(0, total_batches, max_parallel):
        batch_group = all_batches[batch_group_idx:batch_group_idx + max_parallel]

        # Run this group of batches in parallel
        tasks = [infer_religion_batch(batch) for batch in batch_group]
        group_results = await asyncio.gather(*tasks)

        # Merge results
        for result_dict in group_results:
            all_results.update(result_dict)

        # Progress update
        completed = min(batch_group_idx + max_parallel, total_batches)
        progress = (completed / total_batches) * 100
        print(f"  Progress: {completed}/{total_batches} batches ({progress:.1f}%)")

        # Small delay between batch groups to avoid rate limiting
        if completed < total_batches:
            await asyncio.sleep(0.5)

    end_time = time.time()
    report_data['religion_processing_time'] = end_time - start_time

    print(f"Religion inference completed in {report_data['religion_processing_time']:.2f} seconds")

    return all_results

def main():
    print("Loading CSV file...")

    # Load the CSV file
    input_file = "Pattathanam Voters List - Rosedale-001.csv"
    df = pd.read_csv(input_file, encoding='utf-8')

    report_data['total_records'] = len(df)
    print(f"Loaded {report_data['total_records']} records")

    # Split Gender/Age column into separate columns
    print("\nSplitting Gender/Age column...")
    df[['Gender', 'Age']] = df['Gender / Age'].apply(
        lambda x: pd.Series(split_gender_age(x))
    )

    # Reorder columns: keep Gender and Age where Gender/Age was
    cols = list(df.columns)
    gender_age_idx = cols.index('Gender / Age')
    # Remove Gender/Age, Gender, and Age from their current positions
    cols.remove('Gender / Age')
    cols.remove('Gender')
    cols.remove('Age')
    # Insert Gender and Age at the original Gender/Age position
    cols.insert(gender_age_idx, 'Age')
    cols.insert(gender_age_idx, 'Gender')
    df = df[cols]

    # Infer religions using Azure AI (async batch processing)
    # Using smaller batches and sequential processing for better reliability with gpt-5-mini
    religion_results = asyncio.run(process_religions_parallel(df, batch_size=20, max_parallel=1))

    # Add Religion column
    df['Religion'] = df['Serial No.'].map(religion_results)

    # Update religion statistics
    for religion in df['Religion']:
        if religion in report_data['religion_distribution']:
            report_data['religion_distribution'][religion] += 1
        report_data['religion_inferences'] += 1

    # Reorder columns to place Religion after Age
    cols = list(df.columns)
    cols.remove('Religion')
    age_idx = cols.index('Age')
    cols.insert(age_idx + 1, 'Religion')
    df = df[cols]

    # Add a Notes column for flagging issues
    df['Notes'] = ''

    # Process each row
    print("\nProcessing records...")

    for idx, row in df.iterrows():
        notes = []

        # Check for missing SEC ID
        if pd.isna(row['New SEC ID No.']) or row['New SEC ID No.'] == '':
            notes.append('REVIEW_NEEDED: Missing SEC ID')
            report_data['missing_sec_ids'].append({
                'line': idx + 2,  # +2 for header and 0-indexing
                'name': row['Name'],
                'guardian': row["Guardian's Name"]
            })

        # Clean spacing in all text columns
        for col in ['Name', "Guardian's Name", 'House Name']:
            if col in df.columns:
                df.at[idx, col] = clean_spacing(row[col])

        # Standardize ward number
        df.at[idx, 'OldWard No/ House No.'] = standardize_ward_number(row['OldWard No/ House No.'])

        # Check for Malayalam text in House Name and transliterate
        if detect_malayalam(row['House Name']):
            original_text = row['House Name']
            print(f"  Found Malayalam text at line {idx + 2}: {original_text}")
            transliterated = transliterate_malayalam(original_text)
            df.at[idx, 'House Name'] = transliterated
            notes.append(f'TRANSLITERATED: {original_text} -> {transliterated}')
            report_data['malayalam_transliterations'].append({
                'line': idx + 2,
                'original': original_text,
                'transliterated': transliterated
            })
            print(f"  Transliterated to: {transliterated}")

        # Add notes to the row
        if notes:
            df.at[idx, 'Notes'] = '; '.join(notes)

    # Check for duplicates (comparing Name, Guardian's Name, Gender and Age)
    print("\nChecking for duplicates...")
    df['Name_Guardian_Gender_Age'] = (df['Name'].astype(str) + '_' +
                                       df["Guardian's Name"].astype(str) + '_' +
                                       df['Gender'].astype(str) + '_' +
                                       df['Age'].astype(str))
    duplicates = df[df.duplicated(subset=['Name_Guardian_Gender_Age'], keep=False)]

    for idx in duplicates.index:
        current_note = df.at[idx, 'Notes']
        duplicate_note = 'DUPLICATE_CHECK: Possible duplicate entry'
        df.at[idx, 'Notes'] = f"{current_note}; {duplicate_note}" if current_note else duplicate_note

        report_data['duplicates'].append({
            'line': idx + 2,
            'name': df.at[idx, 'Name'],
            'guardian': df.at[idx, "Guardian's Name"],
            'gender': df.at[idx, 'Gender'],
            'age': df.at[idx, 'Age'],
            'sec_id': df.at[idx, 'New SEC ID No.']
        })

    # Remove temporary column
    df.drop('Name_Guardian_Gender_Age', axis=1, inplace=True)

    # Save cleaned CSV
    output_file = "Pattathanam Voters List - Rosedale-001_cleaned.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\nCleaned CSV saved to: {output_file}")

    # Generate report
    generate_report()

def generate_report():
    """Generate a detailed cleaning report"""
    report_file = "cleaning_report.txt"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("VOTER LIST CSV CLEANING REPORT\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Total Records Processed: {report_data['total_records']}\n\n")

        # Missing SEC IDs
        f.write("-" * 80 + "\n")
        f.write(f"MISSING SEC IDs ({len(report_data['missing_sec_ids'])} records)\n")
        f.write("-" * 80 + "\n")
        if report_data['missing_sec_ids']:
            for item in report_data['missing_sec_ids']:
                f.write(f"  Line {item['line']}: {item['name']} (Guardian: {item['guardian']})\n")
        else:
            f.write("  None found\n")
        f.write("\n")

        # Duplicates
        f.write("-" * 80 + "\n")
        f.write(f"DUPLICATE ENTRIES ({len(report_data['duplicates'])} records)\n")
        f.write("-" * 80 + "\n")
        if report_data['duplicates']:
            for item in report_data['duplicates']:
                f.write(f"  Line {item['line']}: {item['name']} (Guardian: {item['guardian']}, "
                       f"Gender: {item['gender']}, Age: {item['age']}, SEC ID: {item['sec_id']})\n")
        else:
            f.write("  None found\n")
        f.write("\n")

        # Malayalam Transliterations
        f.write("-" * 80 + "\n")
        f.write(f"MALAYALAM TRANSLITERATIONS ({len(report_data['malayalam_transliterations'])} records)\n")
        f.write("-" * 80 + "\n")
        if report_data['malayalam_transliterations']:
            for item in report_data['malayalam_transliterations']:
                f.write(f"  Line {item['line']}:\n")
                f.write(f"    Original: {item['original']}\n")
                f.write(f"    Transliterated: {item['transliterated']}\n\n")
        else:
            f.write("  None found\n")
        f.write("\n")

        # Ward Format Changes
        f.write("-" * 80 + "\n")
        f.write(f"WARD NUMBER FORMAT STANDARDIZATIONS ({len(report_data['ward_format_changes'])} changes)\n")
        f.write("-" * 80 + "\n")
        if report_data['ward_format_changes']:
            # Show first 10 examples
            for item in report_data['ward_format_changes'][:10]:
                f.write(f"  {item['original']} -> {item['standardized']}\n")
            if len(report_data['ward_format_changes']) > 10:
                f.write(f"  ... and {len(report_data['ward_format_changes']) - 10} more\n")
        else:
            f.write("  None found\n")
        f.write("\n")

        # Spacing Fixes
        f.write("-" * 80 + "\n")
        f.write(f"SPACING FIXES: {report_data['spacing_fixes']} fields cleaned\n")
        f.write("-" * 80 + "\n\n")

        # Gender/Age Column Split
        f.write("-" * 80 + "\n")
        f.write(f"GENDER/AGE COLUMN SPLIT\n")
        f.write("-" * 80 + "\n")
        f.write(f"Successfully split: {report_data['gender_age_splits']} records\n")
        if report_data['gender_age_errors']:
            f.write(f"Errors encountered: {len(report_data['gender_age_errors'])}\n")
            for item in report_data['gender_age_errors']:
                f.write(f"  Value: '{item['value']}' - {item['error']}\n")
        else:
            f.write("No errors encountered\n")
        f.write("\n")

        # Religion Inference
        f.write("-" * 80 + "\n")
        f.write(f"RELIGION INFERENCE (AI-based)\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total records classified: {report_data['religion_inferences']}\n")
        f.write(f"API calls made: {report_data['religion_api_calls']}\n")
        f.write(f"Processing time: {report_data['religion_processing_time']:.2f} seconds\n\n")
        f.write("Distribution:\n")
        for religion, count in sorted(report_data['religion_distribution'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / report_data['religion_inferences'] * 100) if report_data['religion_inferences'] > 0 else 0
            f.write(f"  {religion}: {count} ({percentage:.1f}%)\n")
        f.write("\n")

        f.write("=" * 80 + "\n")
        f.write("SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Records requiring manual review: {len(report_data['missing_sec_ids']) + len(report_data['duplicates'])}\n")
        f.write(f"Malayalam text transliterated: {len(report_data['malayalam_transliterations'])}\n")
        f.write(f"Format standardizations: {len(report_data['ward_format_changes'])}\n")
        f.write(f"Spacing fixes: {report_data['spacing_fixes']}\n")
        f.write(f"Gender/Age records split: {report_data['gender_age_splits']}\n")
        f.write(f"Religions inferred: {report_data['religion_inferences']}\n")
        f.write("\nOriginal file preserved. Cleaned data saved with '_cleaned' suffix.\n")
        f.write("=" * 80 + "\n")

    print(f"Report saved to: {report_file}")

    # Print summary to console
    print("\n" + "=" * 80)
    print("CLEANING SUMMARY")
    print("=" * 80)
    print(f"Total Records: {report_data['total_records']}")
    print(f"Gender/Age Split: {report_data['gender_age_splits']}")
    print(f"Religions Inferred: {report_data['religion_inferences']} (Hindu: {report_data['religion_distribution']['Hindu']}, Christian: {report_data['religion_distribution']['Christian']}, Muslim: {report_data['religion_distribution']['Muslim']})")
    print(f"Missing SEC IDs: {len(report_data['missing_sec_ids'])}")
    print(f"Duplicates Found: {len(report_data['duplicates'])}")
    print(f"Malayalam Transliterations: {len(report_data['malayalam_transliterations'])}")
    print(f"Ward Format Changes: {len(report_data['ward_format_changes'])}")
    print(f"Spacing Fixes: {report_data['spacing_fixes']}")
    print("=" * 80)

if __name__ == "__main__":
    main()
