"""
Family Structure Analysis Module for Kerala Voter Data
Analyzes household patterns, family relationships, and guardian networks
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict
import re

class FamilyAnalyzer:
    """Analyze family structures and household patterns"""

    def __init__(self, data: pd.DataFrame):
        self.data = data
        self._preprocess_data()
        self.families = self._identify_families()

    def _preprocess_data(self):
        """Preprocess data for family analysis"""
        # Extract age from Gender/Age if needed
        if 'Gender / Age' in self.data.columns and 'Age' not in self.data.columns:
            self.data[['Gender', 'Age']] = self.data['Gender / Age'].str.extract(r'([MF])\s*/\s*(\d+)')
            self.data['Age'] = pd.to_numeric(self.data['Age'], errors='coerce')

        # Create family identifier (combination of house and guardian)
        if 'House Name' in self.data.columns:
            self.data['house_id'] = self.data['House Name'].fillna('Unknown')

    def _identify_families(self) -> Dict:
        """Identify family units based on house and guardian relationships"""
        families = {}

        if 'House Name' not in self.data.columns:
            return families

        # Group by house name
        for house, house_data in self.data.groupby('House Name'):
            if pd.isna(house) or house == 'Unknown':
                continue

            # Within each house, identify family units by guardian patterns
            guardians = house_data["Guardian's Name"].value_counts() if "Guardian's Name" in house_data.columns else pd.Series()

            # If small house (<=5 members), likely single family
            if len(house_data) <= 5:
                families[f"{house}_family_1"] = {
                    'house': house,
                    'members': house_data.index.tolist(),
                    'size': len(house_data),
                    'type': 'nuclear' if len(house_data) <= 4 else 'joint'
                }
            else:
                # Larger house, may have multiple families
                # Group by common guardians
                family_clusters = self._cluster_by_guardians(house_data)
                for idx, cluster in enumerate(family_clusters):
                    families[f"{house}_family_{idx+1}"] = {
                        'house': house,
                        'members': cluster,
                        'size': len(cluster),
                        'type': self._determine_family_type(house_data.loc[cluster])
                    }

        return families

    def _cluster_by_guardians(self, house_data: pd.DataFrame) -> List[List]:
        """Cluster house members into family units based on guardians"""
        if "Guardian's Name" not in house_data.columns:
            return [house_data.index.tolist()]

        clusters = []
        guardian_groups = defaultdict(list)

        for idx, row in house_data.iterrows():
            guardian = row["Guardian's Name"]
            if pd.notna(guardian):
                guardian_groups[guardian].append(idx)

        # Merge clusters with common members
        for guardian, members in guardian_groups.items():
            # Check if guardian is also a member
            guardian_as_member = house_data[house_data['Name'] == guardian]
            if not guardian_as_member.empty:
                members.extend(guardian_as_member.index.tolist())

            clusters.append(list(set(members)))

        # If no clear clusters, treat as single family
        if not clusters:
            clusters = [house_data.index.tolist()]

        return clusters

    def _determine_family_type(self, family_data: pd.DataFrame) -> str:
        """Determine family type based on composition"""
        size = len(family_data)

        if size == 1:
            return 'single'
        elif size <= 4:
            return 'nuclear'
        elif size <= 6:
            return 'joint'
        else:
            return 'extended'

    def get_family_statistics(self) -> Dict:
        """Get comprehensive family structure statistics"""
        stats = {
            'household_analysis': self._analyze_households(),
            'family_structures': self._analyze_family_structures(),
            'guardian_patterns': self._analyze_guardian_patterns(),
            'generational_analysis': self._analyze_generations(),
            'inter_religious_families': self._find_inter_religious_families()
        }
        return stats

    def _analyze_households(self) -> Dict:
        """Analyze household patterns"""
        if 'House Name' not in self.data.columns:
            return {'error': 'House data not available'}

        house_sizes = self.data.groupby('House Name').size()

        # Calculate statistics
        size_distribution = {
            'single_person': int((house_sizes == 1).sum()),
            'couple_2': int((house_sizes == 2).sum()),
            'small_family_3_4': int(((house_sizes >= 3) & (house_sizes <= 4)).sum()),
            'medium_family_5_6': int(((house_sizes >= 5) & (house_sizes <= 6)).sum()),
            'large_family_7_plus': int((house_sizes >= 7).sum())
        }

        # Identify multi-family houses
        multi_family_houses = []
        for house, size in house_sizes.items():
            if size >= 7:  # Likely multi-family
                house_data = self.data[self.data['House Name'] == house]
                unique_guardians = house_data["Guardian's Name"].nunique() if "Guardian's Name" in house_data.columns else 0
                if unique_guardians >= 3:  # Multiple guardians suggest multiple families
                    multi_family_houses.append({
                        'house': house,
                        'total_members': int(size),
                        'unique_guardians': int(unique_guardians)
                    })

        return {
            'total_houses': len(house_sizes),
            'average_household_size': round(house_sizes.mean(), 2),
            'median_household_size': round(house_sizes.median(), 1),
            'largest_household': {
                'name': house_sizes.idxmax() if len(house_sizes) > 0 else None,
                'size': int(house_sizes.max()) if len(house_sizes) > 0 else 0
            },
            'size_distribution': size_distribution,
            'size_percentages': {k: round(v/len(house_sizes)*100, 1) for k, v in size_distribution.items()},
            'multi_family_houses': len(multi_family_houses),
            'multi_family_examples': multi_family_houses[:5]  # Top 5 examples
        }

    def _analyze_family_structures(self) -> Dict:
        """Analyze types of family structures"""
        family_types = Counter()
        family_sizes = []

        for family_id, family_info in self.families.items():
            family_types[family_info['type']] += 1
            family_sizes.append(family_info['size'])

        total_families = len(self.families)

        return {
            'total_families': total_families,
            'average_family_size': round(np.mean(family_sizes), 2) if family_sizes else 0,
            'family_types': dict(family_types),
            'family_type_percentages': {
                k: round(v/total_families*100, 1) for k, v in family_types.items()
            } if total_families > 0 else {},
            'nuclear_families': family_types.get('nuclear', 0),
            'joint_families': family_types.get('joint', 0),
            'extended_families': family_types.get('extended', 0),
            'single_person_households': family_types.get('single', 0)
        }

    def _analyze_guardian_patterns(self) -> Dict:
        """Analyze guardian-dependent relationships"""
        if "Guardian's Name" not in self.data.columns:
            return {'error': 'Guardian data not available'}

        guardian_counts = self.data["Guardian's Name"].value_counts()

        # Identify influential guardians (with multiple dependents)
        influential_guardians = []
        for guardian, count in guardian_counts.head(10).items():
            if pd.notna(guardian) and count > 1:
                dependents = self.data[self.data["Guardian's Name"] == guardian]
                influential_guardians.append({
                    'name': guardian,
                    'dependent_count': int(count),
                    'houses': dependents['House Name'].nunique() if 'House Name' in dependents.columns else 1
                })

        # Gender analysis of guardians (if guardian appears as voter too)
        guardian_genders = {'male': 0, 'female': 0, 'unknown': 0}
        for guardian in guardian_counts.index[:50]:  # Check top 50 guardians
            if pd.notna(guardian):
                guardian_as_voter = self.data[self.data['Name'] == guardian]
                if not guardian_as_voter.empty and 'Gender' in guardian_as_voter.columns:
                    gender = guardian_as_voter.iloc[0]['Gender']
                    if gender == 'M':
                        guardian_genders['male'] += 1
                    elif gender == 'F':
                        guardian_genders['female'] += 1
                    else:
                        guardian_genders['unknown'] += 1
                else:
                    guardian_genders['unknown'] += 1

        return {
            'total_unique_guardians': len(guardian_counts),
            'average_dependents_per_guardian': round(guardian_counts.mean(), 2),
            'max_dependents': {
                'guardian': guardian_counts.index[0] if len(guardian_counts) > 0 else None,
                'count': int(guardian_counts.iloc[0]) if len(guardian_counts) > 0 else 0
            },
            'single_dependent_guardians': int((guardian_counts == 1).sum()),
            'multi_dependent_guardians': int((guardian_counts > 1).sum()),
            'influential_guardians': influential_guardians,
            'guardian_gender_distribution': guardian_genders
        }

    def _analyze_generations(self) -> Dict:
        """Analyze generational patterns within families"""
        if 'Age' not in self.data.columns or 'House Name' not in self.data.columns:
            return {'error': 'Age or House data not available'}

        multi_gen_houses = []
        age_gap_stats = []

        for house, house_data in self.data.groupby('House Name'):
            if len(house_data) < 2:
                continue

            ages = house_data['Age'].dropna()
            if len(ages) < 2:
                continue

            age_range = ages.max() - ages.min()
            age_gap_stats.append(age_range)

            # Multi-generational if age range > 25 years
            if age_range > 25:
                generations = self._identify_generations_in_house(ages)
                multi_gen_houses.append({
                    'house': house,
                    'age_range': int(age_range),
                    'generations': generations,
                    'member_count': len(house_data)
                })

        return {
            'multi_generational_houses': len(multi_gen_houses),
            'multi_gen_percentage': round(len(multi_gen_houses) / self.data['House Name'].nunique() * 100, 1),
            'average_age_gap_in_houses': round(np.mean(age_gap_stats), 1) if age_gap_stats else 0,
            'max_age_gap_in_house': round(max(age_gap_stats), 0) if age_gap_stats else 0,
            'multi_gen_examples': sorted(multi_gen_houses, key=lambda x: x['age_range'], reverse=True)[:5]
        }

    def _identify_generations_in_house(self, ages: pd.Series) -> int:
        """Identify number of generations in a house based on age distribution"""
        age_list = sorted(ages.tolist())
        if not age_list:
            return 1

        generations = 1
        prev_age = age_list[0]

        for age in age_list[1:]:
            if age - prev_age > 20:  # 20+ year gap suggests different generation
                generations += 1
                prev_age = age

        return min(generations, 4)  # Cap at 4 generations

    def _find_inter_religious_families(self) -> Dict:
        """Identify households with multiple religions"""
        if 'religion' not in self.data.columns or 'House Name' not in self.data.columns:
            return {'error': 'Religion or House data not available'}

        inter_religious_houses = []

        for house, house_data in self.data.groupby('House Name'):
            religions = house_data['religion'].value_counts()
            if len(religions) > 1:  # Multiple religions in same house
                inter_religious_houses.append({
                    'house': house,
                    'total_members': len(house_data),
                    'religions': religions.to_dict(),
                    'primary_religion': religions.index[0],
                    'diversity': len(religions)
                })

        return {
            'total_inter_religious_houses': len(inter_religious_houses),
            'percentage_of_houses': round(len(inter_religious_houses) / self.data['House Name'].nunique() * 100, 2),
            'examples': sorted(inter_religious_houses, key=lambda x: x['diversity'], reverse=True)[:10],
            'integration_index': self._calculate_integration_index(inter_religious_houses)
        }

    def _calculate_integration_index(self, inter_religious_houses: List) -> float:
        """Calculate social integration index based on inter-religious households"""
        if not inter_religious_houses:
            return 0.0

        total_houses = self.data['House Name'].nunique()
        integration_score = len(inter_religious_houses) / total_houses

        # Weight by diversity (more religions = higher integration)
        diversity_weight = sum(h['diversity'] for h in inter_religious_houses) / (len(inter_religious_houses) * 3)

        return round(integration_score * diversity_weight * 100, 2)

    def get_kinship_networks(self) -> Dict:
        """Analyze kinship and family networks"""
        if 'Name' not in self.data.columns or "Guardian's Name" not in self.data.columns:
            return {'error': 'Name or Guardian data not available'}

        # Find potential siblings (same guardian, similar age)
        siblings = []
        for guardian, group in self.data.groupby("Guardian's Name"):
            if pd.isna(guardian) or len(group) < 2:
                continue

            if 'Age' in group.columns:
                ages = group['Age'].dropna()
                if len(ages) >= 2:
                    age_diff = ages.max() - ages.min()
                    if age_diff <= 15:  # Likely siblings if age difference <= 15
                        siblings.append({
                            'guardian': guardian,
                            'potential_siblings': group['Name'].tolist(),
                            'count': len(group),
                            'age_range': int(age_diff)
                        })

        # Find potential parent-child relationships
        parent_child = []
        for idx, row in self.data.iterrows():
            if pd.notna(row.get("Guardian's Name")):
                # Check if guardian exists as a voter
                guardian_as_voter = self.data[self.data['Name'] == row["Guardian's Name"]]
                if not guardian_as_voter.empty:
                    if 'Age' in self.data.columns:
                        child_age = row.get('Age')
                        parent_age = guardian_as_voter.iloc[0].get('Age')
                        if pd.notna(child_age) and pd.notna(parent_age):
                            age_diff = parent_age - child_age
                            if 18 <= age_diff <= 60:  # Reasonable parent-child age gap
                                parent_child.append({
                                    'parent': row["Guardian's Name"],
                                    'child': row['Name'],
                                    'age_difference': int(age_diff)
                                })

        return {
            'potential_sibling_groups': len(siblings),
            'largest_sibling_group': max(siblings, key=lambda x: x['count']) if siblings else None,
            'identified_parent_child_pairs': len(parent_child),
            'sibling_examples': siblings[:5],
            'parent_child_examples': parent_child[:5]
        }