"""
HTML Report Generator for Polling Station Analysis
Creates comprehensive, formatted HTML reports with charts and tables
"""

import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class ReportGenerator:
    """Generate HTML reports for polling station analysis"""

    def __init__(self, analysis_results: Dict, output_dir: str):
        self.analysis = analysis_results
        self.output_dir = Path(output_dir)
        self.charts = []

    def generate_html_report(self) -> str:
        """Generate complete HTML report"""
        # Extract metadata
        metadata = self.analysis.get('metadata', {})
        ward_name = metadata.get('ward_name', 'Unknown Ward')
        station_name = metadata.get('station_name', 'Unknown Station')
        total_voters = metadata.get('total_voters', 0)

        # Generate charts
        self._create_all_charts()

        # Build HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ward_name} - {station_name} - Voter Analysis Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header h2 {{
            margin: 10px 0;
            font-size: 1.5em;
            opacity: 0.9;
        }}
        .header .stats {{
            margin-top: 20px;
            display: flex;
            justify-content: center;
            gap: 30px;
        }}
        .header .stat {{
            text-align: center;
        }}
        .header .stat-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        .header .stat-label {{
            font-size: 0.9em;
            opacity: 0.8;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .section {{
            background: white;
            margin: 20px 0;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h3 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }}
        .stat-card .label {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 5px;
        }}
        .stat-card .value {{
            color: #333;
            font-size: 1.5em;
            font-weight: bold;
        }}
        .chart-container {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .characteristics {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 20px 0;
        }}
        .characteristic {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
        @media print {{
            .section {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
"""

        # Header
        html += self._generate_header()

        # Main container
        html += '<div class="container">'

        # Executive Summary
        html += self._generate_executive_summary()

        # Demographics Section
        html += self._generate_demographics_section()

        # Family Analysis Section
        html += self._generate_family_section()

        # Electoral Insights Section
        html += self._generate_electoral_section()

        # Unique Characteristics
        html += self._generate_characteristics_section()

        # Data Quality Section
        html += self._generate_data_quality_section()

        # Charts Section
        html += self._generate_charts_section()

        # Close container
        html += '</div>'

        # Footer
        html += self._generate_footer()

        # Close HTML
        html += """
</body>
</html>
"""
        return html

    def _generate_header(self) -> str:
        """Generate report header"""
        metadata = self.analysis.get('metadata', {})
        demo = self.analysis.get('demographics', {}).get('basic_stats', {})

        total_voters = metadata.get('total_voters', 0)
        gender_dist = demo.get('gender_distribution', {})
        male_count = gender_dist.get('male_count', 0)
        female_count = gender_dist.get('female_count', 0)

        return f"""
    <div class="header">
        <h1>{metadata.get('ward_name', 'Unknown Ward')}</h1>
        <h2>{metadata.get('station_name', 'Unknown Station')}</h2>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{total_voters:,}</div>
                <div class="stat-label">Total Voters</div>
            </div>
            <div class="stat">
                <div class="stat-value">{male_count:,}</div>
                <div class="stat-label">Male Voters</div>
            </div>
            <div class="stat">
                <div class="stat-value">{female_count:,}</div>
                <div class="stat-label">Female Voters</div>
            </div>
        </div>
    </div>
"""

    def _generate_executive_summary(self) -> str:
        """Generate executive summary section"""
        demo = self.analysis.get('demographics', {}).get('basic_stats', {})
        family = self.analysis.get('family_analysis', {})

        html = """
    <div class="section">
        <h3>Executive Summary</h3>
        <div class="stats-grid">
"""

        # Key metrics
        if 'age_statistics' in demo:
            age_stats = demo['age_statistics']
            html += f"""
            <div class="stat-card">
                <div class="label">Average Age</div>
                <div class="value">{age_stats.get('mean_age', 'N/A')} years</div>
            </div>
"""

        if 'religion_distribution' in demo:
            religion = demo['religion_distribution']
            html += f"""
            <div class="stat-card">
                <div class="label">Religious Diversity</div>
                <div class="value">{religion.get('diversity_index', 0):.3f}</div>
            </div>
"""

        if 'household_analysis' in family:
            households = family['household_analysis']
            html += f"""
            <div class="stat-card">
                <div class="label">Total Houses</div>
                <div class="value">{households.get('total_houses', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="label">Avg Household Size</div>
                <div class="value">{households.get('average_household_size', 0)}</div>
            </div>
"""

        html += """
        </div>
    </div>
"""
        return html

    def _generate_demographics_section(self) -> str:
        """Generate demographics section"""
        demo = self.analysis.get('demographics', {}).get('basic_stats', {})

        html = """
    <div class="section">
        <h3>Demographic Profile</h3>
"""

        # Age Distribution
        if 'age_statistics' in demo:
            age_stats = demo['age_statistics']
            if 'age_group_percentages' in age_stats:
                age_groups = age_stats['age_group_percentages']
                html += """
        <h4>Age Distribution</h4>
        <table>
            <tr>
                <th>Age Group</th>
                <th>Percentage</th>
            </tr>
"""
                for group, label in [('youth_18_30', 'Youth (18-30)'),
                                    ('middle_31_60', 'Middle Age (31-60)'),
                                    ('senior_60_plus', 'Senior (60+)')]:
                    html += f"""
            <tr>
                <td>{label}</td>
                <td>{age_groups.get(group, 0)}%</td>
            </tr>
"""
                html += "</table>"

        # Religion Distribution
        if 'religion_distribution' in demo:
            religion = demo['religion_distribution']
            if 'percentages' in religion:
                percentages = religion['percentages']
                html += """
        <h4>Religious Composition</h4>
        <table>
            <tr>
                <th>Religion</th>
                <th>Percentage</th>
            </tr>
"""
                for rel, label in [('hindu_percentage', 'Hindu'),
                                  ('christian_percentage', 'Christian'),
                                  ('muslim_percentage', 'Muslim')]:
                    html += f"""
            <tr>
                <td>{label}</td>
                <td>{percentages.get(rel, 0)}%</td>
            </tr>
"""
                html += "</table>"

        html += "</div>"
        return html

    def _generate_family_section(self) -> str:
        """Generate family analysis section"""
        family = self.analysis.get('family_analysis', {})

        html = """
    <div class="section">
        <h3>Family & Household Analysis</h3>
"""

        if 'household_analysis' in family:
            households = family['household_analysis']
            if 'size_percentages' in households:
                sizes = households['size_percentages']
                html += """
        <h4>Household Size Distribution</h4>
        <table>
            <tr>
                <th>Household Size</th>
                <th>Percentage</th>
            </tr>
"""
                for size, label in [('single_person', 'Single Person'),
                                   ('couple_2', 'Couple (2)'),
                                   ('small_family_3_4', 'Small Family (3-4)'),
                                   ('medium_family_5_6', 'Medium Family (5-6)'),
                                   ('large_family_7_plus', 'Large Family (7+)')]:
                    html += f"""
            <tr>
                <td>{label}</td>
                <td>{sizes.get(size, 0)}%</td>
            </tr>
"""
                html += "</table>"

        html += "</div>"
        return html

    def _generate_electoral_section(self) -> str:
        """Generate electoral insights section"""
        electoral = self.analysis.get('demographics', {}).get('electoral_insights', {})

        html = """
    <div class="section">
        <h3>Electoral Insights</h3>
"""

        # First-time voters
        if 'first_time_voters' in electoral:
            ftv = electoral['first_time_voters']
            html += f"""
        <div class="stat-card">
            <div class="label">First-Time Voters (18-21)</div>
            <div class="value">{ftv.get('count', 0)} ({ftv.get('percentage', 0)}%)</div>
        </div>
"""

        # Senior voters
        if 'senior_voters' in electoral:
            sv = electoral['senior_voters']
            html += f"""
        <div class="stat-card">
            <div class="label">Senior Voters (65+)</div>
            <div class="value">{sv.get('count', 0)} ({sv.get('percentage', 0)}%)</div>
        </div>
"""

        # Vote banks
        if 'vote_banks' in electoral:
            vote_banks = electoral['vote_banks']
            if vote_banks:
                html += "<h4>Identified Vote Banks</h4><ul>"
                for vb in vote_banks:
                    html += f"<li>{vb.get('group')}: {vb.get('size')} voters ({vb.get('percentage')}%)</li>"
                html += "</ul>"

        html += "</div>"
        return html

    def _generate_characteristics_section(self) -> str:
        """Generate unique characteristics section"""
        characteristics = self.analysis.get('unique_characteristics', {})

        if not characteristics:
            return ""

        html = """
    <div class="section">
        <h3>Unique Characteristics</h3>
        <div class="characteristics">
"""
        for key, value in characteristics.items():
            html += f'<div class="characteristic">{value}</div>'

        html += """
        </div>
    </div>
"""
        return html

    def _generate_data_quality_section(self) -> str:
        """Generate data quality section"""
        quality = self.analysis.get('data_quality', {})

        html = f"""
    <div class="section">
        <h3>Data Quality Assessment</h3>
        <div class="stat-card">
            <div class="label">Quality Score</div>
            <div class="value">{quality.get('quality_score', 0)}% - {quality.get('quality_grade', 'N/A')}</div>
        </div>
"""

        if 'issues' in quality and quality['issues']:
            html += "<h4>Identified Issues</h4><ul>"
            for issue in quality['issues']:
                html += f"<li>{issue}</li>"
            html += "</ul>"

        html += "</div>"
        return html

    def _generate_charts_section(self) -> str:
        """Generate charts section with all visualizations"""
        html = """
    <div class="section">
        <h3>Visual Analytics</h3>
"""
        for i, chart in enumerate(self.charts):
            html += f'<div id="chart_{i}" class="chart-container"></div>'

        html += "</div>"

        # Add chart scripts
        html += "<script>"
        for i, chart in enumerate(self.charts):
            html += f"Plotly.newPlot('chart_{i}', {chart});"
        html += "</script>"

        return html

    def _generate_footer(self) -> str:
        """Generate report footer"""
        return f"""
    <div class="footer">
        <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        <p>Kerala Voter Analysis System - Polling Station Report</p>
    </div>
"""

    def _create_all_charts(self):
        """Create all charts for the report"""
        # Population Pyramid
        pyramid_data = self.analysis.get('demographics', {}).get('population_pyramid', {})
        if 'age_groups' in pyramid_data:
            self._create_population_pyramid(pyramid_data)

        # Religion Pie Chart
        religion_data = self.analysis.get('demographics', {}).get('basic_stats', {}).get('religion_distribution', {})
        if 'distribution' in religion_data:
            self._create_religion_pie_chart(religion_data['distribution'])

        # Age Distribution Histogram
        age_stats = self.analysis.get('demographics', {}).get('basic_stats', {}).get('age_statistics', {})
        if 'age_groups' in age_stats:
            self._create_age_histogram(age_stats['age_groups'])

    def _create_population_pyramid(self, data: Dict):
        """Create population pyramid chart"""
        if 'error' in data:
            return

        fig = go.Figure()

        # Male bars (negative for pyramid effect)
        fig.add_trace(go.Bar(
            y=data['age_groups'],
            x=[-v for v in data['male']],
            name='Male',
            orientation='h',
            marker=dict(color='lightblue')
        ))

        # Female bars
        fig.add_trace(go.Bar(
            y=data['age_groups'],
            x=data['female'],
            name='Female',
            orientation='h',
            marker=dict(color='pink')
        ))

        fig.update_layout(
            title='Population Pyramid',
            barmode='relative',
            bargap=0.1,
            xaxis=dict(title='Population'),
            yaxis=dict(title='Age Group'),
            height=400
        )

        self.charts.append(fig.to_json())

    def _create_religion_pie_chart(self, data: Dict):
        """Create religion distribution pie chart"""
        labels = list(data.keys())
        values = list(data.values())

        fig = go.Figure(data=[go.Pie(
            labels=[l.capitalize() for l in labels],
            values=values,
            hole=0.3
        )])

        fig.update_layout(
            title='Religious Distribution',
            height=400
        )

        self.charts.append(fig.to_json())

    def _create_age_histogram(self, data: Dict):
        """Create age distribution histogram"""
        categories = []
        values = []

        for key, value in data.items():
            if key.startswith('youth'):
                categories.append('Youth (18-30)')
            elif key.startswith('middle'):
                categories.append('Middle (31-60)')
            elif key.startswith('senior'):
                categories.append('Senior (60+)')
            elif key.startswith('first_time'):
                categories.append('First Time (18-21)')
            elif key.startswith('elderly'):
                categories.append('Elderly (65+)')
            else:
                continue
            values.append(value)

        fig = go.Figure(data=[go.Bar(
            x=categories,
            y=values,
            marker_color='#667eea'
        )])

        fig.update_layout(
            title='Age Group Distribution',
            xaxis_title='Age Group',
            yaxis_title='Number of Voters',
            height=400
        )

        self.charts.append(fig.to_json())

    def save_report(self, filename: str = "report.html"):
        """Save HTML report to file"""
        report_html = self.generate_html_report()
        output_path = self.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_html)

        print(f"Report saved to {output_path}")
        return output_path