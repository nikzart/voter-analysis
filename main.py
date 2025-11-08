#!/usr/bin/env python3
"""
Kerala Voter List Scraper - Main Entry Point
Scrapes voter list data from sec.kerala.gov.in for configured wards
"""
import sys
import os
from pathlib import Path
from scraper import VoterListScraper


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("Kerala Voter List Scraper - Phase 2: Data Scraping")
    print("="*60 + "\n")

    # Check if polling stations map exists
    map_file = Path('polling_stations_map.json')
    if not map_file.exists():
        print("ERROR: Polling stations map not found!")
        print("\nYou must run Phase 1 (discovery) first:")
        print("  python discover_polling_stations.py")
        print("\nThis will create 'polling_stations_map.json' with all polling stations.")
        print("Then you can run this script to scrape the voter data.\n")
        sys.exit(1)

    try:
        # Initialize and run scraper
        scraper = VoterListScraper(
            config_path='config.json',
            polling_stations_map_path='polling_stations_map.json'
        )
        scraper.run()

    except FileNotFoundError as e:
        print(f"Error: Required file not found - {e}")
        print("Make sure 'config.json' and 'polling_stations_map.json' exist")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user. Exiting...")
        sys.exit(0)

    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()