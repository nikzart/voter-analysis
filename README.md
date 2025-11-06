# Kerala Voter List Scraper

A Python-based web scraper for extracting voter list data from the Kerala State Election Commission website (https://sec.kerala.gov.in).

## Features

- Automated browser control using Playwright
- Advanced captcha solving using Azure OpenAI GPT-4 Vision API
- Configurable ward selection
- Automatic polling station discovery
- CSV export of voter data
- Progress tracking and error handling
- Optimized timing and rate limiting
- Two-phase scraping (discovery and data extraction)

## Prerequisites

Before you begin, ensure you have the following:

1. Python 3.8 or higher
2. Azure OpenAI API access with GPT-4 Vision deployment

## Installation

### 1. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Playwright Browsers

```bash
playwright install chromium
```

## Configuration

The scraper is configured via `config.json`. The default configuration includes 15 wards from Kollam district.

### Configuration Options

```json
{
  "base_url": "https://sec.kerala.gov.in",
  "form_url": "https://sec.kerala.gov.in/public/voters/list",
  "output_directory": "output",
  "delay_between_requests": 1,
  "max_captcha_retries": 8,
  "language": "E",
  "district": "13",
  "local_body": "eMVLzGlZgA",
  "azure_openai": {
    "endpoint": "https://your-resource.cognitiveservices.azure.com/",
    "deployment": "gpt-4-vision",
    "api_version": "2024-12-01-preview",
    "subscription_key": "your-api-key-here"
  },
  "wards": [...]
}
```

- **base_url**: Base URL of the website
- **form_url**: URL of the voter list form
- **output_directory**: Directory where CSV files will be saved
- **delay_between_requests**: Delay in seconds between requests (optimized to 1 second)
- **max_captcha_retries**: Maximum attempts to solve captcha (8 retries)
- **language**: Language code (E=English, M=Malayalam, T=Tamil, K=Kannada)
- **district**: District ID for Kollam
- **local_body**: Local body ID for the municipality
- **azure_openai**: Azure OpenAI API configuration
  - **endpoint**: Your Azure OpenAI resource endpoint
  - **deployment**: Your GPT-4 Vision deployment name
  - **api_version**: API version to use
  - **subscription_key**: Your Azure OpenAI API key
- **wards**: Array of ward objects with `value` and `text` properties

### Adding Custom Wards

To scrape different wards, update the `wards` array in `config.json`:

```json
"wards": [
  {"value": "ward_id_here", "text": "Ward Name Here"},
  {"value": "another_id", "text": "Another Ward"}
]
```

## Usage

### Basic Usage

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run the scraper
python main.py
```

The scraper will:
1. Open a browser window (visible by default for debugging)
2. Navigate to each configured ward
3. Discover all polling stations in the ward
4. For each polling station:
   - Fill in the form
   - Solve the captcha using OCR
   - Submit the form
   - Extract voter data
5. Save data to CSV files in the `output/` directory

### Output

CSV files are created in the `output/` directory with the naming pattern:
```
{ward_name}_{timestamp}.csv
```

Each CSV file contains:
- All voter information from the website
- Ward name
- Polling station name
- Scrape timestamp

## Project Structure

```
voter-analysis/
├── venv/                            # Virtual environment (created by you)
├── output/                          # Output directory for CSV files (created automatically)
├── config.json                     # Configuration file (includes Azure OpenAI credentials)
├── requirements.txt                # Python dependencies
├── main.py                         # Entry point script
├── scraper.py                      # Main scraper logic (Phase 2)
├── discover_polling_stations.py    # Polling station discovery (Phase 1)
├── polling_stations_map.json       # Discovered polling stations data
├── captcha_solver.py               # Azure OpenAI GPT-4 Vision captcha solver
├── .gitignore                      # Git ignore file
└── README.md                       # This file
```

## Troubleshooting

### Captcha Solving Issues

If the captcha solver is having trouble:

1. **Verify Azure OpenAI credentials**: Ensure your API key and endpoint are correct in `config.json`
2. **Check API quota**: Make sure you haven't exceeded your Azure OpenAI API quota
3. **Increase retry attempts**: Increase `max_captcha_retries` in `config.json`
4. **Monitor API responses**: Check logs for HTTP errors from Azure OpenAI API

### Browser Issues

If Playwright browser fails to launch:

```bash
# Reinstall browsers
playwright install chromium --force
```

### Import Errors

Make sure virtual environment is activated and all dependencies are installed:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Limitations

1. **API costs**: Uses Azure OpenAI GPT-4 Vision API which incurs usage costs
2. **Network dependent**: Requires stable internet connection for both scraping and API calls
3. **Server-side rate limiting**: The website may implement rate limiting. Current delay is optimized to 1 second.
4. **Ward configuration**: Requires manual ward ID configuration. Ward IDs must be obtained from the website's HTML/API.

## Ethical Considerations

- This tool is for educational and legitimate research purposes only
- Respect the website's terms of service
- Use appropriate rate limiting to avoid server overload
- Do not use scraped data for unauthorized purposes
- Ensure compliance with data protection regulations

## License

This project is provided as-is for educational purposes.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review the logs output during scraping
3. Verify your configuration in `config.json`

## Performance

Current optimized performance metrics:
- **Average time per polling station**: ~59 seconds
- **Captcha success rate**: ~95% (using GPT-4 Vision)
- **Total scraping time for 63 polling stations**: ~62 minutes
- **Zero errors**: Complete scraping with no failures

## Contributing

Improvements and bug fixes are welcome. Areas for contribution:
- Alternative captcha solving methods
- Better error handling and recovery
- Support for different districts/states
- Data validation and cleaning
- Additional performance optimizations
- Export to different formats (JSON, SQL, etc.)
