"""
Election Strategic Insights Module
Provides strategic classification and campaign recommendations for polling stations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

class ElectionInsights:
    """Generate strategic insights for election campaigns"""

    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.total_voters = len(data)
        self._preprocess_data()

    def _preprocess_data(self):
        """Preprocess data for analysis"""
        # Extract age and gender if needed
        if 'Gender / Age' in self.data.columns and 'Age' not in self.data.columns:
            self.data[['Gender', 'Age']] = self.data['Gender / Age'].str.extract(r'([MF])\s*/\s*(\d+)')
            self.data['Age'] = pd.to_numeric(self.data['Age'], errors='coerce')

    def classify_polling_station(self) -> Dict:
        """
        Classify polling station as SAFE BASE, SWING, or CONTESTED
        Returns classification with confidence level and factors
        """
        classification = {}

        # Get religion distribution
        if 'religion' in self.data.columns:
            religion_counts = self.data['religion'].value_counts()
            total = religion_counts.sum()

            # Calculate percentages
            religion_pcts = (religion_counts / total * 100).round(1)
            max_religion = religion_pcts.index[0]
            max_pct = religion_pcts.iloc[0]

            # Determine classification based on religious dominance
            if max_pct >= 70:
                classification['type'] = 'SAFE BASE'
                classification['sub_type'] = f'{max_religion} Dominated'
                classification['confidence'] = 'HIGH'
                classification['description'] = f'Strong {max_religion} majority provides solid base'
            elif max_pct >= 60:
                classification['type'] = 'SAFE BASE'
                classification['sub_type'] = f'{max_religion} Majority'
                classification['confidence'] = 'MEDIUM-HIGH'
                classification['description'] = f'{max_religion} majority with some minority presence'
            elif max_pct >= 50:
                classification['type'] = 'COMPETITIVE'
                classification['sub_type'] = f'{max_religion} Leaning'
                classification['confidence'] = 'MEDIUM'
                classification['description'] = f'Competitive with {max_religion} advantage'
            elif max_pct >= 40:
                classification['type'] = 'SWING'
                classification['sub_type'] = 'Balanced Demographics'
                classification['confidence'] = 'LOW-MEDIUM'
                classification['description'] = 'Highly competitive swing constituency'
            else:
                classification['type'] = 'CONTESTED'
                classification['sub_type'] = 'Fragmented'
                classification['confidence'] = 'LOW'
                classification['description'] = 'Multiple competing vote banks'

            classification['religious_breakdown'] = religion_pcts.to_dict()

        else:
            classification['type'] = 'UNCLASSIFIED'
            classification['sub_type'] = 'No Data'
            classification['confidence'] = 'N/A'
            classification['description'] = 'Insufficient data for classification'

        # Add age factor
        if 'Age' in self.data.columns:
            youth_pct = ((self.data['Age'] >= 18) & (self.data['Age'] <= 35)).mean() * 100
            if youth_pct > 35:
                classification['age_factor'] = 'YOUTH HEAVY'
            elif youth_pct < 20:
                classification['age_factor'] = 'AGING POPULATION'
            else:
                classification['age_factor'] = 'BALANCED AGE'

        return classification

    def calculate_winning_scenarios(self) -> Dict:
        """Calculate different winning scenarios based on demographics"""
        scenarios = {}

        if 'religion' not in self.data.columns:
            return {'error': 'Religion data not available for scenario calculation'}

        religion_counts = self.data['religion'].value_counts()
        total = self.total_voters

        # Target vote share needed to win (50% + 1)
        winning_threshold = (total // 2) + 1

        # Get religion percentages
        hindu_votes = religion_counts.get('Hindu', 0)
        muslim_votes = religion_counts.get('Muslim', 0)
        christian_votes = religion_counts.get('Christian', 0)

        # Scenario based on majority religion
        if hindu_votes >= muslim_votes and hindu_votes >= christian_votes:
            # Hindu majority scenario
            scenarios['primary_strategy'] = {
                'name': 'Hindu Consolidation Strategy',
                'formula': 'Consolidate Hindu base + Minority goodwill',
                'requirements': {
                    'hindu_consolidation': {
                        'total': hindu_votes,
                        'needed_percentage': 75,
                        'expected_votes': int(hindu_votes * 0.75)
                    },
                    'minority_support': {
                        'total': muslim_votes + christian_votes,
                        'needed_percentage': 20,
                        'expected_votes': int((muslim_votes + christian_votes) * 0.20)
                    }
                },
                'total_expected': int(hindu_votes * 0.75 + (muslim_votes + christian_votes) * 0.20),
                'vote_share': round((hindu_votes * 0.75 + (muslim_votes + christian_votes) * 0.20) / total * 100, 1),
                'margin': int(hindu_votes * 0.75 + (muslim_votes + christian_votes) * 0.20 - winning_threshold)
            }

        elif muslim_votes >= hindu_votes and muslim_votes >= christian_votes:
            # Muslim majority scenario
            scenarios['primary_strategy'] = {
                'name': 'Muslim Consolidation Strategy',
                'formula': 'Consolidate Muslim base + Secular appeal',
                'requirements': {
                    'muslim_consolidation': {
                        'total': muslim_votes,
                        'needed_percentage': 80,
                        'expected_votes': int(muslim_votes * 0.80)
                    },
                    'secular_support': {
                        'total': hindu_votes + christian_votes,
                        'needed_percentage': 35,
                        'expected_votes': int((hindu_votes + christian_votes) * 0.35)
                    }
                },
                'total_expected': int(muslim_votes * 0.80 + (hindu_votes + christian_votes) * 0.35),
                'vote_share': round((muslim_votes * 0.80 + (hindu_votes + christian_votes) * 0.35) / total * 100, 1),
                'margin': int(muslim_votes * 0.80 + (hindu_votes + christian_votes) * 0.35 - winning_threshold)
            }

        else:
            # Christian majority or highly mixed scenario
            scenarios['primary_strategy'] = {
                'name': 'Coalition Building Strategy',
                'formula': 'Build cross-community coalition',
                'requirements': {
                    'christian_consolidation': {
                        'total': christian_votes,
                        'needed_percentage': 85,
                        'expected_votes': int(christian_votes * 0.85)
                    },
                    'coalition_support': {
                        'total': hindu_votes + muslim_votes,
                        'needed_percentage': 40,
                        'expected_votes': int((hindu_votes + muslim_votes) * 0.40)
                    }
                },
                'total_expected': int(christian_votes * 0.85 + (hindu_votes + muslim_votes) * 0.40),
                'vote_share': round((christian_votes * 0.85 + (hindu_votes + muslim_votes) * 0.40) / total * 100, 1),
                'margin': int(christian_votes * 0.85 + (hindu_votes + muslim_votes) * 0.40 - winning_threshold)
            }

        # Alternative scenarios with different risk levels
        scenarios['conservative'] = {
            'target_vote_share': 55,
            'votes_needed': int(total * 0.55),
            'margin_of_victory': int(total * 0.55 - winning_threshold),
            'risk_level': 'LOW'
        }

        scenarios['moderate'] = {
            'target_vote_share': 52,
            'votes_needed': int(total * 0.52),
            'margin_of_victory': int(total * 0.52 - winning_threshold),
            'risk_level': 'MEDIUM'
        }

        scenarios['aggressive'] = {
            'target_vote_share': 50.5,
            'votes_needed': int(total * 0.505),
            'margin_of_victory': int(total * 0.505 - winning_threshold),
            'risk_level': 'HIGH'
        }

        return scenarios

    def identify_priority_demographics(self) -> List[Dict]:
        """Identify and rank priority target demographics"""
        priorities = []

        # 1. Middle-aged women (30-50)
        if 'Age' in self.data.columns and 'Gender' in self.data.columns:
            middle_women = self.data[
                (self.data['Gender'] == 'F') &
                (self.data['Age'] >= 30) &
                (self.data['Age'] <= 50)
            ]
            if len(middle_women) > 0:
                priorities.append({
                    'rank': 1,
                    'demographic': 'Middle-aged women (30-50)',
                    'count': len(middle_women),
                    'percentage': round(len(middle_women) / self.total_voters * 100, 1),
                    'why': 'Largest persuadable group, family decision-makers',
                    'how': 'Women-centric rallies, SHG engagement, welfare promises'
                })

        # 2. Large household members (identified separately)
        # This will be added from household analysis

        # 3. Young voters (18-35)
        if 'Age' in self.data.columns:
            young_voters = self.data[(self.data['Age'] >= 18) & (self.data['Age'] <= 35)]
            if len(young_voters) > 0:
                priorities.append({
                    'rank': 3,
                    'demographic': 'Young voters (18-35)',
                    'count': len(young_voters),
                    'percentage': round(len(young_voters) / self.total_voters * 100, 1),
                    'why': 'Aspirational, persuadable, digital-savvy',
                    'how': 'Employment promises, social media, youth leaders'
                })

        # 4. Senior citizens (60+)
        if 'Age' in self.data.columns:
            seniors = self.data[self.data['Age'] >= 60]
            if len(seniors) > 0:
                priorities.append({
                    'rank': 4,
                    'demographic': 'Senior citizens (60+)',
                    'count': len(seniors),
                    'percentage': round(len(seniors) / self.total_voters * 100, 1),
                    'why': 'High turnout, consistent voters',
                    'how': 'Healthcare, pension, respect for elders'
                })

        # 5. First-time voters (18-21)
        if 'Age' in self.data.columns:
            first_timers = self.data[(self.data['Age'] >= 18) & (self.data['Age'] <= 21)]
            if len(first_timers) > 0:
                priorities.append({
                    'rank': 5,
                    'demographic': 'First-time voters (18-21)',
                    'count': len(first_timers),
                    'percentage': round(len(first_timers) / self.total_voters * 100, 1),
                    'why': 'Malleable, high energy, future base',
                    'how': 'Campus outreach, social media, youth icons'
                })

        # Sort by rank
        priorities.sort(key=lambda x: x.get('rank', 999))

        return priorities

    def get_gender_analysis(self) -> Dict:
        """Detailed gender analysis focusing on women voters"""
        if 'Gender' not in self.data.columns:
            return {'error': 'Gender data not available'}

        gender_counts = self.data['Gender'].value_counts()
        male_count = gender_counts.get('M', 0)
        female_count = gender_counts.get('F', 0)
        total = male_count + female_count

        analysis = {
            'overall': {
                'male_voters': int(male_count),
                'female_voters': int(female_count),
                'male_percentage': round(male_count / total * 100, 1) if total > 0 else 0,
                'female_percentage': round(female_count / total * 100, 1) if total > 0 else 0,
                'gender_gap': int(female_count - male_count),
                'female_majority': female_count > male_count
            }
        }

        # Critical demographic: Middle-aged women
        if 'Age' in self.data.columns:
            middle_women = self.data[
                (self.data['Gender'] == 'F') &
                (self.data['Age'] >= 30) &
                (self.data['Age'] <= 50)
            ]
            analysis['middle_aged_women'] = {
                'total': len(middle_women),
                'percentage_of_electorate': round(len(middle_women) / self.total_voters * 100, 1),
                'percentage_of_women': round(len(middle_women) / female_count * 100, 1) if female_count > 0 else 0,
                'strategic_importance': 'PRIMARY - Family decision makers, welfare scheme beneficiaries',
                'campaign_priorities': [
                    'Self-help groups (SHG) engagement',
                    'Healthcare and child education focus',
                    'Safety and security messaging',
                    'Cooking gas and ration subsidies'
                ]
            }

        return analysis

    def get_age_distribution_analysis(self) -> Dict:
        """Detailed age-based analysis with strategic priorities"""
        if 'Age' not in self.data.columns:
            return {'error': 'Age data not available'}

        age_groups = {
            '18-25': {'label': 'First-time + Early voters', 'priority': 'HIGH', 'strategy': 'Malleable, high energy'},
            '26-35': {'label': 'Young professionals', 'priority': 'HIGH', 'strategy': 'Career-focused, aspirational'},
            '36-45': {'label': 'Established families', 'priority': 'HIGHEST', 'strategy': 'Decision-makers'},
            '46-55': {'label': 'Peak earning', 'priority': 'HIGHEST', 'strategy': 'Stable voters'},
            '56-65': {'label': 'Pre-retirement', 'priority': 'HIGH', 'strategy': 'High turnout'},
            '66+': {'label': 'Senior citizens', 'priority': 'MEDIUM', 'strategy': 'Loyal voters'}
        }

        distribution = {}
        for age_range, info in age_groups.items():
            if '-' in age_range:
                min_age, max_age = map(int, age_range.split('-'))
                count = ((self.data['Age'] >= min_age) & (self.data['Age'] <= max_age)).sum()
            else:  # 66+
                count = (self.data['Age'] >= 66).sum()

            distribution[age_range] = {
                'label': info['label'],
                'count': int(count),
                'percentage': round(count / self.total_voters * 100, 1),
                'priority': info['priority'],
                'strategy': info['strategy']
            }

        # Identify primary target age group
        primary_target = max(distribution.items(), key=lambda x: x[1]['count'])

        return {
            'distribution': distribution,
            'primary_target': {
                'age_group': primary_target[0],
                'percentage': primary_target[1]['percentage'],
                'strategy': f"Focus on {primary_target[1]['label']} - {primary_target[1]['strategy']}"
            },
            'mean_age': round(self.data['Age'].mean(), 1),
            'median_age': round(self.data['Age'].median(), 1),
            'first_time_voters': int(((self.data['Age'] >= 18) & (self.data['Age'] <= 21)).sum())
        }

    def generate_key_actions(self) -> List[str]:
        """Generate top 5 key actions based on analysis"""
        actions = []

        # Get basic stats for decision making
        if 'religion' in self.data.columns:
            religion_counts = self.data['religion'].value_counts()
            dominant_religion = religion_counts.index[0] if len(religion_counts) > 0 else None

            if dominant_religion:
                actions.append(f"Consolidate {dominant_religion} vote bank through community leaders")

        # Age-based actions
        if 'Age' in self.data.columns:
            youth_pct = ((self.data['Age'] >= 18) & (self.data['Age'] <= 35)).mean() * 100
            if youth_pct > 30:
                actions.append("Launch aggressive social media campaign targeting youth")

            senior_pct = (self.data['Age'] >= 60).mean() * 100
            if senior_pct > 20:
                actions.append("Organize senior citizen outreach with transport on election day")

        # Gender-based actions
        if 'Gender' in self.data.columns:
            female_pct = (self.data['Gender'] == 'F').mean() * 100
            if female_pct > 48:
                actions.append("Women-centric campaign with SHG meetings and welfare focus")

        # Standard actions
        actions.extend([
            "Door-to-door campaign for large households (5+ voters)",
            "WhatsApp groups covering 60% of 18-35 demographic",
            "Community meetings with 50+ attendance each",
            "GOTV drive targeting 75%+ turnout on election day"
        ])

        return actions[:5]  # Return top 5

    def generate_success_metrics(self) -> Dict:
        """Generate measurable success metrics for campaign"""
        metrics = {
            'coverage_targets': {
                'large_households': '100% personal contact (5+ voter houses)',
                'youth_whatsapp': '60% coverage of 18-35 age group',
                'women_shg': '3+ SHG meetings with 30+ attendance'
            },
            'turnout_targets': {
                'minimum': {'percentage': 65, 'voters': int(self.total_voters * 0.65)},
                'target': {'percentage': 75, 'voters': int(self.total_voters * 0.75)},
                'stretch': {'percentage': 85, 'voters': int(self.total_voters * 0.85)}
            },
            'outreach_metrics': {
                'door_to_door': f'{int(self.total_voters * 0.8)} voters contacted',
                'community_meetings': '3+ meetings with 50+ attendance',
                'family_heads': 'Personal meetings with top 10 family heads'
            }
        }

        return metrics