#!/usr/bin/env python3
"""
Partial run of clean_voters_csv.py for first 200 records (demonstration)
"""
import pandas as pd
import sys

# Read original script's main function
from clean_voters_csv import *

# Override main to process only first 200 records
def main_partial():
    print("Loading CSV file (first 200 records for demonstration)...")

    # Load the CSV file
    input_file = "Pattathanam Voters List - Rosedale-001.csv"
    df_full = pd.read_csv(input_file, encoding='utf-8')
    df = df_full.head(200)  # Only process first 200

    report_data['total_records'] = len(df)
    print(f"Loaded {report_data['total_records']} records (demo mode)")

    # Split Gender/Age column into separate columns
    print("\nSplitting Gender/Age column...")
    df[['Gender', 'Age']] = df['Gender / Age'].apply(
        lambda x: pd.Series(split_gender_age(x))
    )

    # Reorder columns
    cols = list(df.columns)
    gender_age_idx = cols.index('Gender / Age')
    cols.remove('Gender / Age')
    cols.remove('Gender')
    cols.remove('Age')
    cols.insert(gender_age_idx, 'Age')
    cols.insert(gender_age_idx, 'Gender')
    df = df[cols]

    # Infer religions using Azure AI
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

    # Add a Notes column
    df['Notes'] = ''

    # Save cleaned CSV
    output_file = "Pattathanam Voters List - Rosedale-001_cleaned_DEMO.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\nDemo cleaned CSV saved to: {output_file}")

    print("\n" + "=" * 80)
    print("DEMO CLEANING SUMMARY (First 200 records)")
    print("=" * 80)
    print(f"Records Processed: {report_data['total_records']}")
    print(f"Religions Inferred: {report_data['religion_inferences']}")
    print(f"  Hindu: {report_data['religion_distribution']['Hindu']}")
    print(f"  Christian: {report_data['religion_distribution']['Christian']}")
    print(f"  Muslim: {report_data['religion_distribution']['Muslim']}")
    print(f"Processing Time: {report_data['religion_processing_time']:.2f} seconds")
    print("=" * 80)
    print("\nTo process all 712 records, run: ./venv/bin/python clean_voters_csv.py")
    print("(This will take 3-5 minutes)")

if __name__ == "__main__":
    main_partial()
