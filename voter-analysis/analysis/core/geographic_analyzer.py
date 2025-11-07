"""
Geographic/Regional Analysis Module
Analyzes house number patterns and geographic clustering
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict
import re


class GeographicAnalyzer:
    """Analyze geographic patterns and regional clustering"""

    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.total_voters = len(data)

    def analyze_house_number_clusters(self) -> Dict:
        """
        Analyze clustering patterns based on house numbers

        Returns:
            Dict with house number cluster analysis
        """
        if 'house_address' not in self.data.columns:
            return {'error': 'Missing house_address column'}

        df = self.data.copy()

        # Extract numeric portions from house addresses
        df['house_number'] = df['house_address'].apply(self._extract_house_number)

        # Remove invalid entries
        df = df[df['house_number'].notna()]

        if len(df) == 0:
            return {'error': 'No valid house numbers found'}

        # Sort by house number
        df_sorted = df.sort_values('house_number')

        # Identify clusters (groups of houses with similar numbers)
        clusters = self._identify_house_clusters(df_sorted)

        result = {
            'total_houses': len(df['house_address'].unique()),
            'houses_with_numbers': len(df),
            'clusters': clusters,
            'cluster_count': len(clusters)
        }

        return result

    def analyze_regional_demographics(self) -> Dict:
        """
        Analyze demographic patterns by house number regions

        Returns:
            Dict with regional demographic breakdown
        """
        if 'house_address' not in self.data.columns or 'religion' not in self.data.columns:
            return {'error': 'Missing required columns'}

        df = self.data.copy()
        df['house_number'] = df['house_address'].apply(self._extract_house_number)
        df = df[df['house_number'].notna()]

        # Define regions based on house number ranges
        regions = self._define_house_number_regions(df)

        result = {'regions': {}}

        for region_name, (start, end) in regions.items():
            region_data = df[(df['house_number'] >= start) & (df['house_number'] <= end)]

            if len(region_data) > 0:
                # Religious composition
                religion_counts = region_data['religion'].value_counts()

                # Gender split
                gender_counts = region_data['Gender'].value_counts() if 'Gender' in region_data.columns else {}

                # Age statistics
                age_stats = {}
                if 'Age' in region_data.columns:
                    age_stats = {
                        'mean': round(region_data['Age'].mean(), 1),
                        'median': round(region_data['Age'].median(), 1)
                    }

                result['regions'][region_name] = {
                    'house_range': f"{int(start)}-{int(end)}",
                    'total_voters': len(region_data),
                    'percentage_of_total': round(len(region_data) / self.total_voters * 100, 1),
                    'religion_breakdown': religion_counts.to_dict(),
                    'dominant_religion': religion_counts.index[0] if len(religion_counts) > 0 else 'Unknown',
                    'dominant_religion_percentage': round(religion_counts.iloc[0] / len(region_data) * 100, 1) if len(religion_counts) > 0 else 0,
                    'gender_split': gender_counts.to_dict(),
                    'age_statistics': age_stats
                }

        return result

    def identify_religious_enclaves(self) -> List[Dict]:
        """
        Identify geographic areas with high religious concentration

        Returns:
            List of religious enclaves
        """
        if 'house_address' not in self.data.columns or 'religion' not in self.data.columns:
            return [{'error': 'Missing required columns'}]

        df = self.data.copy()
        df['house_number'] = df['house_address'].apply(self._extract_house_number)
        df = df[df['house_number'].notna()]

        # Group by house number ranges
        enclaves = []
        window_size = 50  # Analyze in windows of 50 house numbers

        min_house = df['house_number'].min()
        max_house = df['house_number'].max()

        current = min_house
        while current < max_house:
            window_data = df[(df['house_number'] >= current) & (df['house_number'] < current + window_size)]

            if len(window_data) >= 20:  # Minimum 20 voters to be significant
                religion_counts = window_data['religion'].value_counts()

                if len(religion_counts) > 0:
                    dominant = religion_counts.index[0]
                    dominant_count = religion_counts.iloc[0]
                    dominant_pct = round(dominant_count / len(window_data) * 100, 1)

                    # If > 70% of one religion, it's an enclave
                    if dominant_pct >= 70:
                        enclaves.append({
                            'house_range': f"{int(current)}-{int(current + window_size)}",
                            'religion': dominant,
                            'total_voters': len(window_data),
                            'dominant_count': int(dominant_count),
                            'dominance_percentage': dominant_pct,
                            'diversity_index': self._calculate_diversity_index(religion_counts)
                        })

            current += window_size

        # Sort by dominance
        enclaves.sort(key=lambda x: x['dominance_percentage'], reverse=True)

        return enclaves

    def analyze_mixed_areas(self) -> List[Dict]:
        """
        Identify geographic areas with high religious diversity

        Returns:
            List of mixed/diverse areas
        """
        if 'house_address' not in self.data.columns or 'religion' not in self.data.columns:
            return [{'error': 'Missing required columns'}]

        df = self.data.copy()
        df['house_number'] = df['house_address'].apply(self._extract_house_number)
        df = df[df['house_number'].notna()]

        mixed_areas = []
        window_size = 50

        min_house = df['house_number'].min()
        max_house = df['house_number'].max()

        current = min_house
        while current < max_house:
            window_data = df[(df['house_number'] >= current) & (df['house_number'] < current + window_size)]

            if len(window_data) >= 20:
                religion_counts = window_data['religion'].value_counts()

                if len(religion_counts) >= 2:  # At least 2 religions present
                    # Calculate diversity
                    diversity_index = self._calculate_diversity_index(religion_counts)

                    # High diversity if no religion > 60% and diversity index > 0.5
                    max_pct = (religion_counts.iloc[0] / len(window_data)) * 100

                    if max_pct < 60 and diversity_index > 0.5:
                        religion_breakdown = {
                            rel: {
                                'count': int(count),
                                'percentage': round(count / len(window_data) * 100, 1)
                            }
                            for rel, count in religion_counts.items()
                        }

                        mixed_areas.append({
                            'house_range': f"{int(current)}-{int(current + window_size)}",
                            'total_voters': len(window_data),
                            'religions_present': len(religion_counts),
                            'diversity_index': round(diversity_index, 3),
                            'religion_breakdown': religion_breakdown,
                            'strategic_importance': 'HIGH - Swing area with diverse demographics'
                        })

            current += window_size

        # Sort by diversity index
        mixed_areas.sort(key=lambda x: x['diversity_index'], reverse=True)

        return mixed_areas

    def get_geographic_summary(self) -> Dict:
        """
        Generate comprehensive geographic analysis summary

        Returns:
            Dict with all geographic analyses
        """
        return {
            'house_clusters': self.analyze_house_number_clusters(),
            'regional_demographics': self.analyze_regional_demographics(),
            'religious_enclaves': self.identify_religious_enclaves(),
            'mixed_diverse_areas': self.analyze_mixed_areas(),
            'total_voters': self.total_voters
        }

    # Helper methods

    def _extract_house_number(self, address: str) -> float:
        """
        Extract numeric house number from address string

        Args:
            address: House address string (e.g., "039/433", "/769")

        Returns:
            Numeric house number or NaN
        """
        if pd.isna(address):
            return np.nan

        # Remove leading slashes and extract numbers
        match = re.search(r'(\d+)(?:/(\d+))?', str(address))

        if match:
            # If format is "ward/house", use house number (second group)
            # Otherwise use first number found
            if match.group(2):
                return float(match.group(2))
            else:
                return float(match.group(1))

        return np.nan

    def _identify_house_clusters(self, df_sorted: pd.DataFrame) -> List[Dict]:
        """
        Identify clusters of houses with consecutive or nearby numbers

        Args:
            df_sorted: DataFrame sorted by house number

        Returns:
            List of cluster dictionaries
        """
        clusters = []
        current_cluster = []
        cluster_threshold = 10  # Max gap between house numbers in a cluster

        house_groups = df_sorted.groupby('house_address').agg({
            'house_number': 'first',
            'religion': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Unknown'
        }).reset_index()

        house_groups = house_groups.sort_values('house_number')

        for _, row in house_groups.iterrows():
            if not current_cluster:
                current_cluster.append(row)
            else:
                last_house = current_cluster[-1]['house_number']
                current_house = row['house_number']

                if current_house - last_house <= cluster_threshold:
                    current_cluster.append(row)
                else:
                    # Save current cluster if significant
                    if len(current_cluster) >= 3:
                        clusters.append(self._summarize_cluster(current_cluster, df_sorted))
                    current_cluster = [row]

        # Don't forget last cluster
        if len(current_cluster) >= 3:
            clusters.append(self._summarize_cluster(current_cluster, df_sorted))

        return clusters

    def _summarize_cluster(self, cluster_houses: List, full_data: pd.DataFrame) -> Dict:
        """
        Summarize a house cluster

        Args:
            cluster_houses: List of house data in cluster
            full_data: Full dataset

        Returns:
            Cluster summary dictionary
        """
        house_numbers = [h['house_number'] for h in cluster_houses]
        min_house = min(house_numbers)
        max_house = max(house_numbers)

        # Get all voters in this cluster
        cluster_voters = full_data[
            (full_data['house_number'] >= min_house) &
            (full_data['house_number'] <= max_house)
        ]

        religion_counts = cluster_voters['religion'].value_counts() if 'religion' in cluster_voters.columns else pd.Series()

        return {
            'house_range': f"{int(min_house)}-{int(max_house)}",
            'house_count': len(cluster_houses),
            'total_voters': len(cluster_voters),
            'dominant_religion': religion_counts.index[0] if len(religion_counts) > 0 else 'Unknown',
            'religion_diversity': len(religion_counts)
        }

    def _define_house_number_regions(self, df: pd.DataFrame) -> Dict[str, Tuple[float, float]]:
        """
        Define house number regions (Low, Mid, High)

        Args:
            df: DataFrame with house_number column

        Returns:
            Dict mapping region names to (start, end) tuples
        """
        min_house = df['house_number'].min()
        max_house = df['house_number'].max()
        range_size = (max_house - min_house) / 3

        return {
            'Low Numbers': (min_house, min_house + range_size),
            'Mid Numbers': (min_house + range_size, min_house + 2 * range_size),
            'High Numbers': (min_house + 2 * range_size, max_house)
        }

    def _calculate_diversity_index(self, counts: pd.Series) -> float:
        """
        Calculate Simpson's Diversity Index

        Args:
            counts: Series of counts

        Returns:
            Diversity index (0-1, higher = more diverse)
        """
        total = counts.sum()
        if total == 0:
            return 0

        # Simpson's D = 1 - sum(p_i^2)
        proportions = counts / total
        return 1 - (proportions ** 2).sum()


def test_geographic_analysis():
    """Test geographic analysis with sample data"""
    sample_file = '/Users/nikzart/Developer/aislop-server/output_with_religion/041_-_BHARANIKKAVU/003_-_Bhaskaranunni_Library_Building_Vanjikovil.csv'

    try:
        df = pd.read_csv(sample_file)

        # Parse Age and Gender
        if 'Gender / Age' in df.columns:
            df[['Gender', 'Age']] = df['Gender / Age'].str.split(' / ', expand=True)
            df['Age'] = pd.to_numeric(df['Age'], errors='coerce')

        # Create house_address column
        if 'OldWard No/ House No.' in df.columns:
            df['house_address'] = df['OldWard No/ House No.']

        analyzer = GeographicAnalyzer(df)

        print("=" * 60)
        print("GEOGRAPHIC ANALYSIS TEST")
        print("=" * 60)

        # Test regional demographics
        print("\n1. Regional Demographics:")
        regional = analyzer.analyze_regional_demographics()
        if 'regions' in regional:
            for region, data in regional['regions'].items():
                print(f"  {region} ({data['house_range']}): {data['total_voters']} voters, {data['dominant_religion']} dominant ({data['dominant_religion_percentage']}%)")

        # Test religious enclaves
        print("\n2. Religious Enclaves:")
        enclaves = analyzer.identify_religious_enclaves()
        for i, enclave in enumerate(enclaves[:3], 1):
            if 'error' not in enclave:
                print(f"  {i}. Houses {enclave['house_range']}: {enclave['religion']} {enclave['dominance_percentage']}% ({enclave['total_voters']} voters)")

        # Test mixed areas
        print("\n3. Mixed/Diverse Areas:")
        mixed = analyzer.analyze_mixed_areas()
        for i, area in enumerate(mixed[:3], 1):
            if 'error' not in area:
                print(f"  {i}. Houses {area['house_range']}: {area['religions_present']} religions, diversity {area['diversity_index']}")

        print("\n✓ Geographic analysis test completed")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_geographic_analysis()
