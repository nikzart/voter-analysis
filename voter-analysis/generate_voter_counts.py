#!/usr/bin/env python3
"""
Generate voter counts JSON file for the dashboard
"""

import json
import pandas as pd
from pathlib import Path
from analysis.hierarchy_parser import HierarchyParser

def main():
    base_dir = Path(__file__).parent
    csv_dir = base_dir.parent / 'output_with_religion'
    hierarchy_file = base_dir.parent / 'polling_stations_map.json'

    # Parse hierarchy
    parser = HierarchyParser(str(hierarchy_file), str(csv_dir))

    # Count voters per station
    voter_counts = {}

    for ward_key, ward_data in parser.hierarchy.items():
        for station in ward_data['stations']:
            station_num = station['number']
            station_name = station['name']
            station_key = f"{ward_key}/{station_num}"

            # Get CSV file path
            csv_file_path = parser.station_to_file_map.get(station_key)

            if csv_file_path:
                try:
                    df = pd.read_csv(csv_file_path)
                    voter_count = len(df)

                    # Store with station full text as key
                    key = station['full_text']
                    voter_counts[key] = voter_count

                except Exception as e:
                    print(f"Error reading {csv_file_path}: {e}")

    # Save to JSON
    output_file = base_dir / 'reports' / 'voter_counts.json'
    with open(output_file, 'w') as f:
        json.dump(voter_counts, f, indent=2)

    print(f"Voter counts saved to: {output_file}")
    print(f"Total stations: {len(voter_counts)}")
    print(f"Total voters: {sum(voter_counts.values()):,}")

if __name__ == '__main__':
    main()
