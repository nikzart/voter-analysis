#!/usr/bin/env python3
"""
Generate consolidated voter index from CSV files for fuzzy search functionality.
Parses all voter CSV files from output_with_religion folder and creates a single JSON index.
"""

import pandas as pd
import json
import glob
import os
from pathlib import Path

def parse_age_gender(age_gender_str):
    """Parse 'M / 28' format into separate gender and age."""
    try:
        if '/' in str(age_gender_str):
            parts = str(age_gender_str).split('/')
            gender = parts[0].strip()
            age = parts[1].strip()
            return gender, age
        return '', ''
    except:
        return '', ''

def generate_voter_index():
    """Generate consolidated voter index from all CSV files."""

    print("Starting voter index generation...")

    # Path to CSV files
    csv_pattern = '/Users/nikzart/Developer/aislop-server/output_with_religion/**/*.csv'
    csv_files = glob.glob(csv_pattern, recursive=True)

    print(f"Found {len(csv_files)} CSV files to process")

    voters = []
    processed_files = 0
    total_voters = 0

    for csv_file in csv_files:
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            processed_files += 1

            # Process each voter record
            for _, row in df.iterrows():
                # Parse age and gender
                gender, age = parse_age_gender(row.get('Gender / Age', ''))

                # Create voter record
                voter = {
                    'name': str(row.get('Name', '')).strip(),
                    'guardian': str(row.get("Guardian's Name", '')).strip(),
                    'houseName': str(row.get('House Name', '')).strip(),
                    'ward': str(row.get('ward', '')).strip(),
                    'pollingStation': str(row.get('polling_station', '')).strip(),
                    'age': age,
                    'gender': gender,
                    'religion': str(row.get('religion', '')).strip(),
                    'voterId': str(row.get('New SEC ID No.', '')).strip(),
                    'houseNo': str(row.get('OldWard No/ House No.', '')).strip()
                }

                # Only add if name exists
                if voter['name'] and voter['name'] != 'nan':
                    voters.append(voter)
                    total_voters += 1

            # Progress update every 50 files
            if processed_files % 50 == 0:
                print(f"Processed {processed_files}/{len(csv_files)} files, {total_voters} voters indexed...")

        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
            continue

    print(f"\nTotal files processed: {processed_files}")
    print(f"Total voters indexed: {total_voters}")

    # Save to JSON file
    output_path = '/Users/nikzart/Developer/aislop-server/voter-analysis/reports/voter_index.json'
    print(f"\nWriting voter index to {output_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(voters, f, ensure_ascii=False, indent=2)

    # Get file size
    file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
    print(f"Voter index generated successfully!")
    print(f"File size: {file_size:.2f} MB")
    print(f"Total records: {len(voters)}")

    # Generate statistics
    print("\n=== Statistics ===")
    wards = set(v['ward'] for v in voters if v['ward'])
    print(f"Unique wards: {len(wards)}")

    religions = {}
    for v in voters:
        if v['religion']:
            religions[v['religion']] = religions.get(v['religion'], 0) + 1
    print(f"Religion breakdown:")
    for religion, count in sorted(religions.items()):
        print(f"  {religion}: {count}")

    genders = {}
    for v in voters:
        if v['gender']:
            genders[v['gender']] = genders.get(v['gender'], 0) + 1
    print(f"Gender breakdown:")
    for gender, count in sorted(genders.items()):
        print(f"  {gender}: {count}")

if __name__ == '__main__':
    generate_voter_index()
