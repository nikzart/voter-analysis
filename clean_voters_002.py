#!/usr/bin/env python3
"""
Process Bharanikkav School South-002 voter list
"""
import pandas as pd
import sys

# Import all functions from the main cleaning script
from clean_voters_csv import *

def main():
    print("Loading CSV file...")

    # Load the CSV file
    input_file = "Pattathanam Voters List - Bharanikkav School South- 002.csv"
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
    output_file = "Pattathanam Voters List - Bharanikkav School South- 002_cleaned.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\nCleaned CSV saved to: {output_file}")

    # Generate report
    generate_report_002()

def generate_report_002():
    """Generate a detailed cleaning report"""
    report_file = "cleaning_report_002.txt"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("VOTER LIST CSV CLEANING REPORT\n")
        f.write("File: Bharanikkav School South- 002\n")
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
