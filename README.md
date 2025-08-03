# VIS Translations Scraper

This Python script uses Playwright to scrape the Immunize.org Spanish VIS (Vaccine Information Statement) translations page and extract PDF links with vaccine information.

## Features

- Scrapes the Immunize.org Spanish VIS translations page
- Extracts vaccine names, PDF URLs, dates, and English VIS links
- Saves results to CSV format with headers: Vaccine, PDF URL, Date of Current English VIS, Current English VIS
- Handles both current and out-of-date translations
- Includes error handling and logging

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install
```

## Usage

Run the scraper:
```bash
python vis_scraper.py
```

The script will:
1. Navigate to the Immunize.org Spanish VIS translations page
2. Extract all vaccine information from the tables
3. Save the results to `vis_translations.csv`

## Output

The script generates a CSV file with the following columns:
- **Vaccine**: Name of the vaccine
- **PDF URL**: Direct link to the Spanish VIS PDF
- **Date of Current English VIS**: Date of the current English version
- **Current English VIS**: Link to the current English VIS

## Requirements

- Python 3.7+
- Playwright
- Internet connection

## Notes

- The script runs in headless mode by default
- It includes comprehensive error handling and logging
- Results are saved in UTF-8 encoding to handle special characters
- The script handles both relative and absolute URLs 