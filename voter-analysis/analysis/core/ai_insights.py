"""
AI-Powered Insights Generator using Azure OpenAI
Generates data-driven insights from demographic analysis
"""

import os
from typing import Dict, List, Optional
import pandas as pd
from openai import AzureOpenAI


class AIInsightsGenerator:
    """Generate AI-powered insights using Azure OpenAI"""

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None,
                 deployment_name: Optional[str] = None, api_version: Optional[str] = None):
        """
        Initialize Azure OpenAI client

        Args:
            api_key: Azure OpenAI API key (or set AZURE_OPENAI_KEY env var)
            endpoint: Azure OpenAI endpoint (or set AZURE_OPENAI_ENDPOINT env var)
            deployment_name: Deployment name (or set AZURE_OPENAI_DEPLOYMENT env var)
            api_version: API version (or set AZURE_OPENAI_API_VERSION env var)
        """
        # Try to load from config file first
        config_file = os.path.join(os.path.dirname(__file__), '../../../config.json')
        config_file = os.path.abspath(config_file)
        if os.path.exists(config_file):
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
                azure_config = config.get('azure_openai', {})
                self.api_key = api_key or azure_config.get('subscription_key') or os.getenv('AZURE_OPENAI_KEY')
                self.endpoint = endpoint or azure_config.get('endpoint') or os.getenv('AZURE_OPENAI_ENDPOINT')
                self.deployment_name = deployment_name or azure_config.get('deployment') or os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
                self.api_version = api_version or azure_config.get('api_version') or os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
        else:
            self.api_key = api_key or os.getenv('AZURE_OPENAI_KEY')
            self.endpoint = endpoint or os.getenv('AZURE_OPENAI_ENDPOINT')
            self.deployment_name = deployment_name or os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
            self.api_version = api_version or os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')

        if not self.api_key or not self.endpoint:
            raise ValueError(
                "Azure OpenAI credentials not provided. "
                "Set credentials in config.json or environment variables."
            )

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )

    def generate_religious_demographic_insight(self, religion_data: Dict) -> str:
        """
        Generate AI insight for religious demographics

        Args:
            religion_data: Dict with religion counts and percentages

        Returns:
            AI-generated insight string
        """
        prompt = f"""You are an election data analyst. Analyze this religious demographic data and provide a concise, data-driven strategic insight (2-3 sentences max):

Religious Composition:
{self._format_religion_data(religion_data)}

Provide:
1. What the demographic balance tells us about electoral dynamics
2. One specific, actionable strategic observation based on these numbers
3. Any notable patterns or considerations

Be specific, data-driven, and avoid generic advice like "conduct meetings". Focus on what the DATA reveals."""

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert election data analyst who provides concise, data-driven insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    def generate_age_demographic_insight(self, age_data: Dict) -> str:
        """
        Generate AI insight for age demographics

        Args:
            age_data: Dict with age distribution and statistics

        Returns:
            AI-generated insight string
        """
        prompt = f"""Analyze this age demographic data and provide a concise strategic insight (2-3 sentences):

Age Distribution:
{self._format_age_data(age_data)}

Focus on:
1. Which age groups offer the most strategic value
2. Specific demographic advantages or challenges
3. Data-driven observations about generational dynamics

Be specific and data-focused."""

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert election data analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    def generate_gender_insight(self, gender_data: Dict) -> str:
        """
        Generate AI insight for gender demographics

        Args:
            gender_data: Dict with gender counts and gap analysis

        Returns:
            AI-generated insight string
        """
        prompt = f"""Analyze this gender demographic data and provide a concise strategic insight (2-3 sentences):

Gender Distribution:
Male: {gender_data.get('male_voters', 0):,} ({gender_data.get('male_percentage', 0)}%)
Female: {gender_data.get('female_voters', 0):,} ({gender_data.get('female_percentage', 0)}%)
Gender Gap: {gender_data.get('gender_gap', 0):,} voters

Middle-aged women (30-50): {gender_data.get('middle_aged_women_count', 0):,} ({gender_data.get('middle_aged_women_percentage', 0)}% of electorate)

Provide data-driven observations about gender dynamics and their electoral significance."""

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert election data analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    def generate_household_insight(self, household_stats: Dict, large_households: List) -> str:
        """
        Generate AI insight for household patterns

        Args:
            household_stats: Dict with household statistics
            large_households: List of large household data

        Returns:
            AI-generated insight string
        """
        prompt = f"""Analyze this household data and provide a concise strategic insight (2-3 sentences):

Household Statistics:
- Total households: {household_stats.get('total_households', 0):,}
- Average household size: {household_stats.get('average_household_size', 0)} voters
- Large households (5+ voters): {len(large_households)}
- Very large households (10+ voters): {household_stats.get('household_size_distribution', {}).get('very_large_10_plus', 0)}

Largest household size: {max([h.get('Voters', 0) for h in large_households[:5]]) if large_households else 0} voters

Provide data-driven observations about household voting patterns and their strategic value."""

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert election data analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    def generate_cross_demographic_insight(self, cross_data: Dict) -> str:
        """
        Generate AI insight for cross-demographic patterns

        Args:
            cross_data: Dict with cross-tabulated demographic data

        Returns:
            AI-generated insight string
        """
        prompt = f"""Analyze this cross-demographic data and identify key patterns (2-3 sentences):

{self._format_cross_data(cross_data)}

Identify:
1. Notable demographic intersections
2. Strategic advantages or vulnerabilities
3. Unexpected patterns in the data

Be specific and data-focused."""

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert election data analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    def generate_geographic_insight(self, geographic_data: Dict) -> str:
        """
        Generate AI insight for geographic/regional patterns

        Args:
            geographic_data: Dict with regional clustering data

        Returns:
            AI-generated insight string
        """
        prompt = f"""Analyze this geographic distribution data and provide insights (2-3 sentences):

{self._format_geographic_data(geographic_data)}

Identify:
1. Geographic concentration patterns
2. Regional religious or demographic clusters
3. Strategic implications of spatial distribution

Be specific and data-focused."""

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert election data analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    def generate_anomaly_insight(self, anomalies: List[Dict]) -> str:
        """
        Generate AI insight for detected anomalies

        Args:
            anomalies: List of detected anomalies

        Returns:
            AI-generated insight string
        """
        if not anomalies:
            return "No significant anomalies detected in the demographic patterns."

        prompt = f"""Analyze these demographic anomalies and explain their significance (2-3 sentences):

Detected Anomalies:
{self._format_anomalies(anomalies)}

Explain what these outliers reveal about the electorate and their strategic implications."""

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert election data analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    def generate_comprehensive_strategy_insight(self, all_data: Dict) -> str:
        """
        Generate comprehensive strategic insight combining all demographic data

        Args:
            all_data: Dict containing all demographic analyses

        Returns:
            AI-generated comprehensive insight string
        """
        prompt = f"""Based on this complete demographic analysis, provide a comprehensive strategic assessment (3-4 sentences):

{self._format_comprehensive_data(all_data)}

Provide:
1. Overall electoral landscape assessment
2. Top 2-3 strategic priorities based on the data
3. Key demographic leverage points
4. One critical warning or consideration

Be specific, data-driven, and actionable."""

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": "You are an expert election strategist analyzing demographic data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )

        return response.choices[0].message.content.strip()

    # Helper methods for formatting data

    def _format_religion_data(self, data: Dict) -> str:
        """Format religion data for prompt"""
        lines = []
        for religion, info in data.items():
            count = info.get('count', 0)
            pct = info.get('percentage', 0)
            lines.append(f"- {religion}: {count:,} ({pct}%)")
        return "\n".join(lines)

    def _format_age_data(self, data: Dict) -> str:
        """Format age data for prompt"""
        lines = []
        for age_group, info in data.get('distribution', {}).items():
            count = info.get('count', 0)
            pct = info.get('percentage', 0)
            lines.append(f"- {age_group}: {count:,} ({pct}%)")
        return "\n".join(lines)

    def _format_cross_data(self, data: Dict) -> str:
        """Format cross-demographic data for prompt"""
        lines = []
        for key, value in data.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines[:10])  # Limit to top 10 entries

    def _format_geographic_data(self, data: Dict) -> str:
        """Format geographic data for prompt"""
        lines = []
        for key, value in data.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines[:10])

    def _format_anomalies(self, anomalies: List[Dict]) -> str:
        """Format anomaly data for prompt"""
        lines = []
        for i, anomaly in enumerate(anomalies[:5], 1):  # Top 5 anomalies
            lines.append(f"{i}. {anomaly.get('description', 'Unknown anomaly')}")
        return "\n".join(lines)

    def _format_comprehensive_data(self, data: Dict) -> str:
        """Format comprehensive data for prompt"""
        lines = []

        # Religion summary
        if 'religion' in data:
            lines.append(f"Religion: {data['religion'].get('summary', 'N/A')}")

        # Age summary
        if 'age' in data:
            lines.append(f"Age: {data['age'].get('summary', 'N/A')}")

        # Gender summary
        if 'gender' in data:
            lines.append(f"Gender: {data['gender'].get('summary', 'N/A')}")

        # Household summary
        if 'household' in data:
            lines.append(f"Households: {data['household'].get('summary', 'N/A')}")

        return "\n".join(lines)


def test_ai_insights():
    """Test the AI insights generator with sample data"""
    # This requires Azure OpenAI credentials to be set
    try:
        generator = AIInsightsGenerator()

        # Test with sample religion data
        religion_data = {
            'Hindu': {'count': 575, 'percentage': 77.7},
            'Christian': {'count': 137, 'percentage': 18.5},
            'Muslim': {'count': 28, 'percentage': 3.8}
        }

        print("Generating religious demographic insight...")
        insight = generator.generate_religious_demographic_insight(religion_data)
        print(f"Insight: {insight}\n")

        return True
    except ValueError as e:
        print(f"Error: {e}")
        print("\nTo use AI insights, set these environment variables:")
        print("  export AZURE_OPENAI_KEY='your-api-key'")
        print("  export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com/'")
        print("  export AZURE_OPENAI_DEPLOYMENT='your-deployment-name'")
        return False


if __name__ == "__main__":
    test_ai_insights()
