"""
Election Insights Report Generator
Generates professional campaign reports matching the Bharanikkav format
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import os

from ..core.household_analyzer import HouseholdAnalyzer
from ..core.election_insights import ElectionInsights
from ..core.cross_demographics import CrossDemographicAnalyzer
from ..core.geographic_analyzer import GeographicAnalyzer
from ..core.pattern_detector import PatternDetector
from ..core.ai_insights import AIInsightsGenerator


class ElectionReportGenerator:
    """Generate comprehensive election insights reports"""

    def __init__(self, data: pd.DataFrame, station_name: str, ward_name: str, enable_ai: bool = False):
        self.data = data
        self.station_name = station_name
        self.ward_name = ward_name
        self.total_voters = len(data)
        self.enable_ai = enable_ai

        # Initialize core analyzers
        self.household_analyzer = HouseholdAnalyzer(data)
        self.election_insights = ElectionInsights(data)

        # Initialize new analyzers
        self.cross_demographics = CrossDemographicAnalyzer(data)
        self.geographic_analyzer = GeographicAnalyzer(data)
        self.pattern_detector = PatternDetector(data)

        # Initialize AI insights (optional)
        self.ai_generator = None
        if self.enable_ai:
            try:
                self.ai_generator = AIInsightsGenerator()
                print(f"    ✓ AI Insights enabled for {station_name}")
            except Exception as e:
                print(f"    ⚠ AI Insights disabled: {str(e)}")
                self.enable_ai = False

    def generate_full_report(self) -> str:
        """Generate complete HTML report with enhanced analysis"""

        # Generate all sections (original)
        classification = self.election_insights.classify_polling_station()
        executive_summary = self._generate_executive_summary(classification)
        religious_demographics = self._generate_religious_demographics()
        age_analysis = self._generate_age_analysis()
        gender_analysis = self._generate_gender_analysis()
        household_analysis = self._generate_household_analysis()

        # Generate NEW enhanced sections
        cross_demographic_analysis = self._generate_cross_demographic_analysis()
        geographic_analysis = self._generate_geographic_analysis()
        pattern_analysis = self._generate_pattern_analysis()

        # Original sections (continued)
        winning_strategy = self._generate_winning_strategy()
        priority_demographics = self._generate_priority_demographics()
        final_recommendations = self._generate_final_recommendations()

        # Build complete HTML with all sections
        html = self._build_html_template(
            classification,
            executive_summary,
            religious_demographics,
            age_analysis,
            gender_analysis,
            household_analysis,
            cross_demographic_analysis,
            geographic_analysis,
            pattern_analysis,
            winning_strategy,
            priority_demographics,
            final_recommendations
        )

        return html

    def _generate_executive_summary(self, classification: Dict) -> str:
        """Generate executive summary section"""
        age_stats = self.election_insights.get_age_distribution_analysis()

        avg_age = age_stats.get('mean_age', 'N/A')
        median_age = age_stats.get('median_age', 'N/A')

        # Get classification details
        class_type = classification.get('type', 'UNCLASSIFIED')
        description = classification.get('description', 'No classification available')

        # Determine color based on classification
        class_color = {
            'SAFE BASE': '#27ae60',
            'COMPETITIVE': '#f39c12',
            'SWING': '#e74c3c',
            'CONTESTED': '#e74c3c'
        }.get(class_type, '#95a5a6')

        html = f"""
        <div class="executive-summary">
            <h2 class="section-title">EXECUTIVE SUMMARY</h2>

            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{self.total_voters:,}</div>
                    <div class="metric-label">Total Voters</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{avg_age}</div>
                    <div class="metric-label">Average Age (years)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{median_age}</div>
                    <div class="metric-label">Median Age (years)</div>
                </div>
            </div>

            <div class="critical-finding">
                <h3>Critical Finding</h3>
                <p><span class="classification-badge" style="background: {class_color};">{class_type}</span></p>
                <p>{description}</p>
            </div>
        </div>
        """

        return html

    def _generate_religious_demographics(self) -> str:
        """Generate religious demographics section"""
        if 'religion' not in self.data.columns:
            return '<p>Religion data not available</p>'

        religion_counts = self.data['religion'].value_counts()
        total = religion_counts.sum()

        # Build table
        table_rows = ""
        for religion, count in religion_counts.items():
            pct = round(count / total * 100, 1)
            table_rows += f"""
            <tr>
                <td>{religion}</td>
                <td>{count:,}</td>
                <td>{pct}%</td>
            </tr>
            """

        # Age profiles by religion
        age_profile_rows = ""
        if 'Age' in self.data.columns:
            for religion in religion_counts.index[:3]:  # Top 3 religions
                religion_data = self.data[self.data['religion'] == religion]

                young = ((religion_data['Age'] >= 18) & (religion_data['Age'] <= 35)).sum()
                middle = ((religion_data['Age'] >= 36) & (religion_data['Age'] <= 55)).sum()
                senior = (religion_data['Age'] >= 56).sum()

                total_rel = len(religion_data)
                avg_age = round(religion_data['Age'].mean(), 1)

                young_pct = round(young / total_rel * 100, 1) if total_rel > 0 else 0
                middle_pct = round(middle / total_rel * 100, 1) if total_rel > 0 else 0
                senior_pct = round(senior / total_rel * 100, 1) if total_rel > 0 else 0

                age_profile_rows += f"""
                <tr>
                    <td>{religion}</td>
                    <td>{avg_age} yrs</td>
                    <td>{young} ({young_pct}%)</td>
                    <td>{middle} ({middle_pct}%)</td>
                    <td>{senior} ({senior_pct}%)</td>
                </tr>
                """

        html = f"""
        <div class="section">
            <h2 class="section-title">1. RELIGIOUS DEMOGRAPHICS & STRATEGIC IMPLICATIONS</h2>

            <h3 class="subsection-title">1.1 Religious Composition</h3>
            <table>
                <thead>
                    <tr>
                        <th>Religion</th>
                        <th>Total Voters</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>

            <div class="strategic-insight">
                <div class="insight-title">Strategic Insight:</div>
                <p>{self._get_religious_strategic_insight(religion_counts)}</p>
            </div>

            <h3 class="subsection-title">1.2 Age Profiles by Religion</h3>
            <table>
                <thead>
                    <tr>
                        <th>Religion</th>
                        <th>Avg Age</th>
                        <th>Young (≤35)</th>
                        <th>Middle (36-55)</th>
                        <th>Senior (56+)</th>
                    </tr>
                </thead>
                <tbody>
                    {age_profile_rows}
                </tbody>
            </table>
        </div>
        """

        return html

    def _get_religious_strategic_insight(self, religion_counts: pd.Series) -> str:
        """Generate strategic insight based on religious composition"""
        if len(religion_counts) == 0:
            return "Insufficient data for strategic analysis."

        total = religion_counts.sum()
        dominant = religion_counts.index[0]
        dominant_pct = round(religion_counts.iloc[0] / total * 100, 1)

        if dominant_pct >= 70:
            return f"Strong {dominant} base ({dominant_pct}%) provides solid foundation. Focus on maintaining unity and high turnout."
        elif dominant_pct >= 60:
            return f"{dominant} majority ({dominant_pct}%) ensures baseline support. Coalition-building with minorities recommended for decisive victory."
        elif dominant_pct >= 50:
            return f"{dominant} has advantage ({dominant_pct}%) but victory requires strong minority outreach and avoiding polarization."
        else:
            return f"Balanced demographics with {dominant} plurality ({dominant_pct}%). Success depends on building cross-community coalition."

    def _generate_age_analysis(self) -> str:
        """Generate age-based analysis section"""
        age_data = self.election_insights.get_age_distribution_analysis()

        if 'error' in age_data:
            return '<p>Age data not available</p>'

        distribution = age_data['distribution']

        # Build table
        table_rows = ""
        for age_group, data in distribution.items():
            priority_class = {
                'HIGHEST': 'priority-high',
                'HIGH': 'priority-high',
                'MEDIUM': 'priority-medium',
                'LOW': 'priority-low'
            }.get(data['priority'], '')

            table_rows += f"""
            <tr>
                <td>{age_group}</td>
                <td>{data['label']}</td>
                <td>{data['count']:,}</td>
                <td>{data['percentage']}%</td>
                <td class="{priority_class}">{data['priority']}</td>
            </tr>
            """

        primary_target = age_data.get('primary_target', {})
        first_time = age_data.get('first_time_voters', 0)
        first_time_pct = round(first_time / self.total_voters * 100, 1)

        html = f"""
        <div class="section">
            <h2 class="section-title">2. AGE-BASED ANALYSIS & GENERATIONAL STRATEGY</h2>

            <h3 class="subsection-title">2.1 Age Distribution</h3>
            <table>
                <thead>
                    <tr>
                        <th>Age Group</th>
                        <th>Category</th>
                        <th>Total</th>
                        <th>Percentage</th>
                        <th>Strategic Priority</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>

            <div class="strategic-insight">
                <div class="insight-title">Critical Insight:</div>
                <p>{primary_target.get('strategy', 'Focus on primary demographic groups')}</p>
                <p><strong>First-time voters (18-21):</strong> {first_time:,} ({first_time_pct}% of electorate)</p>
            </div>
        </div>
        """

        return html

    def _generate_gender_analysis(self) -> str:
        """Generate gender analysis section"""
        gender_data = self.election_insights.get_gender_analysis()

        if 'error' in gender_data:
            return '<p>Gender data not available</p>'

        overall = gender_data['overall']
        middle_women = gender_data.get('middle_aged_women', {})

        html = f"""
        <div class="section">
            <h2 class="section-title">3. GENDER ANALYSIS - THE WOMEN VOTE</h2>

            <h3 class="subsection-title">3.1 Overall Gender Split</h3>
            <table>
                <thead>
                    <tr>
                        <th>Gender</th>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Male Voters</td>
                        <td>{overall['male_voters']:,}</td>
                        <td>{overall['male_percentage']}%</td>
                    </tr>
                    <tr>
                        <td>Female Voters</td>
                        <td>{overall['female_voters']:,}</td>
                        <td>{overall['female_percentage']}%</td>
                    </tr>
                </tbody>
            </table>

            <div class="strategic-insight">
                <div class="insight-title">Gender Gap Analysis:</div>
                <p>Female voters {"outnumber" if overall['gender_gap'] > 0 else "trail"} male voters by {abs(overall['gender_gap']):,} votes
                ({abs(round(overall['gender_gap'] / self.total_voters * 100, 1))}% margin).</p>
            </div>

            <h3 class="subsection-title">3.2 The Critical Demographic: Middle-Aged Women (30-50 years)</h3>
            <div class="action-list">
                <p><strong>Total middle-aged women:</strong> {middle_women.get('total', 0):,}
                ({middle_women.get('percentage_of_electorate', 0)}% of entire electorate)</p>

                <p><strong>STRATEGIC IMPERATIVE:</strong> This group represents 1 in {round(100/middle_women.get('percentage_of_electorate', 1))} voters. They are:</p>
                <ul>
                    <li>Primary household decision-makers</li>
                    <li>Concerned about healthcare, education, safety</li>
                    <li>Influenced by welfare schemes (ration, pension, housing)</li>
                    <li>Often decide how the entire family votes</li>
                </ul>

                <p><strong>Campaign Priority:</strong></p>
                <ul>
                    {''.join(f'<li>{priority}</li>' for priority in middle_women.get('campaign_priorities', []))}
                </ul>
            </div>
        </div>
        """

        return html

    def _generate_household_analysis(self) -> str:
        """Generate household and family voting blocs section"""

        # Get household statistics
        stats = self.household_analyzer.get_household_statistics()

        # Get top 20 large households
        large_households = self.household_analyzer.get_top_large_households(min_size=5, top_n=20)

        # Get top 10 influential families
        top_families = self.household_analyzer.get_top_influential_households(top_n=10)

        # Build large households table
        large_house_rows = ""
        if len(large_households) > 0:
            for _, row in large_households.iterrows():
                large_house_rows += f"""
                <tr>
                    <td>{row['House Address']}</td>
                    <td>{row['Voters']}</td>
                    <td>{row['Religion (Majority)']}</td>
                </tr>
                """

        # Build influential families section with expandable members
        families_html = ""
        for i, family in enumerate(top_families, 1):
            # Build member list
            members_html = ""
            for member in family['members']:
                members_html += f"""
                <div class="member-item">
                    <strong>{member['serial_no']}</strong> - {member['name']}
                    ({member['gender']}, {member['age']}) - {member['relationship']}
                </div>
                """

            # Religious composition
            religion_text = ", ".join([f"{k}: {v}" for k, v in family['religious_composition'].items()])

            families_html += f"""
            <div class="family-card">
                <div class="family-header" onclick="toggleFamily('family{i}')">
                    <div>
                        <strong>#{i}. {family['head_of_household']}</strong> - {family['house_address']}
                        <br>
                        <span style="font-size: 14px; color: #666;">
                            {family['total_members']} members | {family['voting_power_percentage']}% voting power |
                            {family['household_type']}
                        </span>
                    </div>
                    <span class="expand-icon" id="icon{i}">▼</span>
                </div>
                <div class="family-members" id="family{i}">
                    <div style="padding: 15px; background: #f8f9fa;">
                        <p><strong>Religious Composition:</strong> {religion_text}</p>
                        <p><strong>Strategy:</strong> {family['strategy']}</p>
                        <hr style="margin: 10px 0;">
                        <p><strong>Family Members:</strong></p>
                        {members_html}
                    </div>
                </div>
            </div>
            """

        html = f"""
        <div class="section">
            <h2 class="section-title">4. HOUSEHOLD & FAMILY VOTING BLOCS</h2>

            <h3 class="subsection-title">4.1 Household Size Analysis</h3>
            <p><strong>Total Unique Households:</strong> {stats['total_households']:,}</p>
            <p><strong>Average Voters per Household:</strong> {stats['average_household_size']}</p>
            <p><strong>Large Households (5+ voters):</strong> {stats['household_size_distribution']['large_6_10'] + stats['household_size_distribution']['very_large_10_plus']:,}</p>
            <p><strong>Very Large Households (8+ voters):</strong> {stats['household_size_distribution']['very_large_10_plus']:,}</p>

            <div class="strategic-insight">
                <div class="insight-title">Strategic Gold Mine:</div>
                <p>Large households contain significant voting power.
                <strong>Winning one influential family member = winning {stats['average_household_size']} votes</strong></p>
            </div>

            <h3 class="subsection-title">4.2 Top 20 Large Households (5+ Voters)</h3>
            <table>
                <thead>
                    <tr>
                        <th>House Address</th>
                        <th>Voters</th>
                        <th>Religion (Majority)</th>
                    </tr>
                </thead>
                <tbody>
                    {large_house_rows}
                </tbody>
            </table>

            <h3 class="subsection-title">4.4 Top 10 Influential Family Blocs</h3>
            <p style="margin-bottom: 15px;"><em>Click on each family to view all members with serial numbers</em></p>
            {families_html}
        </div>
        """

        return html

    def _generate_winning_strategy(self) -> str:
        """Generate winning strategy section"""
        scenarios = self.election_insights.calculate_winning_scenarios()

        if 'error' in scenarios:
            return '<p>Insufficient data for strategy calculation</p>'

        primary = scenarios.get('primary_strategy', {})

        # Build requirements section
        requirements_html = ""
        for key, req in primary.get('requirements', {}).items():
            requirements_html += f"""
            <li><strong>{key.replace('_', ' ').title()}:</strong> {req['total']:,} voters
            (need {req['needed_percentage']}% = {req['expected_votes']:,} votes)</li>
            """

        # Key actions
        key_actions = self.election_insights.generate_key_actions()
        actions_html = "".join([f"<li>{action}</li>" for action in key_actions])

        html = f"""
        <div class="section">
            <h2 class="section-title">8. WINNING STRATEGY FOR THIS DISTRICT</h2>

            <h3 class="subsection-title">Scenario: {primary.get('name', 'Primary Strategy')}</h3>
            <p><strong>Formula:</strong> {primary.get('formula', 'N/A')}</p>

            <div class="recommendation-box">
                <h4>Requirements:</h4>
                <ul>
                    {requirements_html}
                </ul>
                <p><strong>Expected Total:</strong> {primary.get('total_expected', 0):,} votes ({primary.get('vote_share', 0)}% vote share)</p>
                <p><strong>Margin of Victory:</strong> {primary.get('margin', 0):,} votes</p>
            </div>

            <div class="action-list">
                <h4>Key Actions:</h4>
                <ol>
                    {actions_html}
                </ol>
            </div>
        </div>
        """

        return html

    def _generate_priority_demographics(self) -> str:
        """Generate priority target demographics section"""
        priorities = self.election_insights.identify_priority_demographics()

        # Add large households as priority #2
        stats = self.household_analyzer.get_household_statistics()
        large_house_count = stats['household_size_distribution']['large_6_10'] + stats['household_size_distribution']['very_large_10_plus']

        # Insert large households at position 2
        if len(priorities) >= 2:
            priorities.insert(1, {
                'rank': 2,
                'demographic': 'Large households (5+ voters)',
                'count': large_house_count,
                'percentage': round(large_house_count / stats['total_households'] * 100, 1) if stats['total_households'] > 0 else 0,
                'why': 'One converted family = 5-8 votes',
                'how': 'Personal visits, respected community member introductions'
            })

        # Re-rank
        for i, p in enumerate(priorities, 1):
            p['rank'] = i

        # Build table
        rows_html = ""
        for p in priorities[:5]:  # Top 5
            rows_html += f"""
            <tr>
                <td><strong>{p['rank']}</strong></td>
                <td>{p['demographic']}</td>
                <td>{p['count']:,} ({p['percentage']}%)</td>
                <td>{p['why']}</td>
                <td>{p['how']}</td>
            </tr>
            """

        html = f"""
        <div class="section">
            <h2 class="section-title">9. PRIORITY TARGET DEMOGRAPHICS (Rank Ordered)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Demographic</th>
                        <th>Count</th>
                        <th>Why Important</th>
                        <th>How to Reach</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """

        return html

    def _generate_final_recommendations(self) -> str:
        """Generate final recommendations section"""
        metrics = self.election_insights.generate_success_metrics()

        # Top 5 actions
        actions = self.election_insights.generate_key_actions()
        actions_html = "".join([f"<li><strong>Action {i+1}:</strong> {action}</li>" for i, action in enumerate(actions[:5])])

        # Success metrics
        metrics_html = ""
        for key, value in metrics.get('coverage_targets', {}).items():
            metrics_html += f"<li>{value}</li>"

        turnout = metrics.get('turnout_targets', {})

        html = f"""
        <div class="section">
            <h2 class="section-title">10. FINAL RECOMMENDATIONS</h2>

            <div class="action-list">
                <h3 class="subsection-title">Top 5 Actions for {self.station_name}</h3>
                <ol>
                    {actions_html}
                </ol>
            </div>

            <div class="recommendation-box">
                <h3 class="subsection-title">Success Metrics</h3>
                <ul>
                    {metrics_html}
                </ul>

                <h4 style="margin-top: 15px;">Turnout Targets:</h4>
                <ul>
                    <li><strong>Minimum required:</strong> {turnout.get('minimum', {}).get('percentage', 0)}% ({turnout.get('minimum', {}).get('voters', 0):,} voters)</li>
                    <li><strong>Target:</strong> {turnout.get('target', {}).get('percentage', 0)}% ({turnout.get('target', {}).get('voters', 0):,} voters)</li>
                    <li><strong>Stretch goal:</strong> {turnout.get('stretch', {}).get('percentage', 0)}% ({turnout.get('stretch', {}).get('voters', 0):,} voters)</li>
                </ul>
            </div>
        </div>

        <div style="text-align: center; margin-top: 40px; padding: 20px; border-top: 3px solid #2c3e50;">
            <h3>Report End</h3>
            <p><strong>{self.station_name}:</strong> {self.total_voters:,} voters | Generated {datetime.now().strftime('%Y-%m-%d')}</p>
        </div>
        """

        return html

    def _generate_cross_demographic_analysis(self) -> str:
        """Generate cross-demographic analysis section (NEW)"""
        clusters = self.cross_demographics.identify_demographic_clusters()

        # Build top 10 clusters table
        cluster_rows = ""
        for i, cluster in enumerate(clusters[:10], 1):
            cluster_rows += f"""
            <tr>
                <td>{i}</td>
                <td>{cluster['label']}</td>
                <td>{cluster['count']:,}</td>
                <td>{cluster['percentage_of_electorate']}%</td>
                <td>{cluster['average_age']}</td>
            </tr>
            """

        # Get AI insight if enabled
        ai_insight_html = ""
        if self.enable_ai and self.ai_generator:
            try:
                cross_data = self.cross_demographics.analyze_age_gender_by_religion()
                ai_insight = self.ai_generator.generate_cross_demographic_insight(cross_data)
                ai_insight_html = f"""
                <div class="ai-insight-box">
                    <div class="ai-insight-title">🤖 AI Insight:</div>
                    <p>{ai_insight}</p>
                </div>
                """
            except:
                pass

        html = f"""
        <div class="section">
            <h2 class="section-title">5. CROSS-DEMOGRAPHIC ANALYSIS</h2>

            <h3 class="subsection-title">5.1 Strategic Demographic Clusters</h3>
            <p>Multi-dimensional demographic segments ranked by strategic value:</p>

            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Demographic Cluster</th>
                        <th>Voters</th>
                        <th>% of Electorate</th>
                        <th>Avg Age</th>
                    </tr>
                </thead>
                <tbody>
                    {cluster_rows}
                </tbody>
            </table>

            {ai_insight_html}

            <div class="strategic-insight">
                <div class="insight-title">Strategic Application:</div>
                <p>These clusters represent the most effective ways to segment your outreach. Focus on the top 3-5 clusters for maximum efficiency. Each cluster requires tailored messaging that speaks to their specific demographic identity.</p>
            </div>
        </div>
        """

        return html

    def _generate_geographic_analysis(self) -> str:
        """Generate geographic/regional analysis section (NEW)"""
        regional_data = self.geographic_analyzer.analyze_regional_demographics()
        enclaves = self.geographic_analyzer.identify_religious_enclaves()
        mixed_areas = self.geographic_analyzer.analyze_mixed_areas()

        # Build regional breakdown table
        region_rows = ""
        if 'regions' in regional_data:
            for region, data in regional_data['regions'].items():
                region_rows += f"""
                <tr>
                    <td>{region}</td>
                    <td>{data['house_range']}</td>
                    <td>{data['total_voters']:,}</td>
                    <td>{data['percentage_of_total']}%</td>
                    <td>{data['dominant_religion']} ({data['dominant_religion_percentage']}%)</td>
                </tr>
                """

        # Build enclaves list
        enclaves_html = ""
        for enclave in enclaves[:5]:
            if 'error' not in enclave:
                enclaves_html += f"""
                <div class="enclave-card">
                    <strong>Houses {enclave['house_range']}</strong>: {enclave['religion']} stronghold
                    ({enclave['dominance_percentage']}% - {enclave['total_voters']} voters)
                </div>
                """

        # Build mixed areas list
        mixed_html = ""
        for area in mixed_areas[:3]:
            if 'error' not in area:
                religions = ', '.join([f"{r}: {d['percentage']}%" for r, d in area['religion_breakdown'].items()])
                mixed_html += f"""
                <div class="mixed-area-card">
                    <strong>Houses {area['house_range']}</strong>: Diverse area
                    <br><span style="font-size: 14px;">{religions}</span>
                    <br><em>{area['strategic_importance']}</em>
                </div>
                """

        # Get AI insight if enabled
        ai_insight_html = ""
        if self.enable_ai and self.ai_generator:
            try:
                geographic_summary = self.geographic_analyzer.get_geographic_summary()
                ai_insight = self.ai_generator.generate_geographic_insight(geographic_summary)
                ai_insight_html = f"""
                <div class="ai-insight-box">
                    <div class="ai-insight-title">🤖 AI Insight:</div>
                    <p>{ai_insight}</p>
                </div>
                """
            except:
                pass

        html = f"""
        <div class="section">
            <h2 class="section-title">6. GEOGRAPHIC & REGIONAL ANALYSIS</h2>

            <h3 class="subsection-title">6.1 Regional Demographics by House Numbers</h3>
            <table>
                <thead>
                    <tr>
                        <th>Region</th>
                        <th>House Range</th>
                        <th>Voters</th>
                        <th>% Total</th>
                        <th>Dominant Group</th>
                    </tr>
                </thead>
                <tbody>
                    {region_rows}
                </tbody>
            </table>

            <h3 class="subsection-title">6.2 Religious Enclaves (70%+ Concentration)</h3>
            {enclaves_html if enclaves_html else '<p>No strong religious enclaves identified (healthy diversity)</p>'}

            <h3 class="subsection-title">6.3 Mixed/Swing Areas (High Diversity)</h3>
            {mixed_html if mixed_html else '<p>No highly mixed areas identified</p>'}

            {ai_insight_html}

            <div class="recommendation-box">
                <h4>Geographic Strategy:</h4>
                <ul>
                    <li>Target mixed areas with inclusive, cross-community messaging</li>
                    <li>In enclaves, focus on mobilization and turnout rather than persuasion</li>
                    <li>Use house number clustering for efficient door-to-door campaigns</li>
                </ul>
            </div>
        </div>
        """

        return html

    def _generate_pattern_analysis(self) -> str:
        """Generate pattern detection and anomaly analysis section (NEW)"""
        all_patterns = self.pattern_detector.get_all_anomalies_and_patterns()
        summary = all_patterns['summary']

        # Build critical patterns list
        critical_html = ""
        for i, pattern in enumerate(summary['top_5_critical'], 1):
            severity_class = f"severity-{pattern.get('severity', 'low')}"
            critical_html += f"""
            <div class="pattern-card {severity_class}">
                <div class="pattern-header">
                    <span class="severity-badge">{pattern.get('severity', 'N/A').upper()}</span>
                    <strong>{pattern.get('description', 'N/A')}</strong>
                </div>
                <p class="pattern-implication"><em>Implication:</em> {pattern.get('implication', 'N/A')}</p>
            </div>
            """

        # Get mixed faith households
        mixed_faith = all_patterns.get('mixed_faith_households', [])
        mixed_faith_html = ""
        if mixed_faith and len(mixed_faith) > 0 and 'details' in mixed_faith[0]:
            mixed_faith_html = f"""
            <h3 class="subsection-title">7.2 Mixed-Faith Households</h3>
            <p>Found {mixed_faith[0].get('description', 'mixed-faith households')}</p>
            <div class="strategic-insight">
                <div class="insight-title">Strategic Importance:</div>
                <p>{mixed_faith[0].get('implication', 'These households require inclusive messaging')}</p>
            </div>
            """

        # Get AI insight if enabled
        ai_insight_html = ""
        if self.enable_ai and self.ai_generator:
            try:
                anomalies = summary['top_5_critical']
                ai_insight = self.ai_generator.generate_anomaly_insight(anomalies)
                ai_insight_html = f"""
                <div class="ai-insight-box">
                    <div class="ai-insight-title">🤖 AI Insight:</div>
                    <p>{ai_insight}</p>
                </div>
                """
            except:
                pass

        html = f"""
        <div class="section">
            <h2 class="section-title">7. PATTERN DETECTION & ANOMALIES</h2>

            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-value">{summary['total_patterns_detected']}</div>
                    <div class="metric-label">Patterns Detected</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{summary['high_severity']}</div>
                    <div class="metric-label">High Priority</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{summary['medium_severity']}</div>
                    <div class="metric-label">Medium Priority</div>
                </div>
            </div>

            <h3 class="subsection-title">7.1 Critical Patterns & Anomalies</h3>
            {critical_html if critical_html else '<p>No critical patterns detected</p>'}

            {mixed_faith_html}

            {ai_insight_html}

            <div class="action-list">
                <h4>Action Items from Pattern Analysis:</h4>
                <ol>
                    <li>Review high-severity patterns and adjust strategy accordingly</li>
                    <li>Address identified demographic gaps or imbalances</li>
                    <li>Leverage unusual patterns as strategic opportunities</li>
                    <li>Monitor mixed-faith households for swing potential</li>
                </ol>
            </div>
        </div>
        """

        return html

    def _build_html_template(self, classification, *sections) -> str:
        """Build complete HTML document with all sections"""

        class_type = classification.get('type', 'UNCLASSIFIED')

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Election Insights Report - {self.station_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
            color: #333;
        }}

        .report-header {{
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}

        .report-title {{
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
            margin: 10px 0;
        }}

        .station-info {{
            font-size: 18px;
            color: #666;
            margin: 5px 0;
        }}

        .executive-summary {{
            background: #f8f9fa;
            border-left: 4px solid #e74c3c;
            padding: 20px;
            margin: 20px 0;
        }}

        .critical-finding {{
            background: #ffe4e1;
            border-left: 4px solid #e74c3c;
            padding: 15px;
            margin: 15px 0;
        }}

        .classification-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 3px;
            font-weight: bold;
            color: white;
            margin: 5px 0;
        }}

        .section {{
            margin: 30px 0;
        }}

        .section-title {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin: 25px 0 15px 0;
        }}

        .subsection-title {{
            font-size: 18px;
            font-weight: bold;
            color: #34495e;
            margin: 20px 0 10px 0;
        }}

        .strategic-insight {{
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 15px 0;
        }}

        .insight-title {{
            font-weight: bold;
            color: #2980b9;
            margin-bottom: 5px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}

        th {{
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}

        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
        }}

        tr:nth-child(even) {{
            background: #f8f9fa;
        }}

        tr:hover {{
            background: #ecf0f1;
        }}

        .priority-high {{
            color: #e74c3c;
            font-weight: bold;
        }}

        .priority-medium {{
            color: #f39c12;
            font-weight: bold;
        }}

        .priority-low {{
            color: #95a5a6;
        }}

        .recommendation-box {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
        }}

        .action-list {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin: 15px 0;
        }}

        .action-list li {{
            margin: 8px 0;
            font-weight: 500;
        }}

        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}

        .metric-card {{
            background: #fff;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            padding: 15px;
            text-align: center;
        }}

        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
        }}

        .metric-label {{
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }}

        .family-card {{
            border: 1px solid #ddd;
            border-radius: 5px;
            margin: 10px 0;
            overflow: hidden;
        }}

        .family-header {{
            background: #f8f9fa;
            padding: 15px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .family-header:hover {{
            background: #e9ecef;
        }}

        .family-members {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }}

        .family-members.expanded {{
            max-height: 2000px;
        }}

        .expand-icon {{
            transition: transform 0.3s ease;
            font-size: 18px;
        }}

        .expand-icon.rotated {{
            transform: rotate(180deg);
        }}

        .member-item {{
            padding: 5px 0;
            border-bottom: 1px solid #e0e0e0;
        }}

        .member-item:last-child {{
            border-bottom: none;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}

            .report-title {{
                font-size: 24px;
            }}

            .section-title {{
                font-size: 20px;
            }}

            table {{
                font-size: 14px;
            }}

            th, td {{
                padding: 8px 6px;
            }}

            .metric-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        @media print {{
            .family-members {{
                max-height: none !important;
            }}
        }}

        /* New styles for enhanced sections */
        .ai-insight-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .ai-insight-title {{
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 8px;
        }}

        .pattern-card {{
            border-left: 4px solid #95a5a6;
            background: #f8f9fa;
            padding: 12px;
            margin: 10px 0;
            border-radius: 4px;
        }}

        .pattern-card.severity-high {{
            border-left-color: #e74c3c;
            background: #ffe4e1;
        }}

        .pattern-card.severity-medium {{
            border-left-color: #f39c12;
            background: #fff3cd;
        }}

        .pattern-card.severity-low {{
            border-left-color: #3498db;
            background: #e8f4f8;
        }}

        .pattern-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 5px;
        }}

        .severity-badge {{
            background: #e74c3c;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
        }}

        .pattern-card.severity-medium .severity-badge {{
            background: #f39c12;
        }}

        .pattern-card.severity-low .severity-badge {{
            background: #3498db;
        }}

        .pattern-implication {{
            color: #555;
            font-size: 14px;
            margin: 5px 0 0 0;
        }}

        .enclave-card {{
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 10px 15px;
            margin: 8px 0;
            border-radius: 4px;
        }}

        .mixed-area-card {{
            background: #fff3cd;
            border-left: 4px solid #f39c12;
            padding: 10px 15px;
            margin: 8px 0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="report-header">
        <div class="report-title">ELECTION INSIGHTS REPORT</div>
        <div class="station-info">{self.station_name}</div>
        <div class="station-info">Pattathanam Assembly Constituency, Kollam District, Kerala</div>
        <div class="station-info">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        <div class="station-info">Total Voters Analyzed: {self.total_voters:,} | Polling Area: {self.station_name}</div>
    </div>

    {''.join(sections)}

    <script>
        function toggleFamily(id) {{
            const element = document.getElementById(id);
            const icon = document.getElementById('icon' + id.replace('family', ''));

            if (element.classList.contains('expanded')) {{
                element.classList.remove('expanded');
                icon.classList.remove('rotated');
            }} else {{
                element.classList.add('expanded');
                icon.classList.add('rotated');
            }}
        }}
    </script>
</body>
</html>"""

        return html

    def save_report(self, output_path: Path):
        """Generate and save the report"""
        html = self.generate_full_report()

        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save HTML
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        # Also save influential households data as JSON
        top_families = self.household_analyzer.get_top_influential_households(top_n=10)
        json_path = output_path.parent / 'influential_households.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(top_families, f, indent=2, ensure_ascii=False)

        return output_path