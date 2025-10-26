# Voter Analysis

A Python-based tool for cleaning and standardizing voter list CSV data.

## Features

- **Splits Gender/Age column** into separate Gender (M/F) and Age (numeric) columns
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
- python-dotenv

### Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install pandas openai python-dotenv
```

3. Configure Azure OpenAI (Optional - for Malayalam transliteration):
```bash
cp .env.local.example .env.local
```

Then edit `.env.local` and add your Azure OpenAI credentials:
```
AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_OPENAI_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-5-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

**Note:** The `.env.local` file is git-ignored and will not be committed to the repository.

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

1. **Gender/Age Column Split**: Separates combined "Gender / Age" column into:
   - `Gender`: Single character ('M' or 'F')
   - `Age`: Numeric integer value
2. **Ward Number Standardization**: Converts all ward numbers to 3-digit format (e.g., `43/979` → `043/979`)
3. **Missing SEC ID Flagging**: Marks entries without SEC IDs as `REVIEW_NEEDED`
4. **Duplicate Detection**: Flags potential duplicate entries for manual review
5. **Malayalam Transliteration**: Converts Malayalam text to Latin script
6. **Whitespace Normalization**: Removes extra spaces and cleans text fields

## Output Format

The cleaned CSV includes an additional "Notes" column containing:
- `REVIEW_NEEDED: Missing SEC ID` - Entries requiring SEC ID lookup
- `DUPLICATE_CHECK: Possible duplicate entry` - Potential duplicate records
- `TRANSLITERATED: [original] -> [transliterated]` - Malayalam text conversions

## License

This project is for data analysis and cleaning purposes.
