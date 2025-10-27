#!/usr/bin/env python3
"""
Generate ward-level election reports - Production Version
"""
import pandas as pd
from datetime import datetime
import os

def build_comprehensive_report(ward_num, ward_data):
    """Build comprehensive report incrementally"""
    lines = []
    total = len(ward_data)
    
    # Basic stats
    male = len(ward_data[ward_data['Gender'] == 'M'])
    female = len(ward_data[ward_data['Gender'] == 'F'])
    hindu = len(ward_data[ward_data['Religion'] == 'Hindu'])
    muslim = len(ward_data[ward_data['Religion'] == 'Muslim'])
    christian = len(ward_data[ward_data['Religion'] == 'Christian'])
    
    # Header
    lines.append(f'# WARD {ward_num} - COMPREHENSIVE CAMPAIGN REPORT')
    lines.append('## Pattathanam Assembly Constituency, Kollam District, Kerala')
    lines.append('')
    lines.append(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'**Ward Number:** {ward_num}')
    lines.append(f'**Total Voters:** {total:,}')
    lines.append(f'**Constituency Share:** {total/4133*100:.1f}%')
    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## EXECUTIVE SUMMARY')
    lines.append('')
    
    # Determine ward type
    hindu_pct = hindu/total*100
    if hindu_pct > 70:
        ward_type = 'HINDU-MAJORITY WARD'
    elif 40 < hindu_pct < 70:
        ward_type = 'SWING WARD'
    else:
        ward_type = 'DIVERSE WARD'
    
    lines.append(f'**Ward Type:** {ward_type}')
    lines.append(f'**Priority Level:** {"CRITICAL" if total > 1000 else "HIGH"}')
    lines.append('')
    
    # Demographics table
    lines.append('### Demographics Overview')
    lines.append('')
    lines.append('| Metric | Count | Percentage |')
    lines.append('|--------|-------|------------|')
    lines.append(f'| Male Voters | {male:,} | {male/total*100:.1f}% |')
    lines.append(f'| Female Voters | {female:,} | {female/total*100:.1f}% |')
    lines.append(f'| Hindu | {hindu:,} | {hindu/total*100:.1f}% |')
    lines.append(f'| Muslim | {muslim:,} | {muslim/total*100:.1f}% |')
    lines.append(f'| Christian | {christian:,} | {christian/total*100:.1f}% |')
    lines.append('')
    
    # Age analysis
    lines.append('### Age Distribution')
    lines.append('')
    age_groups = {
        '18-25': ((18, 25), 'First-time voters'),
        '26-35': ((26, 35), 'Young professionals'),
        '36-45': ((36, 45), 'Family decision-makers'),
        '46-55': ((46, 55), 'Peak earners'),
        '56-65': ((56, 65), 'Pre-retirement'),
        '66+': ((66, 150), 'Senior citizens')
    }
    
    lines.append('| Age Group | Count | Percentage | Target |')
    lines.append('|-----------|-------|------------|--------|')
    
    for label, (age_range, target) in age_groups.items():
        min_age, max_age = age_range
        if max_age == 150:
            count = len(ward_data[ward_data['Age'] >= min_age])
        else:
            count = len(ward_data[(ward_data['Age'] >= min_age) & (ward_data['Age'] <= max_age)])
        pct = count/total*100 if total > 0 else 0
        lines.append(f'| {label} | {count} | {pct:.1f}% | {target} |')
    
    lines.append('')
    lines.append(f'**Average Age:** {ward_data["Age"].mean():.1f} years')
    lines.append('')
    
    # Large households
    lines.append('## KEY VOTING BLOCS')
    lines.append('')
    households = ward_data.groupby('OldWard No/ House No.').size()
    large_households = households[households >= 5].sort_values(ascending=False)
    
    lines.append(f'### Large Households (5+ voters): {len(large_households)}')
    lines.append('')
    lines.append(f'**Total voters in large households:** {large_households.sum() if len(large_households) > 0 else 0}')
    lines.append('')
    
    if len(large_households) > 0:
        lines.append('**Top 20 Large Households:**')
        lines.append('')
        lines.append('| Address | Voters |')
        lines.append('|---------|--------|')
        for address, count in large_households.head(20).items():
            lines.append(f'| {address} | {count} |')
        lines.append('')
    
    # Influential families
    guardians = ward_data["Guardian's Name"].value_counts()
    top_families = guardians[guardians >= 3].head(20)
    
    lines.append(f'### Influential Families (3+ dependents): {len(guardians[guardians >= 3])}')
    lines.append('')
    
    if len(top_families) > 0:
        lines.append('| Guardian Name | Family Size |')
        lines.append('|---------------|-------------|')
        for guardian, count in top_families.items():
            lines.append(f'| {guardian} | {count} |')
        lines.append('')
    
    # Complete voter list
    lines.append('## COMPLETE VOTER LIST')
    lines.append('')
    lines.append(f'**Total: {total} voters**')
    lines.append('')
    lines.append('| # | Name | Age | Gender | Religion | Address |')
    lines.append('|---|------|-----|--------|----------|---------|')
    
    ward_sorted = ward_data.sort_values(['OldWard No/ House No.', 'Age'], ascending=[True, False])
    for idx, (_, row) in enumerate(ward_sorted.iterrows(), 1):
        name = str(row['Name'])[:30]
        age = int(row['Age']) if pd.notna(row['Age']) else 0
        gender = row['Gender']
        religion = row['Religion']
        address = str(row['OldWard No/ House No.'])[:20]
        lines.append(f'| {idx} | {name} | {age} | {gender} | {religion} | {address} |')
    
    lines.append('')
    
    # Strategy recommendations
    lines.append('## CAMPAIGN STRATEGY')
    lines.append('')
    lines.append('### Booth Agent Requirements')
    lines.append('')
    agents_needed = max(1, int(total / 225))
    lines.append(f'**Total Agents Needed:** {agents_needed}')
    lines.append(f'- Hindu community: {max(1, int(hindu/300))} agents')
    lines.append(f'- Muslim community: {max(1, int(muslim/300))} agents')
    lines.append(f'- Christian community: {max(1, int(christian/300))} agents')
    lines.append('')
    
    lines.append('### Election Day Logistics')
    lines.append('')
    vehicles = max(1, int(total/500))
    lines.append(f'- **Vehicles needed:** {vehicles}')
    lines.append(f'- **Senior transport:** {max(1, int(len(ward_data[ward_data["Age"]>=70])/20))} vehicles')
    lines.append(f'- **Booth monitors:** {max(2, int(total/750))}')
    lines.append('')
    
    lines.append('### Vote Targets')
    lines.append('')
    lines.append(f'- **Minimum to win:** {int(total*0.5)+1} votes (50%+1)')
    lines.append(f'- **Comfortable win:** {int(total*0.55)} votes (55%)')
    lines.append(f'- **Landslide:** {int(total*0.60)} votes (60%)')
    lines.append('')
    
    lines.append('### Priority Actions')
    lines.append('')
    lines.append(f'1. Personal outreach to {len(top_families)} influential families')
    lines.append(f'2. Women-focused campaign targeting {len(ward_data[(ward_data["Gender"]=="F") & (ward_data["Age"]>=30) & (ward_data["Age"]<=50)])} middle-aged women')
    lines.append(f'3. Door-to-door coverage of {len(large_households)} large households')
    lines.append(f'4. Youth mobilization for {len(ward_data[ward_data["Age"]<=35])} young voters')
    lines.append(f'5. Senior citizen outreach for {len(ward_data[ward_data["Age"]>=60])} elderly voters')
    lines.append('')
    
    lines.append('---')
    lines.append('')
    lines.append(f'**Report Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    lines.append(f'**Data Source:** Pattathanam Voter Rolls 2025')
    
    return '\\n'.join(lines)

def main():
    print('Loading voter data...')
    combined_df = pd.concat([
        pd.read_csv('Pattathanam Voters List - Rosedale-001_cleaned.csv'),
        pd.read_csv('Pattathanam Voters List - Bharanikkav School South- 002_cleaned.csv'),
        pd.read_csv('Pattathanam Voters List - Bharanikkav School North- 003_cleaned.csv')
    ], ignore_index=True)
    
    combined_df['Ward'] = combined_df['OldWard No/ House No.'].str.split('/').str[0]
    
    os.makedirs('ward_reports', exist_ok=True)
    
    # Generate reports for major wards
    for ward_num in ['040', '043']:
        ward_data = combined_df[combined_df['Ward'] == ward_num].copy()
        if len(ward_data) > 0:
            print(f'Generating Ward {ward_num} report ({len(ward_data)} voters)...')
            report = build_comprehensive_report(ward_num, ward_data)
            
            filename = f'ward_reports/Ward_{ward_num}_Comprehensive.md'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f'  ✓ {filename}')
    
    print('')
    print('✓ Ward reports generated successfully!')
    print('✓ Location: ward_reports/ directory')

if __name__ == '__main__':
    main()
