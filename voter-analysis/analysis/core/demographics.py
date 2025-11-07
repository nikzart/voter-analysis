"""
Demographic Analysis Module for Kerala Voter Data
Provides comprehensive demographic analysis for polling stations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import Counter
import re
import builtins

class DemographicAnalyzer:
    """Analyze demographic patterns in voter data"""

    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.total_voters = len(data)
        self._preprocess_data()

    def _preprocess_data(self):
        """Preprocess data for analysis"""
        # Extract age and gender from "Gender / Age" column
        if 'Gender / Age' in self.data.columns:
            self.data[['Gender', 'Age']] = self.data['Gender / Age'].str.extract(r'([MF])\s*/\s*(\d+)')
            self.data['Age'] = pd.to_numeric(self.data['Age'], errors='coerce')

            # Fix age anomalies (e.g., age > 150)
            self.data.loc[self.data['Age'] > 150, 'Age'] = np.nan

            # Fill missing ages with median
            median_age = self.data['Age'].median()
            if pd.notna(median_age):
                self.data['Age'].fillna(median_age, inplace=True)

    def get_basic_stats(self) -> Dict:
        """Get basic demographic statistics"""
        stats = {
            'total_voters': self.total_voters,
            'gender_distribution': self._get_gender_distribution(),
            'age_statistics': self._get_age_statistics(),
            'religion_distribution': self._get_religion_distribution(),
            'house_statistics': self._get_house_statistics()
        }
        return stats

    def _get_gender_distribution(self) -> Dict:
        """Calculate gender distribution"""
        if 'Gender' not in self.data.columns:
            return {'error': 'Gender data not available'}

        gender_counts = self.data['Gender'].value_counts()
        total = gender_counts.sum()

        return {
            'male_count': int(gender_counts.get('M', 0)),
            'female_count': int(gender_counts.get('F', 0)),
            'male_percentage': round(gender_counts.get('M', 0) / total * 100, 2) if total > 0 else 0,
            'female_percentage': round(gender_counts.get('F', 0) / total * 100, 2) if total > 0 else 0,
            'gender_ratio': round(gender_counts.get('F', 0) / gender_counts.get('M', 1) * 1000) if gender_counts.get('M', 0) > 0 else 0
        }

    def _get_age_statistics(self) -> Dict:
        """Calculate age-related statistics"""
        if 'Age' not in self.data.columns:
            return {'error': 'Age data not available'}

        age_data = self.data['Age'].dropna()

        # Age groups
        age_groups = {
            'youth_18_30': int(((age_data >= 18) & (age_data <= 30)).sum()),
            'middle_31_60': int(((age_data >= 31) & (age_data <= 60)).sum()),
            'senior_60_plus': int((age_data > 60).sum()),
            'first_time_18_21': int(((age_data >= 18) & (age_data <= 21)).sum()),
            'elderly_65_plus': int((age_data >= 65).sum())
        }

        # Generational breakdown
        current_year = 2025
        generations = {
            'gen_z_18_29': int(((age_data >= 18) & (age_data <= 29)).sum()),
            'millennials_30_44': int(((age_data >= 30) & (age_data <= 44)).sum()),
            'gen_x_45_59': int(((age_data >= 45) & (age_data <= 59)).sum()),
            'boomers_60_74': int(((age_data >= 60) & (age_data <= 74)).sum()),
            'silent_75_plus': int((age_data >= 75).sum())
        }

        total_age_data = len(age_data)
        return {
            'mean_age': round(age_data.mean(), 1),
            'median_age': round(age_data.median(), 1),
            'min_age': int(age_data.min()),
            'max_age': int(age_data.max()),
            'age_groups': age_groups,
            'age_group_percentages': {k: round(v/total_age_data*100, 1) if total_age_data > 0 else 0 for k, v in age_groups.items()},
            'generations': generations,
            'generation_percentages': {k: round(v/total_age_data*100, 1) if total_age_data > 0 else 0 for k, v in generations.items()}
        }

    def _get_religion_distribution(self) -> Dict:
        """Calculate religion distribution"""
        if 'religion' not in self.data.columns:
            return {'error': 'Religion data not available'}

        religion_counts = self.data['religion'].value_counts()
        total = int(religion_counts.sum())

        distribution = {}
        percentages = {}

        for religion in ['Hindu', 'Christian', 'Muslim']:
            count = int(religion_counts.get(religion, 0))
            distribution[religion.lower()] = count
            percentages[f"{religion.lower()}_percentage"] = round(count / total * 100, 2) if total > 0 else 0

        # Diversity index (Simpson's Diversity Index)
        diversity_index = 0
        if total > 0:
            diversity_sum = 0
            for count in religion_counts.values:  # Use .values property, not .values() method
                diversity_sum += (count/total)**2
            diversity_index = 1 - diversity_sum

        return {
            'distribution': distribution,
            'percentages': percentages,
            'diversity_index': round(diversity_index, 3),
            'majority_religion': religion_counts.index[0] if len(religion_counts) > 0 else 'Unknown'
        }

    def _get_house_statistics(self) -> Dict:
        """Calculate house-related statistics"""
        if 'House Name' not in self.data.columns:
            return {'error': 'House data not available'}

        # Count voters per house
        house_counts = self.data.groupby('House Name').size()

        # Identify house name patterns
        house_types = {
            'bhavan_bhavanam': 0,
            'villa_nivas': 0,
            'mandiram_vihar': 0,
            'manzil_house': 0,
            'traditional': 0,
            'other': 0
        }

        for house in self.data['House Name'].unique():
            if pd.isna(house):
                continue
            house_lower = str(house).lower()
            if 'bhavan' in house_lower or 'bhavanam' in house_lower:
                house_types['bhavan_bhavanam'] += 1
            elif 'villa' in house_lower or 'nivas' in house_lower:
                house_types['villa_nivas'] += 1
            elif 'mandiram' in house_lower or 'vihar' in house_lower:
                house_types['mandiram_vihar'] += 1
            elif 'manzil' in house_lower or 'house' in house_lower:
                house_types['manzil_house'] += 1
            elif any(x in house_lower for x in ['veedu', 'illam', 'tharavad']):
                house_types['traditional'] += 1
            else:
                house_types['other'] += 1

        return {
            'total_houses': len(house_counts),
            'avg_voters_per_house': round(house_counts.mean(), 2),
            'max_voters_in_house': int(house_counts.max()),
            'min_voters_in_house': int(house_counts.min()),
            'single_voter_houses': int((house_counts == 1).sum()),
            'large_houses_5_plus': int((house_counts >= 5).sum()),
            'house_size_distribution': {
                '1_person': int((house_counts == 1).sum()),
                '2_3_persons': int(((house_counts >= 2) & (house_counts <= 3)).sum()),
                '4_5_persons': int(((house_counts >= 4) & (house_counts <= 5)).sum()),
                '6_plus_persons': int((house_counts >= 6).sum())
            },
            'house_name_patterns': house_types
        }

    def get_cross_tabulations(self) -> Dict:
        """Generate cross-tabulations of demographics"""
        cross_tabs = {}

        # Religion x Gender
        if 'religion' in self.data.columns and 'Gender' in self.data.columns:
            cross_tabs['religion_gender'] = pd.crosstab(
                self.data['religion'],
                self.data['Gender']
            ).to_dict()

        # Religion x Age Groups
        if 'religion' in self.data.columns and 'Age' in self.data.columns:
            age_groups = pd.cut(self.data['Age'],
                               bins=[0, 30, 60, 100],
                               labels=['Youth_18-30', 'Middle_31-60', 'Senior_60+'])
            cross_tabs['religion_age'] = pd.crosstab(
                self.data['religion'],
                age_groups
            ).to_dict()

        # Gender x Age Groups
        if 'Gender' in self.data.columns and 'Age' in self.data.columns:
            age_groups = pd.cut(self.data['Age'],
                               bins=[0, 30, 60, 100],
                               labels=['Youth_18-30', 'Middle_31-60', 'Senior_60+'])
            cross_tabs['gender_age'] = pd.crosstab(
                self.data['Gender'],
                age_groups
            ).to_dict()

        return cross_tabs

    def get_population_pyramid_data(self) -> Dict:
        """Get data for population pyramid visualization"""
        if 'Age' not in self.data.columns or 'Gender' not in self.data.columns:
            return {'error': 'Age or Gender data not available'}

        # Create age bins
        age_bins = list(range(0, 101, 5))
        age_labels = [f"{i}-{i+4}" for i in age_bins[:-1]]

        self.data['age_group'] = pd.cut(self.data['Age'], bins=age_bins, labels=age_labels, right=False)

        # Count by age group and gender
        pyramid_data = self.data.groupby(['age_group', 'Gender']).size().unstack(fill_value=0)

        return {
            'age_groups': age_labels,
            'male': pyramid_data.get('M', pd.Series(0, index=pyramid_data.index)).tolist(),
            'female': pyramid_data.get('F', pd.Series(0, index=pyramid_data.index)).tolist()
        }

    def get_electoral_insights(self) -> Dict:
        """Get electoral strategy insights"""
        insights = {
            'first_time_voters': self._get_first_time_voters(),
            'senior_voters': self._get_senior_voters(),
            'vote_banks': self._identify_vote_banks(),
            'swing_demographics': self._identify_swing_demographics()
        }
        return insights

    def _get_first_time_voters(self) -> Dict:
        """Identify first-time voters (18-21)"""
        if 'Age' not in self.data.columns:
            return {'error': 'Age data not available'}

        first_timers = self.data[(self.data['Age'] >= 18) & (self.data['Age'] <= 21)]

        return {
            'count': len(first_timers),
            'percentage': round(len(first_timers) / self.total_voters * 100, 2),
            'gender_split': first_timers['Gender'].value_counts().to_dict() if 'Gender' in first_timers.columns else {},
            'religion_split': first_timers['religion'].value_counts().to_dict() if 'religion' in first_timers.columns else {}
        }

    def _get_senior_voters(self) -> Dict:
        """Identify senior voters (65+)"""
        if 'Age' not in self.data.columns:
            return {'error': 'Age data not available'}

        seniors = self.data[self.data['Age'] >= 65]

        return {
            'count': len(seniors),
            'percentage': round(len(seniors) / self.total_voters * 100, 2),
            'gender_split': seniors['Gender'].value_counts().to_dict() if 'Gender' in seniors.columns else {},
            'religion_split': seniors['religion'].value_counts().to_dict() if 'religion' in seniors.columns else {}
        }

    def _identify_vote_banks(self) -> List[Dict]:
        """Identify potential vote banks"""
        vote_banks = []

        # Religion-based
        if 'religion' in self.data.columns:
            for religion, count in self.data['religion'].value_counts().items():
                if count >= self.total_voters * 0.15:  # At least 15% to be significant
                    vote_banks.append({
                        'type': 'religion',
                        'group': religion,
                        'size': int(count),
                        'percentage': round(count / self.total_voters * 100, 2)
                    })

        # Age-based
        if 'Age' in self.data.columns:
            youth = int(((self.data['Age'] >= 18) & (self.data['Age'] <= 35)).sum())
            if youth >= self.total_voters * 0.25:
                vote_banks.append({
                    'type': 'age',
                    'group': 'Youth (18-35)',
                    'size': int(youth),
                    'percentage': round(youth / self.total_voters * 100, 2)
                })

        return vote_banks

    def _identify_swing_demographics(self) -> Dict:
        """Identify potential swing voter demographics"""
        swing_groups = {}

        # Middle-aged voters often considered swing
        if 'Age' in self.data.columns:
            middle_aged = self.data[(self.data['Age'] >= 35) & (self.data['Age'] <= 55)]
            swing_groups['middle_aged_35_55'] = {
                'count': len(middle_aged),
                'percentage': round(len(middle_aged) / self.total_voters * 100, 2)
            }

        # Religious minorities in diverse areas
        if 'religion' in self.data.columns:
            religion_counts = self.data['religion'].value_counts()
            if len(religion_counts) > 1:
                for religion in religion_counts.index[1:]:  # All except majority
                    if religion_counts[religion] >= self.total_voters * 0.05:  # At least 5%
                        swing_groups[f'minority_{religion.lower()}'] = {
                            'count': int(religion_counts[religion]),
                            'percentage': round(religion_counts[religion] / self.total_voters * 100, 2)
                        }

        return swing_groups