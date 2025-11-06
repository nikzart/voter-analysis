"""
Polling Station Discovery Script
Discovers all polling stations for configured wards and saves to JSON
"""
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PollingStationDiscovery:
    """Discovers polling stations for all configured wards"""

    def __init__(self, config_path='config.json'):
        """
        Initialize the discovery tool

        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.form_url = self.config['form_url']
        self.district = self.config['district']
        self.local_body = self.config['local_body']
        self.output_file = 'polling_stations_map.json'

    def get_polling_stations_for_ward(self, page, ward):
        """
        Get all polling stations for a given ward

        Args:
            page: Playwright page object
            ward: Ward dictionary with 'value' and 'text'

        Returns:
            List of polling station dictionaries (value, text)
        """
        try:
            logger.info(f"Discovering polling stations for ward: {ward['text']}")

            # Navigate to form page
            page.goto(self.form_url)
            page.wait_for_load_state('networkidle')
            time.sleep(2)  # Give page time to fully render

            # Select district (force=True for hidden selects)
            page.locator('#view_voters_list_district').select_option(value=self.district, force=True)
            time.sleep(2)  # Wait for AJAX to populate local bodies

            # Select local body (force=True for hidden selects)
            page.locator('#view_voters_list_localBody').select_option(value=self.local_body, force=True)
            time.sleep(2)  # Wait for AJAX to populate wards

            # Select the ward (force=True for hidden selects)
            page.locator('#view_voters_list_ward').select_option(value=ward['value'], force=True)
            time.sleep(2)  # Wait for AJAX to populate polling stations

            # Get polling station options
            ps_options = page.locator('#view_voters_list_pollingStation option').all()

            polling_stations = []
            for option in ps_options:
                value = option.get_attribute('value')
                text = option.inner_text()

                if value and value != '':  # Skip empty option
                    polling_stations.append({'value': value, 'text': text})

            logger.info(f"Found {len(polling_stations)} polling stations for {ward['text']}")
            return polling_stations

        except Exception as e:
            logger.error(f"Error getting polling stations for {ward['text']}: {e}")
            return []

    def discover_all(self):
        """
        Discover polling stations for all wards

        Returns:
            Dictionary with complete polling station mapping
        """
        logger.info("Starting Polling Station Discovery")
        logger.info(f"Total wards to process: {len(self.config['wards'])}")
        logger.info(f"District: {self.district}")
        logger.info(f"Local Body: {self.local_body}\n")

        start_time = time.time()

        # Result structure
        result = {
            'discovery_timestamp': datetime.now().isoformat(),
            'district': self.district,
            'local_body': self.local_body,
            'wards': []
        }

        total_polling_stations = 0

        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            try:
                # Process each ward
                for idx, ward in enumerate(self.config['wards'], 1):
                    logger.info(f"\n{'='*60}")
                    logger.info(f"Processing ward {idx}/{len(self.config['wards'])}")
                    logger.info(f"Ward: {ward['text']}")
                    logger.info(f"{'='*60}\n")

                    # Get polling stations for this ward
                    polling_stations = self.get_polling_stations_for_ward(page, ward)

                    # Add to result
                    ward_data = {
                        'value': ward['value'],
                        'text': ward['text'],
                        'polling_stations': polling_stations
                    }
                    result['wards'].append(ward_data)

                    total_polling_stations += len(polling_stations)

                    # Progress update
                    logger.info(f"Progress: {idx}/{len(self.config['wards'])} wards")
                    logger.info(f"Total polling stations discovered so far: {total_polling_stations}\n")

            except KeyboardInterrupt:
                logger.warning("Discovery interrupted by user")

            finally:
                browser.close()

        # Calculate statistics
        elapsed_time = time.time() - start_time
        result['total_wards'] = len(result['wards'])
        result['total_polling_stations'] = total_polling_stations

        # Save to JSON file
        with open(self.output_file, 'w') as f:
            json.dump(result, f, indent=2)

        # Final statistics
        logger.info(f"\n{'='*60}")
        logger.info("Discovery completed!")
        logger.info(f"{'='*60}")
        logger.info(f"Total wards: {result['total_wards']}")
        logger.info(f"Total polling stations: {total_polling_stations}")
        logger.info(f"Total time: {elapsed_time:.2f} seconds")
        logger.info(f"Output file: {Path(self.output_file).absolute()}")
        logger.info(f"{'='*60}\n")

        return result


if __name__ == "__main__":
    discovery = PollingStationDiscovery()
    discovery.discover_all()
