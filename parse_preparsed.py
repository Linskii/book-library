#!/usr/bin/env python3
"""
Script to parse preparsed JSON files and create a structured database
with Google Books API enrichment for missing data
"""

import json
import re
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional
import urllib.parse


def parse_date(date_str: str) -> tuple[Optional[int], Optional[int]]:
    """
    Parse date_read field and return (year, month)
    Examples:
      - "April 06" -> (2006, 4)
      - "Januar 2025" -> (2025, 1)
      - "Jan. 2014" -> (2014, 1)
      - "2015-11-06" -> (2015, 11)
    """
    if not date_str:
        return None, None

    # German month names/abbreviations
    months_map = {
        'jan': 1, 'januar': 1,
        'feb': 2, 'februar': 2,
        'mär': 3, 'märz': 3, 'mar': 3,
        'apr': 4, 'april': 4,
        'mai': 5,
        'jun': 6, 'juni': 6,
        'jul': 7, 'juli': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'sept': 9, 'september': 9,
        'okt': 10, 'oktober': 10,
        'nov': 11, 'november': 11,
        'dez': 12, 'dezember': 12
    }

    date_lower = date_str.lower().strip().rstrip('.')

    # Try ISO format first: YYYY-MM-DD
    iso_match = re.match(r'(\d{4})-(\d{2})-\d{2}', date_lower)
    if iso_match:
        return int(iso_match.group(1)), int(iso_match.group(2))

    # Try to find year (2-digit or 4-digit)
    year_match = re.search(r'\b(20\d{2}|\d{2})\b', date_lower)
    year = None
    if year_match:
        year = int(year_match.group(1))
        # Convert 2-digit to 4-digit year
        if year < 100:
            year = 2000 + year if year < 50 else 1900 + year

    # Try to find month
    month = None
    for month_name, month_num in months_map.items():
        if month_name in date_lower:
            month = month_num
            break

    return year, month


def extract_series_info(title: str) -> tuple[str, Optional[int]]:
    """
    Extract series volume from title
    Examples:
      - "Der Hypnotiseur (Band 1)" -> ("Der Hypnotiseur", 1)
      - "Liar (Band 3)" -> ("Liar", 3)
    """
    # Look for patterns like (Band X), (Fall X)
    series_patterns = [
        r'\(Band\s+(\d+)\)',
        r'\((\d+)\.\s*Fall\)',
        r'\(Fall\s+(\d+)\)',
    ]

    for pattern in series_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            volume = int(match.group(1))
            clean_title = re.sub(pattern, '', title).strip()
            return clean_title, volume

    return title, None


def extract_location_from_notes(notes: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract location info from notes if it looks like a place
    Returns (location, remaining_notes)
    Examples:
      - "Bergisch Gladbach" -> ("Bergisch Gladbach", None)
      - "Sydney" -> ("Sydney", None)
      - "Fall 2" -> (None, "Fall 2")
      - "3. Fall 😐" -> (None, "3. Fall 😐")
    """
    if not notes:
        return None, None

    notes = notes.strip()

    # Check if notes contain "Fall" or "Band" - these are not locations
    if re.search(r'\b(Fall|Band)\b', notes, re.IGNORECASE):
        return None, notes

    # Check if it looks like a location (single word or two words, no numbers/emojis)
    # List of known locations from the data
    known_locations = [
        'Bergisch Gladbach', 'Sydney', 'England', 'Frankreich', 'Berlin',
        'Autorenteam', 'Schweden', 'Göteborg', 'Baskenland – Spanien',
        'Bonn-Arzt und Wissenschaftler', 'Belfast', 'Köln'
    ]

    for location in known_locations:
        if notes.lower() == location.lower():
            return location, None

    # If notes contain emojis, numbers, or common note phrases, it's not a location
    if re.search(r'[😐👍]|\d+\.|zum |Esther', notes):
        return None, notes

    # If it's a single word or two words with no special chars, might be location
    if re.match(r'^[A-Za-zäöüÄÖÜß\s-]{2,30}$', notes) and len(notes.split()) <= 4:
        return notes, None

    return None, notes


def search_google_books(title: str, author: str) -> Optional[Dict]:
    """Search Google Books API for a book"""
    query = f"{title} {author}".strip()
    encoded_query = urllib.parse.quote(query)

    url = f"https://www.googleapis.com/books/v1/volumes?q={encoded_query}&maxResults=1"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'items' in data and len(data['items']) > 0:
            book_info = data['items'][0]['volumeInfo']

            result = {
                'google_books_id': data['items'][0]['id'],
                'description': book_info.get('description'),
                'publisher': book_info.get('publisher'),
                'published_date': book_info.get('publishedDate'),
                'page_count': book_info.get('pageCount'),
                'categories': book_info.get('categories', []),
                'language': book_info.get('language'),
                'isbn': None,
                'cover_url': None
            }

            # Extract ISBN
            if 'industryIdentifiers' in book_info:
                for identifier in book_info['industryIdentifiers']:
                    if identifier['type'] in ['ISBN_13', 'ISBN_10']:
                        result['isbn'] = identifier['identifier']
                        break

            # Extract cover URL
            if 'imageLinks' in book_info:
                if 'extraLarge' in book_info['imageLinks']:
                    result['cover_url'] = book_info['imageLinks']['extraLarge']
                elif 'large' in book_info['imageLinks']:
                    result['cover_url'] = book_info['imageLinks']['large']
                elif 'medium' in book_info['imageLinks']:
                    result['cover_url'] = book_info['imageLinks']['medium']
                elif 'thumbnail' in book_info['imageLinks']:
                    result['cover_url'] = book_info['imageLinks']['thumbnail']

                # Convert http to https
                if result['cover_url']:
                    result['cover_url'] = result['cover_url'].replace('http://', 'https://')

            return result

    except requests.RequestException as e:
        print(f"  ⚠ API error: {e}")
        return None

    return None


def process_book(book_data: Dict, fetch_missing: bool = True) -> Dict:
    """
    Process a single book entry from preparsed data
    """
    # Start with basic fields
    processed = {
        'author': book_data['author'],
        'title': book_data['title'],
    }

    # Extract series info from title
    clean_title, series_volume = extract_series_info(book_data['title'])
    processed['title'] = clean_title
    processed['series_volume'] = series_volume

    # Parse date
    year, month = parse_date(book_data.get('date_read'))
    processed['year'] = year
    processed['month'] = month

    # Handle notes - extract location if present
    notes = book_data.get('notes')
    location, remaining_notes = extract_location_from_notes(notes)
    processed['location'] = location
    processed['notes'] = remaining_notes

    # Use existing description if available
    processed['description'] = book_data.get('description')

    # Initialize fields that might come from Google Books
    processed['google_books_id'] = None
    processed['publisher'] = None
    processed['published_date'] = None
    processed['page_count'] = None
    processed['categories'] = []
    processed['language'] = None
    processed['isbn'] = None
    processed['cover_url'] = None

    # Fetch from Google Books API if description or cover is missing
    if fetch_missing and (not processed['description'] or not processed.get('cover_url')):
        print(f"  🔍 Fetching from Google Books API...")
        google_data = search_google_books(processed['title'], processed['author'])

        if google_data:
            # Only use Google data for fields that are empty
            if not processed['description'] and google_data['description']:
                processed['description'] = google_data['description']
                print(f"  ✓ Found description")

            if google_data['cover_url']:
                processed['cover_url'] = google_data['cover_url']
                print(f"  ✓ Found cover")

            # Always add metadata if available
            for key in ['google_books_id', 'publisher', 'published_date',
                       'page_count', 'categories', 'language', 'isbn']:
                if google_data.get(key):
                    processed[key] = google_data[key]
        else:
            print(f"  ✗ No data found in Google Books")

    return processed


def load_preparsed_files() -> List[Dict]:
    """Load all preparsed JSON files"""
    all_books = []
    preparsed_files = ['preparsed1.txt', 'preparsed2.txt', 'preparsed3.txt', 'preparsed4.txt']

    for filename in preparsed_files:
        filepath = Path(filename)
        if filepath.exists():
            print(f"\n📖 Loading {filename}...")
            with open(filepath, 'r', encoding='utf-8') as f:
                books = json.load(f)
                print(f"  Found {len(books)} books")
                all_books.extend(books)
        else:
            print(f"⚠ Warning: {filename} not found, skipping...")

    return all_books


def main(mode: str = None):
    """Main function"""
    print("="*60)
    print("📚 Book Library Parser - Preparsed Edition")
    print("="*60)

    # Load preparsed files
    raw_books = load_preparsed_files()

    if not raw_books:
        print("\n❌ Error: No books found in preparsed files!")
        return

    print(f"\n📊 Total books loaded: {len(raw_books)}")

    # Ask user about API fetching (if not provided via argument)
    if mode:
        choice = mode
    else:
        print("\n" + "="*60)
        print("Options:")
        print("  1. Quick parse (no API calls, use existing descriptions)")
        print("  2. Full enrichment (fetch missing data from Google Books API)")
        print("  3. Test mode (process first 10 books with API)")
        choice = input("\nEnter your choice (1, 2, or 3): ").strip()

    fetch_missing = False
    books_to_process = raw_books

    if choice == '2':
        fetch_missing = True
        print(f"\n🌐 Full enrichment mode - this will take ~{len(raw_books) * 0.5 / 60:.1f} minutes")
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            return
    elif choice == '3':
        fetch_missing = True
        books_to_process = raw_books[:10]
        print(f"\n🧪 Test mode - processing first 10 books")
    else:
        print(f"\n⚡ Quick parse mode - no API calls")

    # Process all books
    print("\n" + "="*60)
    print("Processing books...")
    print("="*60 + "\n")

    processed_books = []
    total = len(books_to_process)

    for i, book_data in enumerate(books_to_process, 1):
        print(f"[{i}/{total}] {book_data['author']}: {book_data['title']}")

        processed = process_book(book_data, fetch_missing=fetch_missing)
        processed_books.append(processed)

        # Rate limiting for API calls
        if fetch_missing and i < total:
            time.sleep(0.5)

    # Sort by date
    processed_books.sort(key=lambda x: (
        x['year'] if x['year'] else 9999,
        x['month'] if x['month'] else 99
    ))

    # Save to JSON
    output_file = 'books_database.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_books, f, ensure_ascii=False, indent=2)

    # Statistics
    print("\n" + "="*60)
    print("✅ Processing complete!")
    print("="*60)
    print(f"📁 Saved to: {output_file}")
    print(f"\n📊 Statistics:")
    print(f"  Total books: {len(processed_books)}")

    years = [b['year'] for b in processed_books if b['year']]
    if years:
        print(f"  Date range: {min(years)} - {max(years)}")

    descriptions = sum(1 for b in processed_books if b.get('description'))
    covers = sum(1 for b in processed_books if b.get('cover_url'))
    print(f"  Books with descriptions: {descriptions} ({descriptions/len(processed_books)*100:.1f}%)")
    print(f"  Books with covers: {covers} ({covers/len(processed_books)*100:.1f}%)")

    # Top authors
    authors = {}
    for book in processed_books:
        author = book['author']
        authors[author] = authors.get(author, 0) + 1

    print(f"\n📚 Top 10 authors:")
    top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10]
    for author, count in top_authors:
        print(f"  {author}: {count} books")

    print("="*60)


if __name__ == '__main__':
    import sys
    # Allow running with command line argument: python parse_preparsed.py 1
    mode = sys.argv[1] if len(sys.argv) > 1 else None
    main(mode)
