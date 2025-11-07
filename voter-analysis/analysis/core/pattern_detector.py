"""
Pattern Detection and Anomaly Analysis Module
Identifies unusual patterns, outliers, and anomalies in voter data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import Counter


class PatternDetector:
    """Detect patterns and anomalies in voter demographics"""

    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.total_voters = len(data)

    def detect_age_anomalies(self) -> List[Dict]:
        """
        Detect unusual age patterns and outliers

        Returns:
            List of age-related anomalies
        """
        if 'Age' not in self.data.columns:
            return [{'error': 'Missing Age column'}]

        anomalies = []

        # Calculate age statistics
        mean_age = self.data['Age'].mean()
        std_age = self.data['Age'].std()
        median_age = self.data['Age'].median()

        # Check for high variance
        if std_age > 20:
            anomalies.append({
                'type': 'high_variance',
                'category': 'age',
                'description': f'Unusually high age variance ({std_age:.1f} years)',
                'severity': 'medium',
                'implication': 'Diverse age groups require multi-generational outreach strategies'
            })

        # Check for age gaps
        age_distribution = self.data['Age'].value_counts().sort_index()
        for age in range(20, 70, 10):
            age_range = self.data[(self.data['Age'] >= age) & (self.data['Age'] < age + 10)]
            if len(age_range) < self.total_voters * 0.05:  # Less than 5%
                anomalies.append({
                    'type': 'age_gap',
                    'category': 'age',
                    'description': f'Underrepresented age group: {age}-{age+10} years ({len(age_range)} voters)',
                    'severity': 'low',
                    'implication': 'Potential voter registration gap or demographic shift'
                })

        # Check for unusually high concentration
        for age_group in [(18, 25), (25, 35), (35, 50), (50, 65), (65, 100)]:
            group_data = self.data[(self.data['Age'] >= age_group[0]) & (self.data['Age'] < age_group[1])]
            percentage = len(group_data) / self.total_voters * 100

            if percentage > 35:  # More than 35% in one age group
                anomalies.append({
                    'type': 'age_concentration',
                    'category': 'age',
                    'description': f'High concentration in {age_group[0]}-{age_group[1]} age group: {len(group_data)} voters ({percentage:.1f}%)',
                    'severity': 'high',
                    'implication': 'Age-specific messaging will be highly effective'
                })

        return anomalies

    def detect_household_anomalies(self) -> List[Dict]:
        """
        Detect unusual household patterns

        Returns:
            List of household anomalies
        """
        if 'household_id' not in self.data.columns:
            return [{'error': 'Missing household_id column'}]

        anomalies = []

        # Group by household
        household_sizes = self.data.groupby('household_id').size()

        # Very large households (10+ voters)
        very_large = household_sizes[household_sizes >= 10]
        if len(very_large) > 0:
            for household_id, size in very_large.items():
                # Extract house address and house name from household_id
                household_data = self.data[self.data['household_id'] == household_id]
                house_address = household_data['house_address'].iloc[0] if len(household_data) > 0 else 'Unknown'
                if 'House Name' in household_data.columns:
                    house_name = household_data['House Name'].mode()[0] if len(household_data['House Name'].mode()) > 0 else 'N/A'
                    display_address = f"{house_address} ({house_name})"
                else:
                    display_address = house_address

                anomalies.append({
                    'type': 'very_large_household',
                    'category': 'household',
                    'description': f'Exceptionally large household at {display_address}: {size} voters',
                    'severity': 'high',
                    'implication': 'High-value target - winning this household = multiple votes'
                })

        # Check for single-voter dominance
        single_voter_households = len(household_sizes[household_sizes == 1])
        single_voter_pct = single_voter_households / len(household_sizes) * 100

        if single_voter_pct > 40:
            anomalies.append({
                'type': 'high_single_voters',
                'category': 'household',
                'description': f'High proportion of single-voter households: {single_voter_households} ({single_voter_pct:.1f}%)',
                'severity': 'medium',
                'implication': 'Individual-focused rather than family-based outreach needed'
            })

        return anomalies

    def detect_religious_patterns(self) -> List[Dict]:
        """
        Detect unusual religious demographic patterns

        Returns:
            List of religious pattern insights
        """
        if 'religion' not in self.data.columns:
            return [{'error': 'Missing religion column'}]

        patterns = []

        religion_counts = self.data['religion'].value_counts()
        total = religion_counts.sum()

        # Check for extreme dominance (>85%)
        if religion_counts.iloc[0] / total > 0.85:
            patterns.append({
                'type': 'extreme_dominance',
                'category': 'religion',
                'description': f'{religion_counts.index[0]} extreme dominance: {religion_counts.iloc[0]} voters ({religion_counts.iloc[0]/total*100:.1f}%)',
                'severity': 'high',
                'implication': 'Consolidation strategy viable - focus on turnout over persuasion'
            })

        # Check for balanced competition (<40% max)
        if religion_counts.iloc[0] / total < 0.40:
            patterns.append({
                'type': 'balanced_competition',
                'category': 'religion',
                'description': f'No religious majority - top group {religion_counts.index[0]} at only {religion_counts.iloc[0]/total*100:.1f}%',
                'severity': 'high',
                'implication': 'Coalition-building essential - swing voters critical'
            })

        # Check for three-way split
        if len(religion_counts) >= 3:
            top_three_pct = religion_counts.iloc[:3].sum() / total
            if top_three_pct > 0.95 and all(religion_counts.iloc[i] / total > 0.20 for i in range(3)):
                patterns.append({
                    'type': 'three_way_split',
                    'category': 'religion',
                    'description': f'Three-way religious split: {religion_counts.iloc[:3].to_dict()}',
                    'severity': 'high',
                    'implication': 'Complex dynamics - requires nuanced multi-community strategy'
                })

        return patterns

    def detect_mixed_faith_households(self) -> List[Dict]:
        """
        Identify households with multiple religions (rare but significant)

        Returns:
            List of mixed-faith household patterns
        """
        if 'household_id' not in self.data.columns or 'religion' not in self.data.columns:
            return [{'error': 'Missing required columns'}]

        mixed_households = []

        for household_id, group in self.data.groupby('household_id'):
            if len(group) >= 2:  # At least 2 voters
                religions = group['religion'].unique()

                if len(religions) > 1:  # Multiple religions in same household
                    religion_breakdown = group['religion'].value_counts().to_dict()

                    # Extract house address and house name for display
                    house_address = group['house_address'].iloc[0] if len(group) > 0 else 'Unknown'
                    if 'House Name' in group.columns:
                        house_name = group['House Name'].mode()[0] if len(group['House Name'].mode()) > 0 else 'N/A'
                        display_address = f"{house_address} ({house_name})"
                    else:
                        display_address = house_address

                    mixed_households.append({
                        'type': 'mixed_faith_household',
                        'category': 'household_religion',
                        'house_address': display_address,
                        'total_voters': len(group),
                        'religions': list(religions),
                        'breakdown': religion_breakdown,
                        'description': f'Mixed-faith household at {display_address}: {len(group)} voters, {len(religions)} religions',
                        'severity': 'medium',
                        'implication': 'Potential swing household - requires inclusive messaging'
                    })

        # Summarize if many mixed households
        if len(mixed_households) > 0:
            summary = {
                'type': 'mixed_faith_summary',
                'category': 'pattern',
                'description': f'Found {len(mixed_households)} mixed-faith households ({len(mixed_households)/len(self.data.groupby("household_id"))*100:.1f}% of all households)',
                'severity': 'high' if len(mixed_households) > 10 else 'medium',
                'implication': 'Significant interfaith mixing indicates openness to cross-community appeal',
                'details': mixed_households[:10]  # Include top 10
            }
            return [summary]

        return []

    def detect_gender_imbalances(self) -> List[Dict]:
        """
        Detect unusual gender patterns

        Returns:
            List of gender-related anomalies
        """
        if 'Gender' not in self.data.columns:
            return [{'error': 'Missing Gender column'}]

        anomalies = []

        gender_counts = self.data['Gender'].value_counts()

        if 'M' in gender_counts and 'F' in gender_counts:
            male_count = gender_counts['M']
            female_count = gender_counts['F']
            total = male_count + female_count

            male_pct = male_count / total * 100
            female_pct = female_count / total * 100

            # Check for extreme imbalance (>60%)
            if max(male_pct, female_pct) > 60:
                dominant = 'Female' if female_pct > male_pct else 'Male'
                anomalies.append({
                    'type': 'gender_imbalance',
                    'category': 'gender',
                    'description': f'Significant gender imbalance: {dominant} voters are {max(male_pct, female_pct):.1f}% of electorate',
                    'severity': 'high',
                    'implication': f'Gender-specific messaging and outreach critical - focus on {dominant.lower()} voters'
                })

            # Check by age group for gender imbalances
            if 'Age' in self.data.columns:
                for age_range in [(18, 35), (35, 50), (50, 100)]:
                    age_data = self.data[(self.data['Age'] >= age_range[0]) & (self.data['Age'] < age_range[1])]
                    if len(age_data) > 50:
                        age_gender = age_data['Gender'].value_counts()
                        if 'M' in age_gender and 'F' in age_gender:
                            age_male_pct = age_gender['M'] / len(age_data) * 100
                            age_female_pct = age_gender['F'] / len(age_data) * 100

                            if abs(age_male_pct - age_female_pct) > 20:
                                anomalies.append({
                                    'type': 'age_gender_imbalance',
                                    'category': 'gender',
                                    'description': f'Gender imbalance in {age_range[0]}-{age_range[1]} age group: {age_male_pct:.1f}% M vs {age_female_pct:.1f}% F',
                                    'severity': 'medium',
                                    'implication': 'Age-specific gender targeting needed'
                                })

        return anomalies

    def detect_age_religion_correlations(self) -> List[Dict]:
        """
        Detect patterns where certain religions have notably different age profiles

        Returns:
            List of age-religion correlation patterns
        """
        if 'Age' not in self.data.columns or 'religion' not in self.data.columns:
            return [{'error': 'Missing required columns'}]

        patterns = []

        overall_mean_age = self.data['Age'].mean()

        for religion in self.data['religion'].unique():
            religion_data = self.data[self.data['religion'] == religion]

            if len(religion_data) >= 20:  # Minimum sample size
                religion_mean_age = religion_data['Age'].mean()
                age_diff = religion_mean_age - overall_mean_age

                # Significant difference (>5 years)
                if abs(age_diff) > 5:
                    patterns.append({
                        'type': 'age_religion_correlation',
                        'category': 'cross_demographic',
                        'religion': religion,
                        'mean_age': round(religion_mean_age, 1),
                        'overall_mean': round(overall_mean_age, 1),
                        'difference': round(age_diff, 1),
                        'description': f'{religion} voters are {"younger" if age_diff < 0 else "older"} than average (mean age {religion_mean_age:.1f} vs {overall_mean_age:.1f})',
                        'severity': 'medium',
                        'implication': f'Generational messaging for {religion} voters should be adjusted'
                    })

        return patterns

    def get_all_anomalies_and_patterns(self) -> Dict:
        """
        Run all pattern detection and anomaly analysis

        Returns:
            Dict with all detected patterns and anomalies
        """
        return {
            'age_anomalies': self.detect_age_anomalies(),
            'household_anomalies': self.detect_household_anomalies(),
            'religious_patterns': self.detect_religious_patterns(),
            'mixed_faith_households': self.detect_mixed_faith_households(),
            'gender_imbalances': self.detect_gender_imbalances(),
            'age_religion_correlations': self.detect_age_religion_correlations(),
            'summary': self._generate_summary()
        }

    def _generate_summary(self) -> Dict:
        """Generate summary of all detected patterns"""
        all_patterns = []

        all_patterns.extend(self.detect_age_anomalies())
        all_patterns.extend(self.detect_household_anomalies())
        all_patterns.extend(self.detect_religious_patterns())
        all_patterns.extend(self.detect_mixed_faith_households())
        all_patterns.extend(self.detect_gender_imbalances())
        all_patterns.extend(self.detect_age_religion_correlations())

        # Filter out errors
        valid_patterns = [p for p in all_patterns if 'error' not in p]

        # Count by severity
        high_severity = len([p for p in valid_patterns if p.get('severity') == 'high'])
        medium_severity = len([p for p in valid_patterns if p.get('severity') == 'medium'])
        low_severity = len([p for p in valid_patterns if p.get('severity') == 'low'])

        return {
            'total_patterns_detected': len(valid_patterns),
            'high_severity': high_severity,
            'medium_severity': medium_severity,
            'low_severity': low_severity,
            'top_5_critical': sorted(valid_patterns, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}.get(x.get('severity'), 0), reverse=True)[:5]
        }


def test_pattern_detection():
    """Test pattern detection with sample data"""
    sample_file = '/Users/nikzart/Developer/aislop-server/output_with_religion/041_-_BHARANIKKAVU/003_-_Bhaskaranunni_Library_Building_Vanjikovil.csv'

    try:
        df = pd.read_csv(sample_file)

        # Parse data
        if 'Gender / Age' in df.columns:
            df[['Gender', 'Age']] = df['Gender / Age'].str.split(' / ', expand=True)
            df['Age'] = pd.to_numeric(df['Age'], errors='coerce')

        if 'OldWard No/ House No.' in df.columns:
            df['house_address'] = df['OldWard No/ House No.']

        detector = PatternDetector(df)

        print("=" * 60)
        print("PATTERN DETECTION & ANOMALY ANALYSIS TEST")
        print("=" * 60)

        # Get all patterns
        all_results = detector.get_all_anomalies_and_patterns()

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        summary = all_results['summary']
        print(f"Total patterns detected: {summary['total_patterns_detected']}")
        print(f"  High severity: {summary['high_severity']}")
        print(f"  Medium severity: {summary['medium_severity']}")
        print(f"  Low severity: {summary['low_severity']}")

        print("\n" + "=" * 60)
        print("TOP 5 CRITICAL PATTERNS")
        print("=" * 60)
        for i, pattern in enumerate(summary['top_5_critical'], 1):
            print(f"\n{i}. [{pattern.get('severity', 'N/A').upper()}] {pattern.get('description', 'N/A')}")
            print(f"   Implication: {pattern.get('implication', 'N/A')}")

        print("\n✓ Pattern detection test completed")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_pattern_detection()
