"""
Main Script to Generate Election Insights Reports for All Polling Stations
Processes all 62 polling stations and creates comprehensive campaign reports
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import sys

# Add analysis directory to path
sys.path.insert(0, str(Path(__file__).parent))

from analysis.hierarchy_parser import HierarchyParser
from analysis.reports.election_report_generator import ElectionReportGenerator


def main():
    """Generate election insights reports for all polling stations"""

    print("=" * 80)
    print("KERALA ELECTION INSIGHTS REPORT GENERATION")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Paths
    base_dir = Path(__file__).parent
    hierarchy_file = base_dir.parent / 'polling_stations_map.json'
    csv_dir = base_dir.parent / 'output_with_religion'
    report_dir = base_dir / 'reports' / 'election_insights'

    # Load hierarchy
    print("Loading ward-polling station hierarchy...")
    parser = HierarchyParser(str(hierarchy_file), str(csv_dir))
    hierarchy = parser.hierarchy

    print(f"  Total Wards: {len(hierarchy)}")
    total_stations = sum(len(ward['stations']) for ward in hierarchy.values())
    print(f"  Total Polling Stations: {total_stations}")
    print(f"  Mapped CSV Files: {len(parser.station_to_file_map)}\n")

    # Statistics
    total_voters_processed = 0
    reports_generated = 0
    failed_stations = []

    # Process each ward
    for ward_code in sorted(hierarchy.keys()):
        ward_info = hierarchy[ward_code]
        ward_name = ward_info['name']

        print(f"\nProcessing Ward: {ward_code} - {ward_name}")
        print("-" * 60)

        ward_voters = 0
        ward_reports = 0

        # Process each station in the ward
        for station in ward_info['stations']:
            station_number = station['number']
            station_name = station['name']
            full_station_id = f"{ward_code}/{station_number}"

            print(f"  Processing {station_number}: {station_name}...")

            # Get CSV file for this station
            csv_file = parser.station_to_file_map.get(full_station_id)

            if not csv_file:
                print(f"    ⚠ No data file found - Skipping")
                failed_stations.append({
                    'ward': ward_name,
                    'station': station_name,
                    'reason': 'No CSV file'
                })
                continue

            try:
                # Load data
                data = pd.read_csv(csv_file)
                voter_count = len(data)
                print(f"    Loaded {voter_count:,} voters")

                if voter_count == 0:
                    print(f"    ⚠ Empty dataset - Skipping")
                    failed_stations.append({
                        'ward': ward_name,
                        'station': station_name,
                        'reason': 'Empty dataset'
                    })
                    continue

                # Generate election insights report with AI
                print(f"    Generating election insights report with AI...")
                generator = ElectionReportGenerator(data, station_name, ward_name, enable_ai=True)

                # Create output path
                output_dir = report_dir / f"{ward_code}_{ward_name}" / f"{station_number}_{station_name.replace('/', '_').replace(' ', '_')}"
                output_file = output_dir / 'election_report.html'

                # Save report
                generator.save_report(output_file)

                print(f"    ✓ Report saved to {output_file}")

                ward_voters += voter_count
                ward_reports += 1
                reports_generated += 1
                total_voters_processed += voter_count

            except Exception as e:
                print(f"    ✗ Error: {str(e)}")
                failed_stations.append({
                    'ward': ward_name,
                    'station': station_name,
                    'reason': str(e)
                })

        print(f"\n  Ward Summary: {ward_reports}/{len(ward_info['stations'])} stations processed")
        print(f"  Total Voters in Ward: {ward_voters:,}")

    # Generate master summary
    print("\n" + "=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"Total Reports Generated: {reports_generated}/{total_stations}")
    print(f"Total Voters Analyzed: {total_voters_processed:,}")
    print(f"Failed Stations: {len(failed_stations)}")

    # Save master summary
    summary = {
        'generation_date': datetime.now().isoformat(),
        'total_wards': len(hierarchy),
        'total_stations': total_stations,
        'reports_generated': reports_generated,
        'total_voters_analyzed': total_voters_processed,
        'failed_stations': failed_stations,
        'ward_breakdown': {}
    }

    for ward_code, ward_info in hierarchy.items():
        ward_reports = sum(1 for s in ward_info['stations']
                          if f"{ward_code}/{s['number']}" in parser.station_to_file_map)
        summary['ward_breakdown'][f"{ward_code}_{ward_info['name']}"] = {
            'total_stations': len(ward_info['stations']),
            'reports_generated': ward_reports
        }

    summary_file = report_dir / 'generation_summary.json'
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\nSummary saved to: {summary_file}")

    if failed_stations:
        print("\n⚠ Failed Stations:")
        for fail in failed_stations:
            print(f"  - {fail['ward']} / {fail['station']}: {fail['reason']}")

    print("\n✅ All reports available in: " + str(report_dir))


if __name__ == "__main__":
    main()