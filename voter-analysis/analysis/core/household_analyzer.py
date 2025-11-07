"""
Household-based Family Analysis Module for Election Insights
Identifies influential households based on house address (OldWard No/ House No.)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict

class HouseholdAnalyzer:
    """Analyze households and influential families based on house address"""

    def __init__(self, data: pd.DataFrame):
        self.data = data
        self._preprocess_data()

    def _preprocess_data(self):
        """Preprocess data for household analysis"""
        # Ensure we have the house address column
        if 'OldWard No/ House No.' not in self.data.columns:
            # Try alternative column names
            house_cols = [col for col in self.data.columns if 'house' in col.lower()]
            if house_cols:
                self.data['house_address'] = self.data[house_cols[0]]
            else:
                self.data['house_address'] = 'Unknown'
        else:
            self.data['house_address'] = self.data['OldWard No/ House No.']

        # Extract age and gender if needed
        if 'Gender / Age' in self.data.columns and 'Age' not in self.data.columns:
            self.data[['Gender', 'Age']] = self.data['Gender / Age'].str.extract(r'([MF])\s*/\s*(\d+)')
            self.data['Age'] = pd.to_numeric(self.data['Age'], errors='coerce')

    def get_top_influential_households(self, top_n: int = 10) -> List[Dict]:
        """
        Get top N influential households based on voter count
        Returns list of households with all member details
        """
        # Group by house address
        house_groups = self.data.groupby('house_address')

        # Calculate household sizes
        house_sizes = house_groups.size().sort_values(ascending=False)

        # Filter out 'Unknown' or invalid addresses
        house_sizes = house_sizes[~house_sizes.index.isin(['Unknown', '', 'N/A', None])]

        # Get top N households
        top_houses = house_sizes.head(top_n)

        influential_households = []
        total_voters = len(self.data)

        for house_address, member_count in top_houses.items():
            # Get all members of this household
            household_data = self.data[self.data['house_address'] == house_address]

            # Extract member details
            members = self._extract_household_members(household_data)

            # Get religious composition
            religion_comp = household_data['religion'].value_counts().to_dict() if 'religion' in household_data.columns else {}

            # Identify potential head of household (eldest member)
            if 'Age' in household_data.columns:
                eldest_idx = household_data['Age'].idxmax()
                head_of_house = household_data.loc[eldest_idx, 'Name'] if pd.notna(eldest_idx) else 'Unknown'
            else:
                head_of_house = household_data.iloc[0]['Name'] if len(household_data) > 0 else 'Unknown'

            # Get unique guardians in the household
            unique_guardians = household_data["Guardian's Name"].nunique() if "Guardian's Name" in household_data.columns else 1

            # Determine household type
            household_type = self._determine_household_type(member_count, unique_guardians)

            # Calculate voting power
            voting_power = round(member_count / total_voters * 100, 2)

            household_info = {
                'house_address': str(house_address),
                'total_members': int(member_count),
                'voting_power_percentage': voting_power,
                'head_of_household': head_of_house,
                'household_type': household_type,
                'unique_guardians': int(unique_guardians),
                'religious_composition': religion_comp,
                'members': members,
                'strategy': self._generate_household_strategy(member_count, religion_comp, household_type)
            }

            influential_households.append(household_info)

        return influential_households

    def _extract_household_members(self, household_data: pd.DataFrame) -> List[Dict]:
        """Extract all members of a household with their details"""
        members = []

        # Sort by age (eldest first) if available
        if 'Age' in household_data.columns:
            household_data = household_data.sort_values('Age', ascending=False, na_position='last')

        for idx, row in household_data.iterrows():
            member = {
                'serial_no': row.get('Serial No.', row.get('New SEC ID No.', 'N/A')),
                'name': row.get('Name', 'Unknown'),
                'guardian': row.get("Guardian's Name", 'N/A'),
                'age': int(row.get('Age', 0)) if pd.notna(row.get('Age')) else 'N/A',
                'gender': row.get('Gender', 'N/A'),
                'religion': row.get('religion', 'N/A'),
                'house_name': row.get('House Name', 'N/A')
            }

            # Determine relationship based on age and guardian
            member['relationship'] = self._infer_relationship(member, household_data)

            members.append(member)

        return members

    def _infer_relationship(self, member: Dict, household_data: pd.DataFrame) -> str:
        """Infer family relationship based on age and guardian patterns"""
        # Simple heuristic-based relationship inference
        if member['age'] != 'N/A':
            age = member['age']

            # Check if this person is a guardian for others
            is_guardian = False
            if member['name'] != 'Unknown':
                is_guardian = (household_data["Guardian's Name"] == member['name']).any()

            if is_guardian:
                if age >= 45:
                    return "Head of Family"
                else:
                    return "Parent"
            elif age >= 60:
                return "Elder"
            elif age >= 35:
                return "Adult Member"
            elif age >= 18:
                return "Young Adult"

        return "Member"

    def _determine_household_type(self, member_count: int, unique_guardians: int) -> str:
        """Determine the type of household based on size and guardian patterns"""
        if member_count == 1:
            return "Single Person"
        elif member_count == 2:
            return "Couple/Small"
        elif member_count <= 4:
            return "Nuclear Family"
        elif member_count <= 6:
            if unique_guardians == 1:
                return "Joint Family"
            else:
                return "Extended Family"
        elif member_count <= 10:
            if unique_guardians <= 2:
                return "Large Joint Family"
            else:
                return "Multi-Family House"
        else:
            return "Very Large Household"

    def _generate_household_strategy(self, member_count: int, religion_comp: Dict, household_type: str) -> str:
        """Generate campaign strategy for the household"""
        strategies = []

        # Size-based strategy
        if member_count >= 10:
            strategies.append("High-priority personal visit by senior leader")
        elif member_count >= 5:
            strategies.append("Personal home visit by campaign team")
        else:
            strategies.append("Door-to-door canvassing")

        # Type-based strategy
        if "Joint" in household_type or "Extended" in household_type:
            strategies.append("Focus on family head/eldest member")
        elif "Multi-Family" in household_type:
            strategies.append("Multiple touchpoints for different families")

        # Religion-based strategy
        if len(religion_comp) > 1:
            strategies.append("Secular/inclusive messaging")
        elif religion_comp:
            dominant_religion = max(religion_comp, key=religion_comp.get)
            strategies.append(f"Community-specific outreach ({dominant_religion})")

        return " | ".join(strategies)

    def get_household_statistics(self) -> Dict:
        """Get comprehensive household statistics"""
        house_groups = self.data.groupby('house_address')
        house_sizes = house_groups.size()

        # Filter out invalid addresses
        valid_houses = house_sizes[~house_sizes.index.isin(['Unknown', '', 'N/A', None])]

        stats = {
            'total_households': len(valid_houses),
            'total_voters': len(self.data),
            'average_household_size': round(valid_houses.mean(), 2),
            'median_household_size': round(valid_houses.median(), 1),
            'largest_household': {
                'address': valid_houses.idxmax() if len(valid_houses) > 0 else None,
                'size': int(valid_houses.max()) if len(valid_houses) > 0 else 0
            },
            'household_size_distribution': {
                'single_person': int((valid_houses == 1).sum()),
                'small_2_3': int(((valid_houses >= 2) & (valid_houses <= 3)).sum()),
                'medium_4_5': int(((valid_houses >= 4) & (valid_houses <= 5)).sum()),
                'large_6_10': int(((valid_houses >= 6) & (valid_houses <= 10)).sum()),
                'very_large_10_plus': int((valid_houses > 10).sum())
            }
        }

        # Calculate percentages
        total = stats['total_households']
        if total > 0:
            stats['household_size_percentages'] = {
                k: round(v/total*100, 1)
                for k, v in stats['household_size_distribution'].items()
            }

        return stats

    def get_top_large_households(self, min_size: int = 5, top_n: int = 20) -> pd.DataFrame:
        """Get top N households with minimum size (for table display)"""
        house_groups = self.data.groupby('house_address')

        # Get household sizes and filter
        house_data = []
        for house_address, group in house_groups:
            if house_address in ['Unknown', '', 'N/A', None]:
                continue

            size = len(group)
            if size >= min_size:
                # Get majority religion
                if 'religion' in group.columns:
                    religion_counts = group['religion'].value_counts()
                    majority_religion = religion_counts.index[0] if len(religion_counts) > 0 else 'Unknown'
                else:
                    majority_religion = 'N/A'

                house_data.append({
                    'House Address': house_address,
                    'Voters': size,
                    'Religion (Majority)': majority_religion
                })

        # Convert to DataFrame and sort
        df = pd.DataFrame(house_data)
        if len(df) > 0:
            df = df.sort_values('Voters', ascending=False).head(top_n)

        return df

    def identify_special_households(self) -> Dict:
        """Identify special types of households for targeted strategies"""
        house_groups = self.data.groupby('house_address')

        special = {
            'inter_religious': [],
            'youth_concentrated': [],
            'senior_only': [],
            'women_only': [],
            'first_time_voters': [],
            'multi_family': []
        }

        for house_address, group in house_groups:
            if house_address in ['Unknown', '', 'N/A', None] or len(group) < 2:
                continue

            # Inter-religious households
            if 'religion' in group.columns:
                religions = group['religion'].nunique()
                if religions > 1:
                    special['inter_religious'].append({
                        'address': house_address,
                        'size': len(group),
                        'religions': group['religion'].value_counts().to_dict()
                    })

            # Youth concentrated (>50% under 35)
            if 'Age' in group.columns:
                youth_pct = ((group['Age'] >= 18) & (group['Age'] <= 35)).mean()
                if youth_pct > 0.5 and len(group) >= 3:
                    special['youth_concentrated'].append({
                        'address': house_address,
                        'size': len(group),
                        'youth_percentage': round(youth_pct * 100, 1)
                    })

                # Senior only households
                if (group['Age'] >= 60).all() and len(group) >= 1:
                    special['senior_only'].append({
                        'address': house_address,
                        'size': len(group)
                    })

                # First-time voter households
                first_timers = ((group['Age'] >= 18) & (group['Age'] <= 21)).sum()
                if first_timers >= 2:
                    special['first_time_voters'].append({
                        'address': house_address,
                        'size': len(group),
                        'first_time_voters': int(first_timers)
                    })

            # Women only households
            if 'Gender' in group.columns:
                if (group['Gender'] == 'F').all() and len(group) >= 2:
                    special['women_only'].append({
                        'address': house_address,
                        'size': len(group)
                    })

            # Multi-family (multiple guardians)
            if "Guardian's Name" in group.columns:
                unique_guardians = group["Guardian's Name"].nunique()
                if unique_guardians >= 3:
                    special['multi_family'].append({
                        'address': house_address,
                        'size': len(group),
                        'families': int(unique_guardians)
                    })

        return special