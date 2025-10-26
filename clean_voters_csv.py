import pandas as pd
import re
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

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

# Tracking for report
report_data = {
    'total_records': 0,
    'missing_sec_ids': [],
    'duplicates': [],
    'malayalam_transliterations': [],
    'ward_format_changes': [],
    'spacing_fixes': 0,
    'gender_age_splits': 0,
    'gender_age_errors': []
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

        f.write("=" * 80 + "\n")
        f.write("SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Records requiring manual review: {len(report_data['missing_sec_ids']) + len(report_data['duplicates'])}\n")
        f.write(f"Malayalam text transliterated: {len(report_data['malayalam_transliterations'])}\n")
        f.write(f"Format standardizations: {len(report_data['ward_format_changes'])}\n")
        f.write(f"Spacing fixes: {report_data['spacing_fixes']}\n")
        f.write(f"Gender/Age records split: {report_data['gender_age_splits']}\n")
        f.write("\nOriginal file preserved. Cleaned data saved with '_cleaned' suffix.\n")
        f.write("=" * 80 + "\n")

    print(f"Report saved to: {report_file}")

    # Print summary to console
    print("\n" + "=" * 80)
    print("CLEANING SUMMARY")
    print("=" * 80)
    print(f"Total Records: {report_data['total_records']}")
    print(f"Gender/Age Split: {report_data['gender_age_splits']}")
    print(f"Missing SEC IDs: {len(report_data['missing_sec_ids'])}")
    print(f"Duplicates Found: {len(report_data['duplicates'])}")
    print(f"Malayalam Transliterations: {len(report_data['malayalam_transliterations'])}")
    print(f"Ward Format Changes: {len(report_data['ward_format_changes'])}")
    print(f"Spacing Fixes: {report_data['spacing_fixes']}")
    print("=" * 80)

if __name__ == "__main__":
    main()
