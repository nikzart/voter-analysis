"""
Kerala Voter Data Hierarchy Parser
Parses ward-polling station hierarchy and maps to CSV files
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

class HierarchyParser:
    """Parse and manage ward-polling station hierarchy"""

    def __init__(self, hierarchy_file: str, data_dir: str):
        self.hierarchy_file = hierarchy_file
        self.data_dir = data_dir
        self.hierarchy = {}
        self.station_to_file_map = {}
        self.load_hierarchy()
        self.map_csv_files()

    def load_hierarchy(self):
        """Load ward-polling station hierarchy from JSON"""
        with open(self.hierarchy_file, 'r') as f:
            data = json.load(f)

        # Parse hierarchy structure
        for ward in data['wards']:
            ward_code = ward['text'].split(' - ')[0]
            ward_name = ward['text'].split(' - ')[1]
            ward_key = f"{ward_code}_{ward_name}"

            self.hierarchy[ward_key] = {
                'code': ward_code,
                'name': ward_name,
                'full_text': ward['text'],
                'stations': []
            }

            for station in ward['polling_stations']:
                station_text = station['text']
                # Extract station number and name
                parts = station_text.split(' - ', 1)
                station_num = parts[0]
                station_name = parts[1] if len(parts) > 1 else station_text

                self.hierarchy[ward_key]['stations'].append({
                    'number': station_num,
                    'name': station_name,
                    'full_text': station_text
                })

    def map_csv_files(self):
        """Map CSV files to polling stations based on naming patterns"""
        csv_files = list(Path(self.data_dir).rglob('*.csv'))

        for csv_file in csv_files:
            # Extract ward and polling station from file path
            # Format: output_with_religion/041_-_BHARANIKKAVU/003_-_Bhaskaranunni_Library_Building_Vanjikovil.csv
            parts = csv_file.parts

            if len(parts) >= 2:
                ward_folder = parts[-2]  # e.g., "041_-_BHARANIKKAVU"
                station_file = parts[-1]  # e.g., "003_-_Bhaskaranunni_Library_Building_Vanjikovil.csv"

                # Parse ward info
                ward_parts = ward_folder.split('_-_')
                if len(ward_parts) == 2:
                    ward_code = ward_parts[0]
                    ward_name_raw = ward_parts[1]
                    # Replace underscores with spaces to match hierarchy format
                    ward_name = ward_name_raw.replace('_', ' ')
                    ward_key = f"{ward_code}_{ward_name}"

                    # Parse station info
                    station_num = station_file.split('_-_')[0] if '_-_' in station_file else None

                    if ward_key in self.hierarchy and station_num:
                        # Find matching station
                        for station in self.hierarchy[ward_key]['stations']:
                            if station['number'] == station_num:
                                station_key = f"{ward_key}/{station_num}"
                                self.station_to_file_map[station_key] = str(csv_file)
                                break

    def get_hierarchy_stats(self) -> Dict:
        """Get statistics about the hierarchy"""
        total_wards = len(self.hierarchy)
        total_stations = sum(len(ward['stations']) for ward in self.hierarchy.values())
        mapped_files = len(self.station_to_file_map)

        return {
            'total_wards': total_wards,
            'total_stations': total_stations,
            'mapped_files': mapped_files,
            'wards': list(self.hierarchy.keys())
        }

    def get_ward_stations(self, ward_key: str) -> List[Dict]:
        """Get all polling stations for a ward"""
        if ward_key in self.hierarchy:
            return self.hierarchy[ward_key]['stations']
        return []

    def get_station_file(self, ward_key: str, station_num: str) -> str:
        """Get CSV file path for a specific polling station"""
        station_key = f"{ward_key}/{station_num}"
        return self.station_to_file_map.get(station_key)

    def save_mapping(self, output_file: str):
        """Save the hierarchy and file mapping to JSON"""
        output = {
            'hierarchy': self.hierarchy,
            'station_file_map': self.station_to_file_map,
            'stats': self.get_hierarchy_stats()
        }

        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)

        return output


def test_parser():
    """Test the hierarchy parser"""
    parser = HierarchyParser(
        hierarchy_file='/Users/nikzart/Developer/aislop-server/polling_stations_map.json',
        data_dir='/Users/nikzart/Developer/aislop-server/output_with_religion'
    )

    stats = parser.get_hierarchy_stats()
    print(f"Parsed Hierarchy:")
    print(f"  Total Wards: {stats['total_wards']}")
    print(f"  Total Stations: {stats['total_stations']}")
    print(f"  Mapped CSV Files: {stats['mapped_files']}")

    # Save mapping
    parser.save_mapping('/Users/nikzart/Developer/aislop-server/voter-analysis/data/processed/metadata/hierarchy_mapping.json')

    # Test getting specific station
    sample_ward = '041_BHARANIKKAVU'
    if sample_ward in parser.hierarchy:
        stations = parser.get_ward_stations(sample_ward)
        print(f"\n{sample_ward} has {len(stations)} polling stations:")
        for station in stations:
            file_path = parser.get_station_file(sample_ward, station['number'])
            if file_path:
                print(f"  {station['number']}: {station['name']}")
                print(f"    File: {file_path}")

    return parser


if __name__ == "__main__":
    test_parser()