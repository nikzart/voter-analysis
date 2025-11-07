"""
Cross-Demographic Analysis Module
Analyzes intersections of age, religion, and gender
"""

import pandas as pd
from typing import Dict, List, Tuple
import numpy as np


class CrossDemographicAnalyzer:
    """Analyze cross-demographic patterns (age × religion × gender)"""

    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.total_voters = len(data)

    def analyze_religion_by_age(self) -> Dict:
        """
        Analyze religious composition across age groups

        Returns:
            Dict with religion-age cross-tabulation
        """
        if 'religion' not in self.data.columns or 'Age' not in self.data.columns:
            return {'error': 'Missing required columns'}

        # Define age groups
        age_bins = [18, 25, 35, 45, 55, 65, 100]
        age_labels = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+']

        df = self.data.copy()
        df['age_group'] = pd.cut(df['Age'], bins=age_bins, labels=age_labels, right=False)

        # Cross-tabulation
        cross_tab = pd.crosstab(df['religion'], df['age_group'], margins=True)

        # Convert to percentages
        cross_tab_pct = pd.crosstab(df['religion'], df['age_group'], normalize='columns') * 100

        result = {
            'absolute_counts': cross_tab.to_dict(),
            'percentage_of_age_group': cross_tab_pct.round(1).to_dict(),
            'insights': []
        }

        # Generate insights
        for religion in cross_tab.index[:-1]:  # Exclude 'All' row
            for age_group in cross_tab.columns[:-1]:  # Exclude 'All' column
                count = cross_tab.loc[religion, age_group]
                pct = cross_tab_pct.loc[religion, age_group] if age_group in cross_tab_pct.columns else 0

                if count > 100 and pct > 40:  # Significant concentration
                    result['insights'].append({
                        'type': 'concentration',
                        'religion': religion,
                        'age_group': age_group,
                        'count': int(count),
                        'percentage': round(float(pct), 1),
                        'description': f"{religion} voters dominate {age_group} age group ({pct:.1f}%)"
                    })

        return result

    def analyze_gender_by_religion(self) -> Dict:
        """
        Analyze gender distribution within each religion

        Returns:
            Dict with gender-religion cross-tabulation
        """
        if 'religion' not in self.data.columns or 'Gender' not in self.data.columns:
            return {'error': 'Missing required columns'}

        df = self.data.copy()

        # Cross-tabulation
        cross_tab = pd.crosstab(df['religion'], df['Gender'], margins=True)

        # Calculate percentages within each religion
        cross_tab_pct = pd.crosstab(df['religion'], df['Gender'], normalize='index') * 100

        result = {
            'absolute_counts': cross_tab.to_dict(),
            'percentage_within_religion': cross_tab_pct.round(1).to_dict(),
            'gender_gaps': {}
        }

        # Calculate gender gaps within each religion
        for religion in cross_tab.index[:-1]:
            if 'M' in cross_tab.columns and 'F' in cross_tab.columns:
                male_count = cross_tab.loc[religion, 'M']
                female_count = cross_tab.loc[religion, 'F']
                gap = female_count - male_count
                gap_pct = (gap / (male_count + female_count)) * 100 if (male_count + female_count) > 0 else 0

                result['gender_gaps'][religion] = {
                    'male': int(male_count),
                    'female': int(female_count),
                    'gap': int(gap),
                    'gap_percentage': round(float(gap_pct), 1),
                    'female_majority': gap > 0
                }

        return result

    def analyze_age_gender_by_religion(self) -> Dict:
        """
        Three-way analysis: age × gender × religion

        Returns:
            Dict with 3-way demographic breakdown
        """
        if 'religion' not in self.data.columns or 'Age' not in self.data.columns or 'Gender' not in self.data.columns:
            return {'error': 'Missing required columns'}

        # Define age groups
        age_bins = [18, 30, 45, 60, 100]
        age_labels = ['Young (18-29)', 'Middle (30-44)', 'Senior (45-59)', 'Elderly (60+)']

        df = self.data.copy()
        df['age_group'] = pd.cut(df['Age'], bins=age_bins, labels=age_labels, right=False)

        result = {'breakdown': {}}

        for religion in df['religion'].unique():
            religion_data = df[df['religion'] == religion]
            religion_result = {'total': len(religion_data), 'segments': {}}

            for age_group in age_labels:
                age_data = religion_data[religion_data['age_group'] == age_group]

                for gender in ['M', 'F']:
                    segment_data = age_data[age_data['Gender'] == gender]
                    count = len(segment_data)

                    if count > 0:
                        segment_key = f"{age_group} - {'Male' if gender == 'M' else 'Female'}"
                        religion_result['segments'][segment_key] = {
                            'count': count,
                            'percentage_of_religion': round(count / len(religion_data) * 100, 1),
                            'percentage_of_total': round(count / self.total_voters * 100, 1)
                        }

            result['breakdown'][religion] = religion_result

        # Identify strategic segments (top 10)
        all_segments = []
        for religion, rel_data in result['breakdown'].items():
            for segment, seg_data in rel_data['segments'].items():
                all_segments.append({
                    'religion': religion,
                    'segment': segment,
                    'count': seg_data['count'],
                    'percentage': seg_data['percentage_of_total']
                })

        result['top_strategic_segments'] = sorted(
            all_segments,
            key=lambda x: x['count'],
            reverse=True
        )[:10]

        return result

    def identify_demographic_clusters(self) -> List[Dict]:
        """
        Identify significant demographic clusters

        Returns:
            List of notable demographic clusters
        """
        if 'religion' not in self.data.columns or 'Age' not in self.data.columns or 'Gender' not in self.data.columns:
            return [{'error': 'Missing required columns'}]

        age_bins = [18, 35, 50, 65, 100]
        age_labels = ['Youth', 'Young Adults', 'Middle Age', 'Senior']

        df = self.data.copy()
        df['age_category'] = pd.cut(df['Age'], bins=age_bins, labels=age_labels, right=False)

        clusters = []

        # Analyze each combination
        for religion in df['religion'].unique():
            for age_cat in age_labels:
                for gender in ['M', 'F']:
                    segment = df[
                        (df['religion'] == religion) &
                        (df['age_category'] == age_cat) &
                        (df['Gender'] == gender)
                    ]

                    count = len(segment)
                    percentage = round(count / self.total_voters * 100, 2)

                    # Include if significant (>2% of electorate or >100 voters)
                    if count > 100 or percentage > 2:
                        avg_age = round(segment['Age'].mean(), 1) if len(segment) > 0 else 0

                        clusters.append({
                            'religion': religion,
                            'age_category': age_cat,
                            'gender': 'Male' if gender == 'M' else 'Female',
                            'count': count,
                            'percentage_of_electorate': percentage,
                            'average_age': avg_age,
                            'label': f"{religion} {age_cat} {'Men' if gender == 'M' else 'Women'}",
                            'strategic_value': self._calculate_strategic_value(count, percentage, age_cat)
                        })

        # Sort by strategic value
        clusters.sort(key=lambda x: x['strategic_value'], reverse=True)

        return clusters

    def _calculate_strategic_value(self, count: int, percentage: float, age_category: str) -> float:
        """
        Calculate strategic value score for a demographic cluster

        Args:
            count: Number of voters
            percentage: Percentage of electorate
            age_category: Age category

        Returns:
            Strategic value score (0-100)
        """
        # Base score from size
        size_score = min(percentage * 5, 50)  # Max 50 points

        # Bonus for young/middle-aged (more persuadable)
        age_bonus = 0
        if age_category in ['Young Adults', 'Middle Age']:
            age_bonus = 20
        elif age_category == 'Youth':
            age_bonus = 15

        # Bonus for absolute numbers
        count_bonus = min(count / 100, 20)  # Max 20 points

        return size_score + age_bonus + count_bonus

    def generate_cross_demographic_summary(self) -> Dict:
        """
        Generate comprehensive cross-demographic summary

        Returns:
            Dict with all cross-demographic analyses
        """
        return {
            'religion_by_age': self.analyze_religion_by_age(),
            'gender_by_religion': self.analyze_gender_by_religion(),
            'three_way_breakdown': self.analyze_age_gender_by_religion(),
            'demographic_clusters': self.identify_demographic_clusters(),
            'total_voters': self.total_voters
        }

    def get_formatted_clusters_table(self, top_n: int = 10) -> pd.DataFrame:
        """
        Get formatted table of top demographic clusters

        Args:
            top_n: Number of top clusters to return

        Returns:
            DataFrame with formatted cluster data
        """
        clusters = self.identify_demographic_clusters()[:top_n]

        df = pd.DataFrame(clusters)

        if not df.empty:
            df = df[['label', 'count', 'percentage_of_electorate', 'average_age', 'strategic_value']]
            df.columns = ['Demographic Cluster', 'Voters', '% of Electorate', 'Avg Age', 'Strategic Value']
            df['Voters'] = df['Voters'].apply(lambda x: f"{x:,}")
            df['% of Electorate'] = df['% of Electorate'].apply(lambda x: f"{x}%")
            df['Strategic Value'] = df['Strategic Value'].apply(lambda x: f"{x:.1f}")

        return df


def test_cross_demographics():
    """Test cross-demographic analysis with sample data"""
    # Load sample data
    sample_file = '/Users/nikzart/Developer/aislop-server/output_with_religion/041_-_BHARANIKKAVU/003_-_Bhaskaranunni_Library_Building_Vanjikovil.csv'

    try:
        df = pd.read_csv(sample_file)

        # Parse Age from "Gender / Age" column
        if 'Gender / Age' in df.columns:
            df[['Gender', 'Age']] = df['Gender / Age'].str.split(' / ', expand=True)
            df['Age'] = pd.to_numeric(df['Age'], errors='coerce')

        analyzer = CrossDemographicAnalyzer(df)

        print("=" * 60)
        print("CROSS-DEMOGRAPHIC ANALYSIS TEST")
        print("=" * 60)

        # Test religion by age
        print("\n1. Religion by Age Analysis:")
        rel_age = analyzer.analyze_religion_by_age()
        if 'insights' in rel_age:
            for insight in rel_age['insights'][:3]:
                print(f"  - {insight['description']}")

        # Test gender by religion
        print("\n2. Gender by Religion:")
        gender_rel = analyzer.analyze_gender_by_religion()
        if 'gender_gaps' in gender_rel:
            for religion, gap_info in gender_rel['gender_gaps'].items():
                print(f"  - {religion}: {gap_info['female']} F vs {gap_info['male']} M (Gap: {gap_info['gap']:+d})")

        # Test demographic clusters
        print("\n3. Top 5 Demographic Clusters:")
        clusters = analyzer.identify_demographic_clusters()[:5]
        for i, cluster in enumerate(clusters, 1):
            print(f"  {i}. {cluster['label']}: {cluster['count']} voters ({cluster['percentage_of_electorate']}%)")

        print("\n✓ Cross-demographic analysis test completed")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_cross_demographics()
