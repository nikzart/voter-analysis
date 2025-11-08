#!/usr/bin/env python3
"""
Generate voter counts JSON file for the dashboard
Uses polling_stations_map.json to build expected CSV paths
"""

import json
import pandas as pd
from pathlib import Path


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


def main():
    base_dir = Path(__file__).parent
    csv_dir = base_dir.parent / 'output_with_religion'
    polling_stations_map_path = base_dir.parent / 'polling_stations_map.json'

    # Load polling stations map
    if not polling_stations_map_path.exists():
        print(f"Error: Polling stations map not found: {polling_stations_map_path}")
        print("Run discover_polling_stations.py first to generate the map")
        return

    with open(polling_stations_map_path, 'r') as f:
        ps_map = json.load(f)

    # Count voters per station
    voter_counts = {}
    total_expected = 0
    total_found = 0
    total_voters = 0

    for ward in ps_map.get('wards', []):
        ward_text = ward.get('text', '')
        ward_folder = sanitize_ward_name(ward_text)

        for polling_station in ward.get('polling_stations', []):
            ps_text = polling_station.get('text', '')
            ps_filename = sanitize_polling_station_name(ps_text) + '.csv'

            # Build full path
            csv_path = csv_dir / ward_folder / ps_filename
            total_expected += 1

            if csv_path.exists():
                try:
                    df = pd.read_csv(csv_path)
                    voter_count = len(df)

                    # Store with station full text as key (for dashboard)
                    voter_counts[ps_text] = voter_count
                    total_found += 1
                    total_voters += voter_count

                except Exception as e:
                    print(f"Error reading {csv_path}: {e}")
            else:
                print(f"Warning: CSV file not found: {csv_path.relative_to(csv_dir)}")

    # Save to JSON
    output_file = base_dir / 'reports' / 'voter_counts.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(voter_counts, f, indent=2)

    print(f"\nVoter counts saved to: {output_file}")
    print(f"Expected stations: {total_expected}")
    print(f"Found stations: {total_found}")
    print(f"Total voters: {total_voters:,}")

    if total_found < total_expected:
        print(f"\nWarning: {total_expected - total_found} stations missing from output_with_religion/")
        print("Run add_religion_column.py to process remaining stations")


if __name__ == '__main__':
    main()
