"""
Polling Station Analyzer and Report Generator
Orchestrates analysis and generates comprehensive reports for each polling station
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import analysis modules
from analysis.core.demographics import DemographicAnalyzer
from analysis.core.family_analysis import FamilyAnalyzer

class PollingStationAnalyzer:
    """Complete analysis pipeline for a polling station"""

    def __init__(self, ward_code: str, ward_name: str, station_num: str, station_name: str, csv_path: str):
        self.ward_code = ward_code
        self.ward_name = ward_name
        self.station_num = station_num
        self.station_name = station_name
        self.csv_path = csv_path
        self.data = None
        self.analysis_results = {}

    def load_data(self) -> bool:
        """Load and validate CSV data"""
        try:
            self.data = pd.read_csv(self.csv_path)
            print(f"Loaded {len(self.data)} records from {self.station_name}")
            return True
        except Exception as e:
            print(f"Error loading data for {self.station_name}: {e}")
            return False

    def run_analysis(self) -> Dict:
        """Run complete analysis pipeline"""
        if self.data is None:
            if not self.load_data():
                return {'error': 'Failed to load data'}

        print(f"Analyzing {self.ward_name} - {self.station_name}...")

        # Metadata
        self.analysis_results['metadata'] = {
            'ward_code': self.ward_code,
            'ward_name': self.ward_name,
            'station_number': self.station_num,
            'station_name': self.station_name,
            'total_voters': len(self.data),
            'analysis_timestamp': datetime.now().isoformat(),
            'data_file': self.csv_path
        }

        # Demographic Analysis
        print("  Running demographic analysis...")
        demo_analyzer = DemographicAnalyzer(self.data)
        self.analysis_results['demographics'] = {
            'basic_stats': demo_analyzer.get_basic_stats(),
            'cross_tabulations': demo_analyzer.get_cross_tabulations(),
            'population_pyramid': demo_analyzer.get_population_pyramid_data(),
            'electoral_insights': demo_analyzer.get_electoral_insights()
        }

        # Family Analysis
        print("  Running family structure analysis...")
        family_analyzer = FamilyAnalyzer(self.data)
        self.analysis_results['family_analysis'] = family_analyzer.get_family_statistics()
        self.analysis_results['kinship_networks'] = family_analyzer.get_kinship_networks()

        # Unique Characteristics
        print("  Identifying unique characteristics...")
        self.analysis_results['unique_characteristics'] = self._identify_unique_characteristics()

        # Data Quality
        self.analysis_results['data_quality'] = self._assess_data_quality()

        return self.analysis_results

    def _identify_unique_characteristics(self) -> Dict:
        """Identify unique characteristics of this polling station"""
        characteristics = {}

        # Check for unusual demographics
        if 'demographics' in self.analysis_results:
            demo = self.analysis_results['demographics']['basic_stats']

            # Religion dominance
            if 'religion_distribution' in demo:
                religion = demo['religion_distribution']
                if 'percentages' in religion:
                    for rel_name, rel_key in [('Hindu', 'hindu_percentage'),
                                             ('Christian', 'christian_percentage'),
                                             ('Muslim', 'muslim_percentage')]:
                        if rel_key in religion['percentages']:
                            pct = religion['percentages'][rel_key]
                            if pct > 75:
                                characteristics['religion_dominance'] = f"{rel_name} dominated ({pct}%)"
                            elif pct < 5:
                                characteristics[f'low_{rel_name.lower()}'] = f"Very few {rel_name} voters ({pct}%)"

            # Age characteristics
            if 'age_statistics' in demo:
                age_stats = demo['age_statistics']
                if 'mean_age' in age_stats:
                    mean_age = age_stats['mean_age']
                    if mean_age < 35:
                        characteristics['young_population'] = f"Young demographic (avg age: {mean_age})"
                    elif mean_age > 50:
                        characteristics['aging_population'] = f"Aging demographic (avg age: {mean_age})"

                if 'age_group_percentages' in age_stats:
                    youth_pct = age_stats['age_group_percentages'].get('youth_18_30', 0)
                    if youth_pct > 40:
                        characteristics['youth_concentration'] = f"High youth concentration ({youth_pct}%)"

            # Gender characteristics
            if 'gender_distribution' in demo:
                gender = demo['gender_distribution']
                if 'gender_ratio' in gender:
                    ratio = gender['gender_ratio']
                    if ratio > 1100:
                        characteristics['female_majority'] = f"Strong female majority (ratio: {ratio})"
                    elif ratio < 900:
                        characteristics['male_majority'] = f"Male majority (ratio: {ratio})"

        # Family characteristics
        if 'family_analysis' in self.analysis_results:
            family = self.analysis_results['family_analysis']
            if 'household_analysis' in family:
                households = family['household_analysis']
                if 'average_household_size' in households:
                    avg_size = households['average_household_size']
                    if avg_size > 5:
                        characteristics['large_families'] = f"Large family sizes (avg: {avg_size})"
                    elif avg_size < 2.5:
                        characteristics['small_families'] = f"Small household sizes (avg: {avg_size})"

                if 'multi_family_houses' in households:
                    multi = households['multi_family_houses']
                    if multi > 10:
                        characteristics['multi_family_housing'] = f"{multi} multi-family houses"

            if 'inter_religious_families' in family:
                inter_rel = family['inter_religious_families']
                if 'total_inter_religious_houses' in inter_rel:
                    count = inter_rel['total_inter_religious_houses']
                    if count > 5:
                        characteristics['religious_integration'] = f"{count} inter-religious households"

        return characteristics

    def _assess_data_quality(self) -> Dict:
        """Assess data quality and completeness"""
        quality = {
            'total_records': len(self.data),
            'completeness': {},
            'issues': []
        }

        # Check completeness of each column
        for col in self.data.columns:
            null_count = self.data[col].isnull().sum()
            completeness = round((1 - null_count / len(self.data)) * 100, 2)
            quality['completeness'][col] = completeness

            if completeness < 95:
                quality['issues'].append(f"{col}: {completeness}% complete")

        # Check for data anomalies
        if 'Age' in self.data.columns:
            age_anomalies = self.data[(self.data['Age'] < 18) | (self.data['Age'] > 120)]['Age'].count()
            if age_anomalies > 0:
                quality['issues'].append(f"{age_anomalies} age anomalies detected")

        # Check for duplicate records
        if 'New SEC ID No.' in self.data.columns:
            duplicates = self.data['New SEC ID No.'].duplicated().sum()
            if duplicates > 0:
                quality['issues'].append(f"{duplicates} duplicate SEC IDs")

        quality['quality_score'] = round(100 - len(quality['issues']) * 5, 0)
        quality['quality_grade'] = 'Excellent' if quality['quality_score'] >= 95 else \
                                  'Good' if quality['quality_score'] >= 85 else \
                                  'Fair' if quality['quality_score'] >= 75 else 'Poor'

        return quality

    def save_results(self, output_dir: str):
        """Save analysis results to files"""
        # Create output directory
        station_dir = Path(output_dir) / f"{self.ward_code}_{self.ward_name}" / f"{self.station_num}_{self.station_name.replace(' ', '_')[:50]}"
        station_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON results
        json_path = station_dir / "analysis_results.json"
        with open(json_path, 'w') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)

        # Save summary CSV
        summary_df = self._create_summary_dataframe()
        csv_path = station_dir / "summary_statistics.csv"
        summary_df.to_csv(csv_path, index=False)

        print(f"  Results saved to {station_dir}")
        return station_dir

    def _create_summary_dataframe(self) -> pd.DataFrame:
        """Create summary statistics dataframe"""
        summary = []

        # Basic demographics
        if 'demographics' in self.analysis_results:
            demo = self.analysis_results['demographics']['basic_stats']
            summary.append({
                'Category': 'Total Voters',
                'Value': demo.get('total_voters', 'N/A')
            })

            if 'gender_distribution' in demo:
                gender = demo['gender_distribution']
                summary.append({
                    'Category': 'Male Voters',
                    'Value': f"{gender.get('male_count', 0)} ({gender.get('male_percentage', 0)}%)"
                })
                summary.append({
                    'Category': 'Female Voters',
                    'Value': f"{gender.get('female_count', 0)} ({gender.get('female_percentage', 0)}%)"
                })
                summary.append({
                    'Category': 'Gender Ratio (F per 1000 M)',
                    'Value': gender.get('gender_ratio', 'N/A')
                })

            if 'age_statistics' in demo:
                age = demo['age_statistics']
                summary.append({
                    'Category': 'Average Age',
                    'Value': age.get('mean_age', 'N/A')
                })
                if 'age_group_percentages' in age:
                    age_groups = age['age_group_percentages']
                    summary.append({
                        'Category': 'Youth (18-30)',
                        'Value': f"{age_groups.get('youth_18_30', 0)}%"
                    })
                    summary.append({
                        'Category': 'Middle Age (31-60)',
                        'Value': f"{age_groups.get('middle_31_60', 0)}%"
                    })
                    summary.append({
                        'Category': 'Senior (60+)',
                        'Value': f"{age_groups.get('senior_60_plus', 0)}%"
                    })

            if 'religion_distribution' in demo:
                religion = demo['religion_distribution']
                if 'percentages' in religion:
                    percentages = religion['percentages']
                    summary.append({
                        'Category': 'Hindu',
                        'Value': f"{percentages.get('hindu_percentage', 0)}%"
                    })
                    summary.append({
                        'Category': 'Christian',
                        'Value': f"{percentages.get('christian_percentage', 0)}%"
                    })
                    summary.append({
                        'Category': 'Muslim',
                        'Value': f"{percentages.get('muslim_percentage', 0)}%"
                    })

        # Family statistics
        if 'family_analysis' in self.analysis_results:
            family = self.analysis_results['family_analysis']
            if 'household_analysis' in family:
                households = family['household_analysis']
                summary.append({
                    'Category': 'Total Houses',
                    'Value': households.get('total_houses', 'N/A')
                })
                summary.append({
                    'Category': 'Avg Household Size',
                    'Value': households.get('average_household_size', 'N/A')
                })

        return pd.DataFrame(summary)