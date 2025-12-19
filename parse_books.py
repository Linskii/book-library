#!/usr/bin/env python3
"""
Script to parse book files and create a structured JSON database
"""

import re
import json
from typing import List, Dict, Optional
from pathlib import Path


def parse_date(text: str) -> Optional[Dict[str, int]]:
    """Extract year and month from text"""
    if not text:
        return None

    # Common German month abbreviations
    months = {
        'jan': 1, 'januar': 1, 'feb': 2, 'februar': 2, 'märz': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'mai': 5, 'juni': 6, 'juli': 7, 'aug': 8,
        'august': 8, 'sep': 9, 'sept': 9, 'september': 9, 'okt': 10,
        'oktober': 10, 'nov': 11, 'november': 11, 'dez': 12, 'dezember': 12
    }

    text_lower = text.lower().strip()

    # Try to find year (2-digit or 4-digit)
    year_match = re.search(r'\b(20\d{2}|0[6-9]|1[0-9]|2[0-5])\b', text_lower)
    if year_match:
        year = int(year_match.group(1))
        # Convert 2-digit to 4-digit year
        if year < 100:
            year = 2000 + year if year < 50 else 1900 + year

        # Try to find month
        for month_name, month_num in months.items():
            if month_name in text_lower:
                return {'year': year, 'month': month_num}

        return {'year': year, 'month': None}

    return None


def extract_series_info(title: str) -> tuple:
    """Extract series information from title, return (clean_title, volume)"""
    # Look for patterns like (Band 1), (Fall 2), etc.
    series_patterns = [
        (r'\(Band\s+(\d+)\)', 'remove'),
        (r'\((\d+)\.\s*Fall\)', 'remove'),
        (r'\(Fall\s+(\d+)\)', 'remove'),
        (r'\s+\((\d+)\.\)', 'remove'),
    ]

    for pattern, action in series_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            volume = int(match.group(1))
            clean_title = re.sub(pattern, '', title).strip()
            return clean_title, volume

    return title, None


def parse_book_line(line: str) -> Optional[Dict]:
    """Parse a single book line and extract information"""
    line = line.strip()

    # Skip empty lines
    if not line:
        return None

    # Skip description blocks (they start with specific patterns)
    skip_patterns = [
        r'^>>',  # Quotes
        r'^\s*Als\s+',  # Description lines
        r'^\s*Ein\s+',  # Description lines
        r'^\s*In\s+',  # Description lines
        r'^\s*Sie\s+',  # Description lines
        r'^\s*Er\s+',  # Description lines
        r'^\s*Die\s+[A-Z][a-z]+\s+',  # "Die Geschichte..."
        r'^\s*Vom\s+',  # Description lines
        r'^\s*Mit\s+',  # Description lines
        r'^\s*Für\s+',  # Description lines
        r'^\s*Auf\s+',  # Description lines
        r'^\s*Seit\s+',  # Description lines
        r'^\s*Nach\s+',  # Description lines
        r'^\s*Während\s+',  # Description lines
        r'^\s*[A-Z][a-z]+,?\s+im\s+',  # "Berlin, im Sommer..."
    ]

    for pattern in skip_patterns:
        if re.match(pattern, line):
            return None

    # Skip lines that are too short to be book entries
    if len(line) < 15:
        return None

    # Main pattern: Author: Title (anything in parenthesis) trailing notes
    # Split by colon to get author and rest
    if ':' not in line:
        return None

    parts = line.split(':', 1)
    if len(parts) != 2:
        return None

    author_part = parts[0].strip()
    rest = parts[1].strip()

    # Extract location from author if present (e.g., "Kepler, Lars (Bergisch Gladbach)")
    location = None
    author_location_match = re.match(r'^(.+?)\s*\(([^)]+)\)$', author_part)
    if author_location_match:
        author = author_location_match.group(1).strip()
        location = author_location_match.group(2).strip()
    else:
        author = author_part

    # Now parse the rest: Title (date/info) notes
    # Find all parenthetical expressions
    parentheticals = re.findall(r'\(([^)]+)\)', rest)

    # Remove all parentheticals from rest to get base title + notes
    title_and_notes = re.sub(r'\([^)]+\)', '', rest).strip()

    # The title is everything up to common note patterns
    note_patterns = [
        r'\s+😐.*$',
        r'\s+TOP!.*$',
        r'\s+super!.*$',
        r'\s+nee!.*$',
        r'\s+zum heulen.*$',
        r'\s+-[^-]+-.*$',  # things in dashes like "-Heidi-"
        r'\s+selbst.*$',
    ]

    notes = None
    title = title_and_notes
    for note_pattern in note_patterns:
        match = re.search(note_pattern, title_and_notes, re.IGNORECASE)
        if match:
            notes = match.group(0).strip()
            title = re.sub(note_pattern, '', title_and_notes, flags=re.IGNORECASE).strip()
            break

    # Extract series info from title
    title, series_volume = extract_series_info(title)

    # Parse date from parentheticals
    date_info = None
    for paren in parentheticals:
        date_info = parse_date(paren)
        if date_info:
            break

    # If no date found, try the notes
    if not date_info and notes:
        date_info = parse_date(notes)

    book = {
        'author': author,
        'title': title.strip(),
        'location': location,
        'series_volume': series_volume,
        'year': date_info['year'] if date_info else None,
        'month': date_info['month'] if date_info else None,
        'notes': notes
    }

    # Skip if no actual title
    if not book['title'] or len(book['title']) < 2:
        return None

    return book


def parse_file(filepath: Path) -> List[Dict]:
    """Parse a single book file"""
    books = []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            # Remove line numbers (format: "     1→")
            line = re.sub(r'^\s*\d+→', '', line)

            book = parse_book_line(line)
            if book:
                books.append(book)

    return books


def main():
    """Main parsing function"""
    # Parse all book files
    all_books = []
    book_files = ['books1.txt', 'books2.txt', 'books3.txt', 'books4.txt']

    for filename in book_files:
        filepath = Path(filename)
        if filepath.exists():
            print(f"Parsing {filename}...")
            books = parse_file(filepath)
            all_books.extend(books)
            print(f"  Found {len(books)} books")

    print(f"\nTotal books parsed: {len(all_books)}")

    # Sort by year and month
    all_books.sort(key=lambda x: (
        x['year'] if x['year'] else 9999,
        x['month'] if x['month'] else 99
    ))

    # Save to JSON
    output_file = 'books_database.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_books, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(all_books)} books to {output_file}")

    # Print some statistics
    years = [b['year'] for b in all_books if b['year']]
    if years:
        print(f"\nDate range: {min(years)} - {max(years)}")

    authors = {}
    for book in all_books:
        author = book['author']
        authors[author] = authors.get(author, 0) + 1

    print(f"\nTop 10 authors:")
    top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10]
    for author, count in top_authors:
        print(f"  {author}: {count} books")


if __name__ == '__main__':
    main()
