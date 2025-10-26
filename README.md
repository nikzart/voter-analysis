# Voter Analysis

A Python-based tool for cleaning and standardizing voter list CSV data.

## Features

- Standardizes ward/house number formatting
- Detects and flags missing SEC IDs
- Identifies duplicate entries
- Transliterates Malayalam text to Latin script (optional, requires Azure OpenAI)
- Removes extra whitespace and normalizes text
- Generates detailed cleaning reports

## Setup

### Requirements

- Python 3.7+
- pandas
- openai (for Malayalam transliteration)

### Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install pandas openai
```

### Configuration (Optional)

For Malayalam transliteration, set the following environment variables:

```bash
export AZURE_OPENAI_ENDPOINT="your-endpoint-url"
export AZURE_OPENAI_KEY="your-api-key"
export AZURE_OPENAI_DEPLOYMENT="gpt-5-mini"
export AZURE_OPENAI_API_VERSION="2024-12-01-preview"
```

## Usage

Run the cleaning script:

```bash
python clean_voters_csv.py
```

### Input

- `Pattathanam Voters List - Rosedale-001.csv` - Original voter list data

### Output

- `Pattathanam Voters List - Rosedale-001_cleaned.csv` - Cleaned data with Notes column
- `cleaning_report.txt` - Detailed report of all changes and flagged items

## Data Cleaning Operations

1. **Ward Number Standardization**: Converts all ward numbers to 3-digit format (e.g., `43/979` → `043/979`)
2. **Missing SEC ID Flagging**: Marks entries without SEC IDs as `REVIEW_NEEDED`
3. **Duplicate Detection**: Flags potential duplicate entries for manual review
4. **Malayalam Transliteration**: Converts Malayalam text to Latin script
5. **Whitespace Normalization**: Removes extra spaces and cleans text fields

## Output Format

The cleaned CSV includes an additional "Notes" column containing:
- `REVIEW_NEEDED: Missing SEC ID` - Entries requiring SEC ID lookup
- `DUPLICATE_CHECK: Possible duplicate entry` - Potential duplicate records
- `TRANSLITERATED: [original] -> [transliterated]` - Malayalam text conversions

## License

This project is for data analysis and cleaning purposes.
