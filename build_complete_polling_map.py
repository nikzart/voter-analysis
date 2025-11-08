#!/usr/bin/env python3
"""
Build complete polling_stations_map.json from existing CSV files in output_with_religion/
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Ward list from user
WARDS = [
    {"value": "q7ZP0QkZVY", "text": "001 - SAKTHIKULANGARA HARBOUR"},
    {"value": "WALNgGOZK6", "text": "002 - SAKTHIKULANGARA"},
    {"value": "anZbRbQZ65", "text": "003 - MEENATHUCHERY"},
    {"value": "2VZAWJNXqe", "text": "004 - KAVANAD"},
    {"value": "MOZ4WaaLAD", "text": "005 - VALLIKEEZHU"},
    {"value": "MVLzW6VZgA", "text": "006 - KUREEPUZHA WEST"},
    {"value": "b5X8WaoBq1", "text": "007 - KUREEPUZHA"},
    {"value": "GaB2Wa1XAq", "text": "008 - NEERAVIL"},
    {"value": "AKXRkM4L9o", "text": "009 - ANCHALUMMOODU WEST"},
    {"value": "20Xk2Y0Bg9", "text": "010 - ANCHALUMMOODU EAST"},
    {"value": "4WXyW7lZ3G", "text": "011 - KADAVOOR"},
    {"value": "wNL5WazB8b", "text": "012 - MATHILIL"},
    {"value": "woXGk4aXxV", "text": "013 - THEVALLY"},
    {"value": "k8XvWDVLO9", "text": "014 - VADAKKUMBHAGAM"},
    {"value": "7eXQklDZ8m", "text": "015 - ASRAMAM"},
    {"value": "3KXl4vJX8g", "text": "016 - ULIYAKOVIL"},
    {"value": "2VZMD57LKM", "text": "017 - ULIYAKOVIL EAST"},
    {"value": "Q9ZxWnPL2O", "text": "018 - KADAPPAKADA"},
    {"value": "7mXe6zaLOg", "text": "019 - KOYIKKAL"},
    {"value": "ErLmzQJZ7Y", "text": "020 - KALLUMTHAZHAM"},
    {"value": "20XkAR3Zg9", "text": "021 - MANGADU"},
    {"value": "y6Z0Wd8LKE", "text": "022 - ARUNNOOTTIMANGALAM"},
    {"value": "oeX9edDXkq", "text": "023 - CHATHINAMKULAM"},
    {"value": "nNXDeoDL4J", "text": "024 - KARIKODE"},
    {"value": "aQBV7ejX5w", "text": "025 - COLLEGE DIVISION"},
    {"value": "41Xjb2vXbW", "text": "026 - PALKULANGARA"},
    {"value": "r6XqWlgZRO", "text": "027 - AMMANNADA"},
    {"value": "OABKk82B82", "text": "028 - VADAKKEVILA"},
    {"value": "MlZa2JwB0G", "text": "029 - PALLIMUKKU"},
    {"value": "6zLwW0MLRV", "text": "030 - AYATHIL"},
    {"value": "RQBd7N8Zm3", "text": "031 - KILIKOLLOOR"},
    {"value": "VnBWYmEL5r", "text": "032 - PUNTHALATHAZHAM"},
    {"value": "8KLpRQOBqx", "text": "033 - PALATHARA"},
    {"value": "EAL33dzL89", "text": "034 - MANACADU"},
    {"value": "n6Zgo4oZor", "text": "035 - KOLLOORVILA"},
    {"value": "o7LEmPQL2e", "text": "036 - KAYYALAKKAL"},
    {"value": "w2XOk51X4K", "text": "037 - VALATHUNGAL"},
    {"value": "lMB1WdxLbV", "text": "038 - AKKOLIL"},
    {"value": "odLrWMGZ39", "text": "039 - THEKKUMBHAGAM"},
    {"value": "WxLYo02BME", "text": "040 - ERAVIPUARAM"},
    {"value": "91Bn8G9LwD", "text": "041 - BHARANIKKAVU"},
    {"value": "QNL7WdNLEG", "text": "042 - THEKKEVILA"},
    {"value": "P3L6WdlZON", "text": "043 - MUNDAKKAL"},
    {"value": "3bZJ9zoLN9", "text": "044 - PATTATHANAM"},
    {"value": "14Xo2vGBJr", "text": "045 - CONTONMENT"},
    {"value": "q7ZP0GkZVY", "text": "046 - UDAYAMARTHANDAPUARAM"},
    {"value": "WALNgyOZK6", "text": "047 - THAMARAKULAM"},
    {"value": "2VZAWYNXqe", "text": "048 - PORT"},
    {"value": "MVLzWVVZgA", "text": "049 - KAIKULANGARA"},
    {"value": "MOZ4WdaLAD", "text": "050 - CUTCHERY"},
    {"value": "b5X8WdoBq1", "text": "051 - THANGASSERY"},
    {"value": "GaB2W31XAq", "text": "052 - THIRUMULLAVARAM"},
    {"value": "AKXRkQ4L9o", "text": "053 - MULANKADAKAM"},
    {"value": "4WXyWYlZ3G", "text": "054 - ALATTUKAVU"},
    {"value": "wNL5WdzB8b", "text": "055 - KANNIMEL WEST"},
    {"value": "anZbRoQZ65", "text": "056 - KANNIMEL"}
]

def sanitize_ward_name(ward_text):
    """Convert ward text to folder name"""
    return ward_text.replace('/', '_').replace(' ', '_')

def unsanitize_station_name(filename):
    """Convert CSV filename back to polling station text"""
    # Remove .csv extension
    name = filename.replace('.csv', '')
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    return name

def main():
    output_dir = Path('/Users/nikzart/Developer/aislop-server/output_with_religion')

    polling_map = {
        "discovery_timestamp": datetime.now().isoformat(),
        "district": "13",
        "local_body": "eMVLzGlZgA",
        "wards": [],
        "total_wards": 0,
        "total_polling_stations": 0
    }

    total_stations = 0

    for ward in WARDS:
        ward_text = ward["text"]
        ward_folder = sanitize_ward_name(ward_text)
        ward_path = output_dir / ward_folder

        if not ward_path.exists():
            print(f"Warning: Ward folder not found: {ward_folder}")
            continue

        # Find all CSV files in this ward
        csv_files = sorted(ward_path.glob('*.csv'))

        if not csv_files:
            print(f"Warning: No CSV files in {ward_folder}")
            continue

        polling_stations = []
        for csv_file in csv_files:
            # Generate a unique value (we don't have the original, so generate one)
            station_value = f"gen_{len(polling_stations)}"

            # Read the actual polling_station value from the CSV file
            try:
                df = pd.read_csv(csv_file, nrows=1)
                if 'polling_station' in df.columns:
                    station_text = df['polling_station'].iloc[0]
                else:
                    # Fallback to filename if column doesn't exist
                    station_text = unsanitize_station_name(csv_file.name)
            except Exception as e:
                print(f"Warning: Could not read {csv_file.name}: {e}")
                station_text = unsanitize_station_name(csv_file.name)

            polling_stations.append({
                "value": station_value,
                "text": station_text
            })

        polling_map["wards"].append({
            "value": ward["value"],
            "text": ward_text,
            "polling_stations": polling_stations
        })

        total_stations += len(polling_stations)
        print(f"✓ {ward_text}: {len(polling_stations)} stations")

    polling_map["total_wards"] = len(polling_map["wards"])
    polling_map["total_polling_stations"] = total_stations

    # Save to file
    output_file = Path('/Users/nikzart/Developer/aislop-server/polling_stations_map_complete.json')
    with open(output_file, 'w') as f:
        json.dump(polling_map, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Complete polling stations map saved to:")
    print(f"  {output_file}")
    print(f"Total wards: {polling_map['total_wards']}")
    print(f"Total polling stations: {total_stations}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
