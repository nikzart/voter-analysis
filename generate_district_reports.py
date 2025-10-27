#!/usr/bin/env python3
"""
Generate separate comprehensive reports for each polling district
"""
import pandas as pd
from datetime import datetime

def generate_district_report(district_name, df, filename):
    """Generate comprehensive report for a single district"""
    
    # Calculate all statistics
    total = len(df)
    male = len(df[df['Gender'] == 'M'])
    female = len(df[df['Gender'] == 'F'])
    hindu = len(df[df['Religion'] == 'Hindu'])
    muslim = len(df[df['Religion'] == 'Muslim'])
    christian = len(df[df['Religion'] == 'Christian'])
    
    avg_age = df['Age'].mean()
    median_age = df['Age'].median()
    
    # Age groups
    age_18_25 = len(df[(df['Age'] >= 18) & (df['Age'] <= 25)])
    age_26_35 = len(df[(df['Age'] >= 26) & (df['Age'] <= 35)])
    age_36_45 = len(df[(df['Age'] >= 36) & (df['Age'] <= 45)])
    age_46_55 = len(df[(df['Age'] >= 46) & (df['Age'] <= 55)])
    age_56_65 = len(df[(df['Age'] >= 56) & (df['Age'] <= 65)])
    age_66_plus = len(df[df['Age'] >= 66])
    
    # Religion by age
    hindu_df = df[df['Religion'] == 'Hindu']
    muslim_df = df[df['Religion'] == 'Muslim']
    christian_df = df[df['Religion'] == 'Christian']
    
    hindu_avg_age = hindu_df['Age'].mean() if len(hindu_df) > 0 else 0
    muslim_avg_age = muslim_df['Age'].mean() if len(muslim_df) > 0 else 0
    christian_avg_age = christian_df['Age'].mean() if len(christian_df) > 0 else 0
    
    hindu_young = len(hindu_df[hindu_df['Age'] <= 35]) if len(hindu_df) > 0 else 0
    muslim_young = len(muslim_df[muslim_df['Age'] <= 35]) if len(muslim_df) > 0 else 0
    christian_young = len(christian_df[christian_df['Age'] <= 35]) if len(christian_df) > 0 else 0
    
    hindu_middle = len(hindu_df[(hindu_df['Age'] >= 36) & (hindu_df['Age'] <= 55)]) if len(hindu_df) > 0 else 0
    muslim_middle = len(muslim_df[(muslim_df['Age'] >= 36) & (muslim_df['Age'] <= 55)]) if len(muslim_df) > 0 else 0
    christian_middle = len(christian_df[(christian_df['Age'] >= 36) & (christian_df['Age'] <= 55)]) if len(christian_df) > 0 else 0
    
    hindu_senior = len(hindu_df[hindu_df['Age'] >= 56]) if len(hindu_df) > 0 else 0
    muslim_senior = len(muslim_df[muslim_df['Age'] >= 56]) if len(muslim_df) > 0 else 0
    christian_senior = len(christian_df[christian_df['Age'] >= 56]) if len(christian_df) > 0 else 0
    
    # Gender by religion
    hindu_female = len(hindu_df[hindu_df['Gender'] == 'F']) if len(hindu_df) > 0 else 0
    muslim_female = len(muslim_df[muslim_df['Gender'] == 'F']) if len(muslim_df) > 0 else 0
    christian_female = len(christian_df[christian_df['Gender'] == 'F']) if len(christian_df) > 0 else 0
    
    hindu_male = len(hindu_df[hindu_df['Gender'] == 'M']) if len(hindu_df) > 0 else 0
    muslim_male = len(muslim_df[muslim_df['Gender'] == 'M']) if len(muslim_df) > 0 else 0
    christian_male = len(christian_df[christian_df['Gender'] == 'M']) if len(christian_df) > 0 else 0
    
    # Key demographics
    middle_aged_women = len(df[(df['Gender'] == 'F') & (df['Age'] >= 30) & (df['Age'] <= 50)])
    young_voters = age_18_25 + age_26_35
    senior_citizens = len(df[df['Age'] >= 60])
    first_time_voters = len(df[(df['Age'] >= 18) & (df['Age'] <= 21)])
    
    # Households
    households = df.groupby('OldWard No/ House No.').size()
    large_households = households[households >= 5]
    very_large_households = households[households >= 8]
    
    # Religious homogeneity
    household_religion = df.groupby('OldWard No/ House No.')['Religion'].apply(lambda x: x.nunique())
    homogeneous_households = len(household_religion[household_religion == 1])
    mixed_households = len(household_religion[household_religion > 1])
    
    # Influential families
    guardians = df["Guardian's Name"].value_counts()
    top_families = guardians[guardians >= 3]
    top_10_families = guardians[guardians >= 3].head(10)
    
    # Determine district type
    hindu_pct = hindu/total*100
    if hindu_pct > 70:
        district_type = "Hindu-Majority District"
        strategic_classification = "SAFE BASE"
    elif 40 < hindu_pct < 70:
        district_type = "Diverse District"
        strategic_classification = "SWING ZONE"
    else:
        district_type = "Minority-Significant District"
        strategic_classification = "COALITION REQUIRED"
    
    # Build report
    lines = []
    lines.append(f'# ELECTION INSIGHTS REPORT')
    lines.append(f'## {district_name}')
    lines.append(f'### Pattathanam Assembly Constituency, Kollam District, Kerala')
    lines.append('')
    lines.append(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'**Total Voters Analyzed:** {total:,}')
    lines.append(f'**Polling Area:** {district_name}')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## EXECUTIVE SUMMARY')
    lines.append('')
    lines.append('### Overall Composition')
    lines.append('')
    lines.append(f'**Total Electorate:** {total:,} voters')
    lines.append('')
    lines.append('| Metric | Count | Percentage |')
    lines.append('|--------|-------|------------|')
    lines.append(f'| Male Voters | {male:,} | {male/total*100:.1f}% |')
    lines.append(f'| Female Voters | {female:,} | {female/total*100:.1f}% |')
    lines.append(f'| Hindu | {hindu:,} | {hindu/total*100:.1f}% |')
    lines.append(f'| Muslim | {muslim:,} | {muslim/total*100:.1f}% |')
    lines.append(f'| Christian | {christian:,} | {christian/total*100:.1f}% |')
    lines.append('')
    lines.append(f'**Average Age:** {avg_age:.1f} years (Median: {median_age:.0f} years)')
    lines.append('')
    lines.append('### Critical Finding')
    lines.append('')
    lines.append(f'**This is a {district_type.lower()}** with {hindu/total*100:.1f}% Hindu voters.')
    
    if hindu_pct > 70:
        lines.append(f'Strong Hindu majority provides solid base, but coalition-building recommended to ensure victory.')
    elif 40 < hindu_pct < 70:
        lines.append(f'Diverse religious composition requires careful coalition-building for electoral success.')
    else:
        lines.append(f'Significant minority presence demands inclusive messaging and broad alliances.')
    
    lines.append('')
    lines.append(f'**Classification:** {strategic_classification}')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 1. RELIGIOUS DEMOGRAPHICS & STRATEGIC IMPLICATIONS')
    lines.append('')
    lines.append('### 1.1 Religious Composition')
    lines.append('')
    lines.append('| Religion | Male | Female | Total | % of District |')
    lines.append('|----------|------|--------|-------|---------------|')
    lines.append(f'| Hindu | {hindu_male:,} | {hindu_female:,} | {hindu:,} | {hindu/total*100:.1f}% |')
    lines.append(f'| Muslim | {muslim_male:,} | {muslim_female:,} | {muslim:,} | {muslim/total*100:.1f}% |')
    lines.append(f'| Christian | {christian_male:,} | {christian_female:,} | {christian:,} | {christian/total*100:.1f}% |')
    lines.append('')
    lines.append('**Strategic Insight:**')
    
    if hindu_pct > 70:
        lines.append(f'- Strong Hindu base ({hindu_pct:.1f}%) provides foundation')
        lines.append(f'- Need {50 - hindu_pct:.1f}% from minorities to cross 50% mark if Hindu vote splits')
        lines.append(f'- Focus on consolidating Hindu vote while maintaining minority goodwill')
    elif muslim/total*100 > 20:
        lines.append(f'- Significant Muslim population ({muslim/total*100:.1f}%) is key to coalition')
        lines.append(f'- Hindu vote ({hindu_pct:.1f}%) alone insufficient for victory')
        lines.append(f'- Secular messaging and minority outreach essential')
    elif christian/total*100 > 20:
        lines.append(f'- Strong Christian presence ({christian/total*100:.1f}%) makes them kingmakers')
        lines.append(f'- Church relations and Christian institutional support critical')
        lines.append(f'- Balanced approach to Hindu and Christian communities needed')
    else:
        lines.append(f'- Balanced three-way split requires sophisticated coalition-building')
        lines.append(f'- Development messaging over identity politics')
        lines.append(f'- All communities must be engaged')
    
    lines.append('')
    lines.append('### 1.2 Age Profiles by Religion')
    lines.append('')
    lines.append('| Religion | Avg Age | Young (≤35) | Middle (36-55) | Senior (56+) |')
    lines.append('|----------|---------|-------------|----------------|--------------|')
    lines.append(f'| **Hindu** | {hindu_avg_age:.1f} yrs | {hindu_young:,} ({hindu_young/hindu*100 if hindu > 0 else 0:.1f}%) | {hindu_middle:,} ({hindu_middle/hindu*100 if hindu > 0 else 0:.1f}%) | {hindu_senior:,} ({hindu_senior/hindu*100 if hindu > 0 else 0:.1f}%) |')
    lines.append(f'| **Muslim** | {muslim_avg_age:.1f} yrs | {muslim_young:,} ({muslim_young/muslim*100 if muslim > 0 else 0:.1f}%) | {muslim_middle:,} ({muslim_middle/muslim*100 if muslim > 0 else 0:.1f}%) | {muslim_senior:,} ({muslim_senior/muslim*100 if muslim > 0 else 0:.1f}%) |')
    lines.append(f'| **Christian** | {christian_avg_age:.1f} yrs | {christian_young:,} ({christian_young/christian*100 if christian > 0 else 0:.1f}%) | {christian_middle:,} ({christian_middle/christian*100 if christian > 0 else 0:.1f}%) | {christian_senior:,} ({christian_senior/christian*100 if christian > 0 else 0:.1f}%) |')
    lines.append('')
    
    # Determine youngest community
    ages = [(hindu_avg_age, 'Hindu', hindu), (muslim_avg_age, 'Muslim', muslim), (christian_avg_age, 'Christian', christian)]
    ages_sorted = sorted([a for a in ages if a[2] > 0], key=lambda x: x[0])
    
    if len(ages_sorted) > 0:
        youngest = ages_sorted[0][1]
        oldest = ages_sorted[-1][1]
        lines.append('**Strategic Insight:**')
        lines.append(f'- **{youngest} community is youngest** (avg {ages_sorted[0][0]:.1f} years) → More open to change, digital-savvy')
        lines.append(f'- **{oldest} community is oldest** (avg {ages_sorted[-1][0]:.1f} years) → Traditional loyalties stronger')
    
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 2. AGE-BASED ANALYSIS & GENERATIONAL STRATEGY')
    lines.append('')
    lines.append('### 2.1 Age Distribution')
    lines.append('')
    lines.append('| Age Group | Total | Percentage | Strategic Priority |')
    lines.append('|-----------|-------|------------|-------------------|')
    lines.append(f'| **18-25** (First-time + Early voters) | {age_18_25:,} | {age_18_25/total*100:.1f}% | {"CRITICAL" if age_18_25/total > 0.08 else "HIGH"} - Malleable, high energy |')
    lines.append(f'| **26-35** (Young professionals) | {age_26_35:,} | {age_26_35/total*100:.1f}% | HIGH - Career-focused, aspirational |')
    lines.append(f'| **36-45** (Established families) | {age_36_45:,} | {age_36_45/total*100:.1f}% | HIGHEST - Decision-makers |')
    lines.append(f'| **46-55** (Peak earning) | {age_46_55:,} | {age_46_55/total*100:.1f}% | HIGHEST - Stable voters |')
    lines.append(f'| **56-65** (Pre-retirement) | {age_56_65:,} | {age_56_65/total*100:.1f}% | HIGH - High turnout |')
    lines.append(f'| **66+** (Senior citizens) | {age_66_plus:,} | {age_66_plus/total*100:.1f}% | MEDIUM - Loyal voters |')
    lines.append('')
    lines.append('**Critical Insight:**')
    
    middle_aged_pct = (age_36_45 + age_46_55)/total*100
    lines.append(f'- **{middle_aged_pct:.1f}% of voters are in 36-55 age bracket** - This is your PRIMARY TARGET')
    lines.append(f'- {"Only" if age_18_25/total < 0.08 else "Significant"} {age_18_25/total*100:.1f}% are youth (18-25) - {"Mature electorate" if age_18_25/total < 0.08 else "Youth engagement matters"}')
    lines.append(f'- Average age {avg_age:.1f} means **{"development over disruption" if avg_age > 45 else "balance tradition and change"}**')
    lines.append('')
    lines.append(f'**First-time voters (18-21):** {first_time_voters:,} ({first_time_voters/total*100:.1f}% of electorate)')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 3. GENDER ANALYSIS - THE WOMEN VOTE')
    lines.append('')
    lines.append('### 3.1 Overall Gender Split')
    lines.append('')
    lines.append(f'- **Female voters:** {female:,} ({female/total*100:.1f}%)')
    lines.append(f'- **Male voters:** {male:,} ({male/total*100:.1f}%)')
    lines.append('')
    
    gender_diff = abs(female - male)
    if female > male:
        lines.append(f'**Female voters outnumber male voters by {gender_diff:,} votes** - this is a {gender_diff/total*100:.1f}% margin.')
    else:
        lines.append(f'**Male voters outnumber female voters by {gender_diff:,} votes** - this is a {gender_diff/total*100:.1f}% margin.')
    
    lines.append('')
    lines.append('### 3.2 The Critical Demographic: Middle-Aged Women (30-50 years)')
    lines.append('')
    lines.append(f'**Total middle-aged women:** {middle_aged_women:,} ({middle_aged_women/total*100:.1f}% of entire electorate)')
    lines.append('')
    lines.append('**STRATEGIC IMPERATIVE:** This group represents **1 in 4 voters**. They are:')
    lines.append('- Primary household decision-makers')
    lines.append('- Concerned about healthcare, education, safety')
    lines.append('- Influenced by welfare schemes (ration, pension, housing)')
    lines.append('- Often decide how the entire family votes')
    lines.append('')
    lines.append('**Campaign Priority:** Women-centric manifesto promises (self-help groups, healthcare, child education, cooking gas subsidies, safety)')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 4. HOUSEHOLD & FAMILY VOTING BLOCS')
    lines.append('')
    lines.append('### 4.1 Household Size Analysis')
    lines.append('')
    lines.append(f'**Total Unique Households:** {len(households)}')
    lines.append(f'**Average Voters per Household:** {households.mean():.1f}')
    lines.append(f'**Large Households (5+ voters):** {len(large_households)}')
    lines.append(f'**Very Large Households (8+ voters):** {len(very_large_households)}')
    lines.append('')
    lines.append(f'**Strategic Gold Mine:** These {len(large_households)} large households contain approximately **{large_households.sum() if len(large_households) > 0 else 0:,} voters** ({large_households.sum()/total*100 if len(large_households) > 0 and total > 0 else 0:.1f}% of district).')
    lines.append('')
    lines.append('**Winning one influential family member = winning 5-8 votes**')
    lines.append('')
    
    if len(large_households) > 0:
        lines.append('### 4.2 Top 20 Large Households (5+ Voters)')
        lines.append('')
        lines.append('| Household Address | Voters | Religion (Majority) |')
        lines.append('|-------------------|--------|---------------------|')
        for address, count in large_households.head(20).items():
            household_voters = df[df['OldWard No/ House No.'] == address]
            dominant_religion = household_voters['Religion'].mode()[0] if len(household_voters) > 0 else 'Unknown'
            lines.append(f'| {address} | {count} | {dominant_religion} |')
        lines.append('')
    
    lines.append('### 4.3 Religious Homogeneity of Households')
    lines.append('')
    lines.append(f'- **Religiously homogeneous households:** {homogeneous_households} ({homogeneous_households/(homogeneous_households+mixed_households)*100:.1f}%)')
    lines.append(f'- **Mixed religion households:** {mixed_households} ({mixed_households/(homogeneous_households+mixed_households)*100:.1f}%)')
    lines.append('')
    lines.append('**Key Finding:**')
    
    if homogeneous_households/(homogeneous_households+mixed_households) > 0.75:
        lines.append('- Majority of households are religiously homogeneous → **community-specific messaging works**')
    else:
        lines.append('- Significant mixed households → **secular messaging has audience**')
    
    lines.append(f'- Mixed households ({mixed_households}) represent potential for **inclusive/secular messaging**')
    lines.append('')
    
    if len(top_10_families) > 0:
        lines.append('### 4.4 Top 10 Influential Family Blocs')
        lines.append('')
        lines.append('These families have 3+ registered dependents. Winning the patriarch/matriarch wins the family bloc.')
        lines.append('')
        lines.append('| Guardian Name | Family Members | Strategy |')
        lines.append('|---------------|----------------|----------|')
        for guardian, count in top_10_families.items():
            family_data = df[df["Guardian's Name"] == guardian]
            religion = family_data['Religion'].mode()[0] if len(family_data) > 0 else 'Unknown'
            lines.append(f'| {guardian} | {count} | Personal meeting, {religion} community leader introduction |')
        lines.append('')
        lines.append(f'**Campaign Strategy:** Personal outreach to these families through respected community members. One home visit = multiple votes.')
        lines.append('')
    
    lines.append('---')
    lines.append('')
    lines.append('## 5. WINNING STRATEGY FOR THIS DISTRICT')
    lines.append('')
    
    # Generate winning scenarios based on demographics
    if hindu_pct > 70:
        lines.append('### Scenario: Hindu Consolidation Strategy')
        lines.append('')
        lines.append('**Formula:** Consolidate Hindu base + Minority goodwill')
        lines.append('')
        lines.append('**Requirements:**')
        lines.append(f'- Near-total Hindu consolidation: {hindu} voters (need 75%+ = {int(hindu*0.75)} votes)')
        lines.append(f'- Minority goodwill: {muslim + christian} voters (need 20%+ = {int((muslim + christian)*0.2)} votes)')
        lines.append('')
        lines.append(f'**This gives:** {int(hindu*0.75 + (muslim + christian)*0.2)} votes ({(int(hindu*0.75 + (muslim + christian)*0.2))/total*100:.1f}%)')
        lines.append('')
        lines.append('**Key Actions:**')
        lines.append('1. Temple committees and religious leaders engagement')
        lines.append('2. Cultural events (Onam, Vishu) as campaign platforms')
        lines.append('3. Development messaging to attract moderate minorities')
        lines.append('4. Avoid polarization - maintain minority vote share')
    
    elif muslim/total*100 > 20:
        lines.append('### Scenario: Coalition Strategy (Muslim-Plus)')
        lines.append('')
        lines.append('**Formula:** Muslim base + Hindu split + Christian support')
        lines.append('')
        lines.append('**Requirements:**')
        lines.append(f'- Muslim consolidation: {muslim} voters (need 90%+ = {int(muslim*0.9)} votes)')
        lines.append(f'- Hindu split: {hindu} voters (need 25%+ = {int(hindu*0.25)} votes)')
        lines.append(f'- Christian support: {christian} voters (need 50%+ = {int(christian*0.5)} votes)')
        lines.append('')
        lines.append(f'**This gives:** {int(muslim*0.9 + hindu*0.25 + christian*0.5)} votes ({(int(muslim*0.9 + hindu*0.25 + christian*0.5))/total*100:.1f}%)')
        lines.append('')
        lines.append('**Key Actions:**')
        lines.append('1. Masjid committees and Muslim leaders engagement')
        lines.append('2. Secular messaging to attract progressive Hindus')
        lines.append('3. Church relations for Christian support')
        lines.append('4. Prevent Hindu consolidation through inclusive development agenda')
    
    else:
        lines.append('### Scenario: Broad Coalition Strategy')
        lines.append('')
        lines.append('**Formula:** Balanced appeal across all communities')
        lines.append('')
        lines.append('**Requirements:**')
        lines.append(f'- Hindu vote: {hindu} voters (need 40%+ = {int(hindu*0.4)} votes)')
        lines.append(f'- Muslim vote: {muslim} voters (need 50%+ = {int(muslim*0.5)} votes)')
        lines.append(f'- Christian vote: {christian} voters (need 60%+ = {int(christian*0.6)} votes)')
        lines.append('')
        lines.append(f'**This gives:** {int(hindu*0.4 + muslim*0.5 + christian*0.6)} votes ({(int(hindu*0.4 + muslim*0.5 + christian*0.6))/total*100:.1f}%)')
        lines.append('')
        lines.append('**Key Actions:**')
        lines.append('1. Development-focused messaging (infrastructure, jobs, education)')
        lines.append('2. Engage all religious leaders simultaneously')
        lines.append('3. Emphasize inclusive growth and social harmony')
        lines.append('4. Target swing voters in mixed households')
    
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 6. PRIORITY TARGET DEMOGRAPHICS (Rank Ordered)')
    lines.append('')
    lines.append(f'1. **Middle-aged women (30-50):** {middle_aged_women:,} voters ({middle_aged_women/total*100:.1f}%)')
    lines.append('   - Why: Largest persuadable group, family decision-makers')
    lines.append('   - How: Women-centric rallies, SHG engagement, welfare promises')
    lines.append('')
    lines.append(f'2. **Large households (5+ voters):** {large_households.sum() if len(large_households) > 0 else 0:,} voters in {len(large_households)} families')
    lines.append('   - Why: One converted family = 5-8 votes')
    lines.append('   - How: Personal visits, respected community member introductions')
    lines.append('')
    lines.append(f'3. **Young voters (18-35):** {young_voters:,} voters ({young_voters/total*100:.1f}%)')
    lines.append('   - Why: Aspirational, persuadable, digital-savvy')
    lines.append('   - How: Employment promises, social media, youth leaders')
    lines.append('')
    lines.append(f'4. **Senior citizens (60+):** {senior_citizens:,} voters ({senior_citizens/total*100:.1f}%)')
    lines.append('   - Why: High turnout, consistent voters')
    lines.append('   - How: Healthcare, pension, respect for elders')
    lines.append('')
    lines.append(f'5. **Influential families:** {len(top_families)} families controlling {top_families.sum()} votes')
    lines.append('   - Why: Bloc voting potential')
    lines.append('   - How: Personal meetings with family heads')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 7. CAMPAIGN RESOURCE ALLOCATION')
    lines.append('')
    lines.append('### 7.1 Budget Allocation (Suggested)')
    lines.append('')
    lines.append(f'- **Door-to-door campaign:** {total*10:,.0f} INR (10 INR per voter)')
    lines.append(f'- **Booth agents (Election Day):** {max(1, int(total/225))*1500:,.0f} INR ({max(1, int(total/225))} agents × 1500 INR)')
    lines.append(f'- **Vehicles:** {max(1, int(total/500))*2000:,.0f} INR ({max(1, int(total/500))} vehicles × 2000 INR)')
    lines.append(f'- **Volunteers & workers:** {total*5:,.0f} INR (meals, travel)')
    lines.append(f'- **Total District Budget:** {total*10 + max(1, int(total/225))*1500 + max(1, int(total/500))*2000 + total*5:,.0f} INR')
    lines.append('')
    lines.append('### 7.2 Human Resources')
    lines.append('')
    lines.append(f'- **Full-time Campaign Workers:** {max(2, int(total/500))}')
    lines.append(f'- **Part-time Volunteers:** {max(5, int(total/100))}')
    lines.append(f'- **Booth Agents (Election Day):** {max(1, int(total/225))}')
    lines.append(f'- **Vehicle Drivers:** {max(1, int(total/500))}')
    lines.append('')
    lines.append('### 7.3 Election Day Logistics')
    lines.append('')
    lines.append(f'- **Vehicles needed:** {max(1, int(total/500))} (1 per 500 voters)')
    lines.append(f'- **Senior transport:** {max(1, int(len(df[df["Age"]>=70])/20))} special vehicles (70+ age voters)')
    lines.append(f'- **Booth monitors:** {max(2, int(total/750))} (2 per booth)')
    lines.append(f'- **Women volunteers:** {max(2, int(female/100))} (for women voter mobilization)')
    lines.append('')
    lines.append('**Turnout Targets:**')
    lines.append(f'- Minimum required: 65% ({int(total*0.65)} voters)')
    lines.append(f'- Target: 75% ({int(total*0.75)} voters)')
    lines.append(f'- Stretch goal: 85% ({int(total*0.85)} voters)')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 8. FINAL RECOMMENDATIONS')
    lines.append('')
    lines.append(f'### Top 5 Actions for {district_name}')
    lines.append('')
    lines.append(f'1. **Personal outreach to top {min(10, len(top_families))} influential families** - Control {top_10_families.sum() if len(top_10_families) > 0 else 0} votes')
    lines.append(f'2. **Women-centric campaign targeting {middle_aged_women} middle-aged women**')
    lines.append(f'3. **Community leader engagement** - Temple/Church/Masjid committees')
    lines.append(f'4. **Youth digital campaign** - WhatsApp/social media for {young_voters} young voters')
    lines.append(f'5. **GOTV on election day** - Target 75%+ turnout ({int(total*0.75)} votes)')
    lines.append('')
    lines.append('### Success Metrics')
    lines.append('')
    lines.append(f'- ✓ 100% coverage of {len(large_households)} large households')
    lines.append(f'- ✓ Personal meetings with top {min(10, len(top_families))} family heads')
    lines.append('- ✓ 3+ community meetings with 50+ attendance each')
    lines.append('- ✓ WhatsApp groups covering 60% of 18-35 demographic')
    lines.append('- ✓ Election day turnout: 75%+ target')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('**Report End**')
    lines.append('')
    lines.append(f'**{district_name}: {total:,} voters | Generated {datetime.now().strftime("%Y-%m-%d")}**')
    lines.append('')
    lines.append('---')
    
    return '\n'.join(lines)

def main():
    print("Generating separate district reports...")
    
    districts = {
        'Rosedale-001': 'Pattathanam Voters List - Rosedale-001_cleaned.csv',
        'Bharanikkav School South-002': 'Pattathanam Voters List - Bharanikkav School South- 002_cleaned.csv',
        'Bharanikkav School North-003': 'Pattathanam Voters List - Bharanikkav School North- 003_cleaned.csv'
    }
    
    for district_name, filename in districts.items():
        print(f"\nProcessing {district_name}...")
        df = pd.read_csv(filename)
        
        report = generate_district_report(district_name, df, filename)
        
        # Create safe filename
        safe_name = district_name.replace(' ', '_').replace('-', '_')
        output_file = f'ELECTION_INSIGHTS_{safe_name}.md'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f'  ✓ {output_file} ({len(report):,} characters)')
    
    print('\n✓ All district reports generated successfully!')

if __name__ == '__main__':
    main()
