#!/usr/bin/env python3
"""
Generate All Polling Station Reports
Main script to generate comprehensive reports for all 239 polling stations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import time

# Import modules
from analysis.hierarchy_parser import HierarchyParser
from analysis.polling_station_analyzer import PollingStationAnalyzer
from analysis.reports.report_generator import ReportGenerator

def generate_all_reports():
    """Generate reports for all polling stations"""
    print("="*80)
    print("KERALA VOTER DATA ANALYSIS - REPORT GENERATION")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Initialize hierarchy parser
    print("Loading ward-polling station hierarchy...")
    parser = HierarchyParser(
        hierarchy_file='/Users/nikzart/Developer/aislop-server/polling_stations_map.json',
        data_dir='/Users/nikzart/Developer/aislop-server/output_with_religion'
    )

    stats = parser.get_hierarchy_stats()
    print(f"  Total Wards: {stats['total_wards']}")
    print(f"  Total Polling Stations: {stats['total_stations']}")
    print(f"  Mapped CSV Files: {stats['mapped_files']}")
    print()

    # Output directory
    output_base = '/Users/nikzart/Developer/aislop-server/voter-analysis/reports/by_ward'
    data_output_base = '/Users/nikzart/Developer/aislop-server/voter-analysis/data/processed/by_ward'

    # Statistics tracking
    total_processed = 0
    successful = 0
    failed = 0
    ward_stats = {}

    # Process each ward
    for ward_key in sorted(parser.hierarchy.keys()):
        ward_info = parser.hierarchy[ward_key]
        ward_code = ward_info['code']
        ward_name = ward_info['name']

        print(f"\nProcessing Ward: {ward_code} - {ward_name}")
        print("-" * 60)

        ward_successful = 0
        ward_failed = 0
        ward_total_voters = 0
        ward_analyses = []

        # Process each polling station in the ward
        for station in ward_info['stations']:
            station_num = station['number']
            station_name = station['name']

            # Get CSV file path
            csv_path = parser.get_station_file(ward_key, station_num)

            if not csv_path or not Path(csv_path).exists():
                print(f"  ⚠ {station_num}: {station_name} - No data file found")
                failed += 1
                ward_failed += 1
                continue

            try:
                # Analyze polling station
                print(f"  Processing {station_num}: {station_name}...")
                analyzer = PollingStationAnalyzer(
                    ward_code=ward_code,
                    ward_name=ward_name,
                    station_num=station_num,
                    station_name=station_name,
                    csv_path=csv_path
                )

                # Run analysis
                results = analyzer.run_analysis()

                # Save analysis results
                station_output_dir = analyzer.save_results(data_output_base)

                # Generate HTML report
                report_gen = ReportGenerator(
                    analysis_results=results,
                    output_dir=f"{output_base}/{ward_code}_{ward_name}/{station_num}_{station_name.replace(' ', '_')[:50]}"
                )
                report_path = report_gen.save_report()

                # Track statistics
                successful += 1
                ward_successful += 1
                ward_total_voters += results['metadata']['total_voters']
                ward_analyses.append(results)

                print(f"    ✓ Analysis complete: {results['metadata']['total_voters']} voters")

            except Exception as e:
                print(f"    ✗ Error: {e}")
                failed += 1
                ward_failed += 1

            total_processed += 1

        # Generate ward summary
        if ward_analyses:
            print(f"\n  Generating ward summary...")
            generate_ward_summary(
                ward_code=ward_code,
                ward_name=ward_name,
                station_analyses=ward_analyses,
                output_dir=f"{output_base}/{ward_code}_{ward_name}"
            )

        # Store ward statistics
        ward_stats[ward_key] = {
            'code': ward_code,
            'name': ward_name,
            'total_stations': len(ward_info['stations']),
            'successful': ward_successful,
            'failed': ward_failed,
            'total_voters': ward_total_voters
        }

        print(f"\n  Ward Summary: {ward_successful}/{len(ward_info['stations'])} stations processed")
        print(f"  Total Voters in Ward: {ward_total_voters:,}")

    # Generate master summary
    print("\n" + "="*80)
    print("GENERATING MASTER SUMMARY...")
    generate_master_summary(ward_stats, output_base)

    # Final statistics
    print("\n" + "="*80)
    print("REPORT GENERATION COMPLETE")
    print("="*80)
    print(f"Total Polling Stations Processed: {total_processed}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"Success Rate: {successful/total_processed*100:.1f}%")
    print(f"\nReports saved to: {output_base}")
    print(f"Analysis data saved to: {data_output_base}")
    print(f"\nEnd Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def generate_ward_summary(ward_code: str, ward_name: str, station_analyses: List[Dict], output_dir: str):
    """Generate ward-level summary report"""
    # Aggregate statistics
    total_voters = sum(a['metadata']['total_voters'] for a in station_analyses)
    total_stations = len(station_analyses)

    # Calculate ward-wide demographics
    ward_summary = {
        'ward_code': ward_code,
        'ward_name': ward_name,
        'total_stations': total_stations,
        'total_voters': total_voters,
        'stations': []
    }

    # Aggregate religion distribution
    religion_totals = {'Hindu': 0, 'Christian': 0, 'Muslim': 0}
    gender_totals = {'male': 0, 'female': 0}
    age_sum = 0
    age_count = 0

    for analysis in station_analyses:
        # Add station summary
        ward_summary['stations'].append({
            'name': analysis['metadata']['station_name'],
            'voters': analysis['metadata']['total_voters']
        })

        # Aggregate demographics
        demo = analysis.get('demographics', {}).get('basic_stats', {})

        if 'religion_distribution' in demo:
            dist = demo['religion_distribution'].get('distribution', {})
            for rel in religion_totals:
                religion_totals[rel] += dist.get(rel.lower(), 0)

        if 'gender_distribution' in demo:
            gender = demo['gender_distribution']
            gender_totals['male'] += gender.get('male_count', 0)
            gender_totals['female'] += gender.get('female_count', 0)

        if 'age_statistics' in demo:
            age_stats = demo['age_statistics']
            if 'mean_age' in age_stats:
                age_sum += age_stats['mean_age'] * analysis['metadata']['total_voters']
                age_count += analysis['metadata']['total_voters']

    # Calculate percentages
    ward_summary['demographics'] = {
        'religion': {
            'Hindu': round(religion_totals['Hindu'] / total_voters * 100, 1),
            'Christian': round(religion_totals['Christian'] / total_voters * 100, 1),
            'Muslim': round(religion_totals['Muslim'] / total_voters * 100, 1)
        },
        'gender': {
            'male': gender_totals['male'],
            'female': gender_totals['female'],
            'ratio': round(gender_totals['female'] / gender_totals['male'] * 1000) if gender_totals['male'] > 0 else 0
        },
        'average_age': round(age_sum / age_count, 1) if age_count > 0 else 0
    }

    # Save ward summary
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    with open(output_path / 'ward_summary.json', 'w') as f:
        json.dump(ward_summary, f, indent=2)

    # Generate HTML summary
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{ward_name} - Ward Summary</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .stat-box {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #667eea; color: white; }}
    </style>
</head>
<body>
    <h1>{ward_code} - {ward_name}</h1>
    <h2>Ward Summary Report</h2>

    <div class="stats">
        <div class="stat-box">
            <div class="stat-value">{total_voters:,}</div>
            <div class="stat-label">Total Voters</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{total_stations}</div>
            <div class="stat-label">Polling Stations</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{ward_summary['demographics']['average_age']}</div>
            <div class="stat-label">Average Age</div>
        </div>
    </div>

    <h3>Religious Composition</h3>
    <table>
        <tr><th>Religion</th><th>Percentage</th></tr>
        <tr><td>Hindu</td><td>{ward_summary['demographics']['religion']['Hindu']}%</td></tr>
        <tr><td>Christian</td><td>{ward_summary['demographics']['religion']['Christian']}%</td></tr>
        <tr><td>Muslim</td><td>{ward_summary['demographics']['religion']['Muslim']}%</td></tr>
    </table>

    <h3>Polling Stations</h3>
    <table>
        <tr><th>Station Name</th><th>Total Voters</th></tr>
"""
    for station in ward_summary['stations']:
        html += f"<tr><td>{station['name']}</td><td>{station['voters']:,}</td></tr>"

    html += """
    </table>
</body>
</html>
"""

    with open(output_path / 'ward_summary.html', 'w') as f:
        f.write(html)


def generate_master_summary(ward_stats: Dict, output_dir: str):
    """Generate Kerala-wide master summary"""
    total_voters = sum(w['total_voters'] for w in ward_stats.values())
    total_wards = len(ward_stats)
    total_stations = sum(w['total_stations'] for w in ward_stats.values())
    successful_stations = sum(w['successful'] for w in ward_stats.values())

    summary = {
        'generated_at': datetime.now().isoformat(),
        'total_wards': total_wards,
        'total_polling_stations': total_stations,
        'processed_stations': successful_stations,
        'total_voters_analyzed': total_voters,
        'wards': ward_stats
    }

    # Save master summary
    output_path = Path(output_dir) / 'kerala_master_summary.json'
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"Master summary saved to {output_path}")


if __name__ == "__main__":
    generate_all_reports()