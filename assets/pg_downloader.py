"""
gutenberg_downloader.py

Downloads English-language HTML books from Project Gutenberg.

Strategy:
  1. Search the local pg_catalog.csv for matching author IDs.
  2. Fetch book metadata from Gutendex using those exact IDs.
  3. Download the HTML version of each matched book.

NOTE: This script uses the public gutendex.com server. For sustained or
high-volume use, run your own instance: https://github.com/garethbjohnson/gutendex

REQUIRES: pg_catalog.csv in the same directory as this script.
"""

import os
import time
import unicodedata
import requests
import pandas as pd
from urllib.parse import unquote

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CATALOG_PATH    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pg_catalog.csv")
BASE_URL        = "https://gutendex.com/books/"
DOWNLOAD_DIR    = "downloaded"
REQUEST_TIMEOUT = 15       # seconds before a network call is abandoned
RETRY_ATTEMPTS  = 3        # how many times to retry a failed request
RETRY_BACKOFF   = 2.0      # seconds to wait between retries (doubles each time)
DOWNLOAD_PAUSE  = 1.0      # seconds to pause between file downloads (be polite)
GUTENDEX_PAGE   = 32       # max IDs per Gutendex request


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------
def normalize(s: str) -> str:
    """Lowercase and strip diacritics so 'Bronte' matches 'Brontë'."""
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower())
        if unicodedata.category(c) != "Mn"
    )


# ---------------------------------------------------------------------------
# Catalog search
# ---------------------------------------------------------------------------
def find_ids_in_catalog(last: str, first: str) -> list[int]:
    """
    Search pg_catalog.csv for English books whose Authors field contains an
    entry matching 'last, first' (diacritic-insensitive, ignoring birth/death
    years and role annotations like [Illustrator]).

    Author entries in the catalog look like:
      Bronte, Charlotte, 1816-1855
      Bronte, Charlotte, 1816-1855; Townsend, F. H. (Frederick Henry), 1868-1920 [Illustrator]

    We split on ';', strip years and annotations, then compare last and first
    name parts separately using startswith on the first name.
    """
    if not os.path.exists(CATALOG_PATH):
        print(f"ERROR: Catalog not found at {CATALOG_PATH}")
        print("Please place pg_catalog.csv in the same folder as this script.")
        return []

    df = pd.read_csv(CATALOG_PATH, dtype={"Text#": int})

    norm_last  = normalize(last)
    norm_first = normalize(first)

    matched_ids = []

    for _, row in df.iterrows():
        raw_authors = str(row.get("Authors", ""))
        language    = str(row.get("Language", ""))

        # Catalog stores multiple languages as comma-separated codes.
        if "en" not in [lang.strip() for lang in language.split(",")]:
            continue

        # Each row may have multiple authors separated by semicolons.
        for author_entry in raw_authors.split(";"):
            # Strip role annotations like [Illustrator], [Translator], etc.
            author_entry = author_entry.split("[")[0].strip()

            # Format: "Last, First, YYYY-YYYY" — split on comma.
            parts = [p.strip() for p in author_entry.split(",")]
            if len(parts) < 2:
                continue

            entry_last  = normalize(parts[0])
            entry_first = normalize(parts[1])

            if (entry_last == norm_last
                    and entry_first.startswith(norm_first)):
                matched_ids.append(int(row["Text#"]))
                break  # don't double-count a book with multiple matching authors

    return matched_ids


# ---------------------------------------------------------------------------
# Networking helpers
# ---------------------------------------------------------------------------
def fetch_json(url: str, params: dict | None = None) -> dict | None:
    """GET a URL and return parsed JSON, with retries and a timeout."""
    delay = RETRY_BACKOFF
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"  [timeout] attempt {attempt}/{RETRY_ATTEMPTS}")
        except requests.exceptions.HTTPError as exc:
            print(f"  [HTTP {exc.response.status_code}] {url}")
            return None
        except requests.exceptions.RequestException as exc:
            print(f"  [error] {exc} (attempt {attempt}/{RETRY_ATTEMPTS})")

        if attempt < RETRY_ATTEMPTS:
            time.sleep(delay)
            delay *= 2

    return None


def fetch_books_by_ids(ids: list[int]) -> list[dict]:
    """
    Fetch Gutendex book records for a list of Gutenberg IDs.
    Batches requests to stay within Gutendex's page size.
    """
    books = []
    for i in range(0, len(ids), GUTENDEX_PAGE):
        batch = ids[i : i + GUTENDEX_PAGE]
        params = {"ids": ",".join(str(id_) for id_ in batch)}
        data = fetch_json(BASE_URL, params=params)
        if data:
            books.extend(data.get("results", []))
    return books


# ---------------------------------------------------------------------------
# File download
# ---------------------------------------------------------------------------
def is_index_file(filename: str) -> bool:
    """Return True for Gutenberg index / table-of-contents pages."""
    name_lower = filename.lower()
    index_markers = ("-index.", "_index.", "-h.htm", "-h.html")
    return any(marker in name_lower for marker in index_markers)


def download_file(url: str) -> None:
    """Download a single file into DOWNLOAD_DIR, skipping duplicates."""
    filename = unquote(os.path.basename(url.split("?")[0]))

    if filename.endswith(".images"):
        filename = filename[: -len(".images")]

    if is_index_file(filename):
        print(f"  [skip index] {filename}")
        time.sleep(DOWNLOAD_PAUSE)
        return

    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        print(f"  [exists]     {filename}")
        return

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        with open(filepath, "wb") as fh:
            fh.write(response.content)
        print(f"  [ok]         {filename}")
    except requests.exceptions.RequestException as exc:
        print(f"  [failed]     {url}: {exc}")
    finally:
        time.sleep(DOWNLOAD_PAUSE)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    author_input = input("Enter author name (LAST, FIRST): ").strip()
    parts = [p.strip() for p in author_input.split(",", 1)]
    if len(parts) < 2:
        print("Invalid format. Please use: LAST, FIRST")
        input("Press Enter to exit")
        return

    last, first = parts

    print(f"\nSearching catalog for: {author_input}")
    ids = find_ids_in_catalog(last, first)

    if not ids:
        print("No matching books found in the local catalog.")
        input("Press Enter to exit")
        return

    print(f"Found {len(ids)} book ID(s) in catalog: {ids}")
    print("Fetching metadata from Gutendex...\n")

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    books = fetch_books_by_ids(ids)

    if not books:
        print("Gutendex returned no results for those IDs.")
        input("Press Enter to exit")
        return

    total_downloaded = 0
    for book in books:
        title   = book.get("title", "(untitled)")
        formats = book.get("formats", {})

        html_url = (
            formats.get("text/html")
            or next((v for k, v in formats.items() if k.startswith("text/html")), None)
        )

        if html_url:
            print(f'"{title}"')
            download_file(html_url)
            total_downloaded += 1
        else:
            print(f'  [no html] "{title}" — skipping')

    print(f"\nDone. {total_downloaded} file(s) processed.")
    input("Press Enter to exit")


if __name__ == "__main__":
    main()