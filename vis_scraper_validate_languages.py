import asyncio
import csv
import re
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_languages_from_dropdown(page):
    """
    Get all languages from the select id="attr-lang" dropdown
    """
    languages = []

    try:
        # Specifically target the select element with id="attr-lang"
        dropdown = await page.query_selector('select[id="attr-lang"]')

        if dropdown:
            logger.info("Found select element with id='attr-lang'")
            options = await dropdown.query_selector_all("option")

            logger.info(f"Found {len(options)} language options in dropdown")

            for i, option in enumerate(options):
                try:
                    value = await option.get_attribute("value")
                    text = await option.inner_text()

                    if value and text and value != "":
                        languages.append(
                            {"value": value, "text": text.strip(), "index": i}
                        )
                        logger.info(
                            f"  Option {i}: value='{value}', text='{text.strip()}'"
                        )
                    else:
                        logger.warning(f"  Option {i}: empty value or text")

                except Exception as e:
                    logger.warning(f"Error processing option {i}: {e}")

            logger.info(
                f"Successfully extracted {len(languages)} languages from dropdown"
            )
        else:
            logger.error("Could not find select element with id='attr-lang'")

            # Fallback: try to find any select element
            all_selects = await page.query_selector_all("select")
            logger.info(f"Found {len(all_selects)} total select elements on page")

            for i, select in enumerate(all_selects):
                try:
                    id_attr = await select.get_attribute("id")
                    name_attr = await select.get_attribute("name")
                    class_attr = await select.get_attribute("class")
                    logger.info(
                        f"Select {i}: id='{id_attr}', name='{name_attr}', class='{class_attr}'"
                    )
                except Exception as e:
                    logger.warning(f"Error getting select {i} attributes: {e}")

    except Exception as e:
        logger.error(f"Error getting languages from dropdown: {e}")

    return languages


async def scrape_language_translations(page, language_info):
    """
    Scrape translations for a specific language
    """
    language_value = language_info["value"]
    language_text = language_info["text"]

    logger.info(f"Scraping translations for {language_text} ({language_value})")

    # Navigate to the language-specific page
    language_url = (
        f"https://www.immunize.org/vaccines/vis-translations/{language_value}/"
    )

    try:
        await page.goto(language_url, wait_until="networkidle")
        await page.wait_for_selector("table", timeout=30000)

        # Get the first table (Current Translations)
        tables = await page.query_selector_all("table")
        if not tables:
            logger.warning(f"No tables found for {language_text}")
            return {}

        current_table = tables[0]

        # Get table headers to extract vaccine names
        headers = await current_table.query_selector_all("th")
        vaccine_headers = []

        if headers:
            for header in headers:
                text = await header.inner_text()
                vaccine_headers.append(text.strip())

        # Get all rows
        rows = await current_table.query_selector_all("tr")
        language_data = {}

        # Process each row to extract vaccine data
        for row_index, row in enumerate(rows):
            try:
                cells = await row.query_selector_all("td")

                if len(cells) >= 5:
                    # Get vaccine name from the header (skip first 6 headers which are column titles)
                    if row_index + 6 < len(vaccine_headers):
                        vaccine_name = vaccine_headers[row_index + 6]
                    else:
                        continue

                    # Skip if no vaccine name
                    if not vaccine_name or vaccine_name in [
                        "Vaccine",
                        "PDF View & Print",
                        "Download",
                        "Date of Current English VIS",
                        "Current English VIS",
                        "More Information",
                    ]:
                        continue

                    # Extract PDF URL from first column (index 0)
                    pdf_cell = cells[0]
                    pdf_link = await pdf_cell.query_selector("a")
                    pdf_url = ""
                    if pdf_link:
                        pdf_url = await pdf_link.get_attribute("href")
                        if pdf_url and pdf_url.startswith("/"):
                            pdf_url = urljoin(language_url, pdf_url)

                    # Extract date from third column (index 2)
                    date_cell = cells[2]
                    date_text = await date_cell.inner_text()
                    date = date_text.strip()

                    # Extract English VIS link from fourth column (index 3)
                    english_vis_url = ""
                    english_vis_cell = cells[3]
                    english_vis_link = await english_vis_cell.query_selector("a")
                    if english_vis_link:
                        english_vis_url = await english_vis_link.get_attribute("href")
                        if english_vis_url and english_vis_url.startswith("/"):
                            english_vis_url = urljoin(language_url, english_vis_url)

                    # Only add if we have a vaccine name and PDF URL
                    if vaccine_name and pdf_url:
                        language_data[vaccine_name] = {
                            "pdf_url": pdf_url,
                            "date": date,
                            "english_vis_url": english_vis_url,
                        }

            except Exception as e:
                logger.warning(
                    f"Error processing row {row_index} for {language_text}: {e}"
                )
                continue

        logger.info(f"Found {len(language_data)} vaccines for {language_text}")
        return language_data

    except Exception as e:
        logger.error(f"Error scraping {language_text}: {e}")
        return {}


async def validate_all_languages():
    """
    Validate that all languages from the dropdown are being scraped
    """
    url = "https://www.immunize.org/vaccines/vis-translations/"
    all_results = {}
    validation_results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_selector("table", timeout=30000)

            logger.info("Page loaded successfully")

            # Get all languages from the dropdown
            languages = await get_languages_from_dropdown(page)
            logger.info(f"Found {len(languages)} languages in dropdown")

            if not languages:
                logger.error("No languages found in dropdown!")
                return {}

            # Validate each language
            for language_info in languages:
                logger.info(
                    f"\n=== Validating {language_info['text']} ({language_info['value']}) ==="
                )

                # Try to scrape this language
                language_data = await scrape_language_translations(page, language_info)

                validation_results[language_info["text"]] = {
                    "language_info": language_info,
                    "scraped": len(language_data) > 0,
                    "vaccine_count": len(language_data),
                    "data": language_data,
                }

                if language_data:
                    all_results[language_info["text"]] = language_data
                    logger.info(
                        f"✅ {language_info['text']}: Successfully scraped {len(language_data)} vaccines"
                    )
                else:
                    logger.warning(f"❌ {language_info['text']}: No data scraped")

        except Exception as e:
            logger.error(f"Error during validation: {e}")
        finally:
            await browser.close()

    return all_results, validation_results


def save_validation_report(
    validation_results, filename="language_validation_report.csv"
):
    """
    Save a validation report showing which languages were successfully scraped
    """
    try:
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "Language",
                "Language Value",
                "Dropdown Index",
                "Successfully Scraped",
                "Vaccine Count",
                "Notes",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for language_name, result in validation_results.items():
                writer.writerow(
                    {
                        "Language": language_name,
                        "Language Value": result["language_info"]["value"],
                        "Dropdown Index": result["language_info"]["index"],
                        "Successfully Scraped": "Yes" if result["scraped"] else "No",
                        "Vaccine Count": result["vaccine_count"],
                        "Notes": (
                            "Data found" if result["scraped"] else "No data or error"
                        ),
                    }
                )

        logger.info(f"Validation report saved to {filename}")

    except Exception as e:
        logger.error(f"Error saving validation report: {e}")


def save_to_csv(all_results, filename="vis_translations_all_languages_validated.csv"):
    """
    Save the scraped data to a CSV file with language-specific columns
    """
    if not all_results:
        logger.warning("No data to save")
        return

    try:
        # Get all unique vaccine names
        all_vaccines = set()
        for language_data in all_results.values():
            all_vaccines.update(language_data.keys())

        all_vaccines = sorted(list(all_vaccines))

        # Create fieldnames
        fieldnames = ["Vaccine", "Date of Current English VIS", "Current English VIS"]

        # Add language-specific PDF URL columns
        for language_name in sorted(all_results.keys()):
            fieldnames.append(f"PDF URL ({language_name})")

        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            # Write data for each vaccine
            for vaccine_name in all_vaccines:
                row = {
                    "Vaccine": vaccine_name,
                    "Date of Current English VIS": "",
                    "Current English VIS": "",
                }

                # Add PDF URLs for each language
                for language_name in sorted(all_results.keys()):
                    language_data = all_results[language_name]
                    if vaccine_name in language_data:
                        row[f"PDF URL ({language_name})"] = language_data[vaccine_name][
                            "pdf_url"
                        ]
                        # Use the first language's date and English VIS URL
                        if not row["Date of Current English VIS"]:
                            row["Date of Current English VIS"] = language_data[
                                vaccine_name
                            ]["date"]
                        if not row["Current English VIS"]:
                            row["Current English VIS"] = language_data[vaccine_name][
                                "english_vis_url"
                            ]
                    else:
                        row[f"PDF URL ({language_name})"] = ""

                writer.writerow(row)

        logger.info(
            f"Successfully saved data for {len(all_vaccines)} vaccines in {len(all_results)} languages to {filename}"
        )

    except Exception as e:
        logger.error(f"Error saving to CSV: {e}")


async def main():
    """
    Main function to validate all languages
    """
    logger.info("Starting language validation scraper...")

    # Validate all languages
    all_results, validation_results = await validate_all_languages()

    if validation_results:
        total_languages = len(validation_results)
        successful_languages = sum(
            1 for result in validation_results.values() if result["scraped"]
        )
        total_vaccines = sum(
            result["vaccine_count"] for result in validation_results.values()
        )

        logger.info(f"\n=== VALIDATION SUMMARY ===")
        logger.info(f"Total languages in dropdown: {total_languages}")
        logger.info(f"Successfully scraped: {successful_languages}")
        logger.info(f"Failed to scrape: {total_languages - successful_languages}")
        logger.info(f"Total vaccine records: {total_vaccines}")

        # Save validation report
        save_validation_report(validation_results)

        # Save CSV if we have data
        if all_results:
            save_to_csv(all_results)

        # Print detailed results
        print(f"\n=== DETAILED RESULTS ===")
        for language_name, result in validation_results.items():
            status = "✅" if result["scraped"] else "❌"
            print(f"{status} {language_name}: {result['vaccine_count']} vaccines")

    else:
        logger.error("No validation results")


if __name__ == "__main__":
    asyncio.run(main())
