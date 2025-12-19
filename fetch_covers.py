#!/usr/bin/env python3
"""
Script to fetch book covers and metadata from Google Books API
"""

import json
import requests
import time
from pathlib import Path
from typing import Dict, Optional
import urllib.parse


def search_google_books(title: str, author: str) -> Optional[Dict]:
    """Search Google Books API for a book"""
    # Clean up the query
    query = f"{title} {author}".strip()
    encoded_query = urllib.parse.quote(query)

    url = f"https://www.googleapis.com/books/v1/volumes?q={encoded_query}&maxResults=1"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'items' in data and len(data['items']) > 0:
            book_info = data['items'][0]['volumeInfo']

            # Extract relevant information
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
                # Try to get the largest available image
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
        print(f"  Error fetching data for '{title}': {e}")
        return None

    return None


def enrich_books(books: list, delay: float = 0.5) -> list:
    """Enrich book data with information from Google Books API"""
    enriched_books = []
    total = len(books)

    print(f"Fetching data for {total} books...")
    print("This may take a while. Please be patient!\n")

    for i, book in enumerate(books, 1):
        print(f"[{i}/{total}] {book['author']}: {book['title']}")

        # Make a copy of the book
        enriched_book = book.copy()

        # Search Google Books
        google_data = search_google_books(book['title'], book['author'])

        if google_data:
            # Merge the data
            enriched_book.update(google_data)
            if google_data['cover_url']:
                print(f"  ✓ Found cover image")
            else:
                print(f"  ⚠ No cover image found")
        else:
            print(f"  ✗ No data found")
            # Add empty fields
            enriched_book.update({
                'google_books_id': None,
                'description': None,
                'publisher': None,
                'published_date': None,
                'page_count': None,
                'categories': [],
                'language': None,
                'isbn': None,
                'cover_url': None
            })

        enriched_books.append(enriched_book)

        # Rate limiting - be nice to the API
        if i < total:
            time.sleep(delay)

    return enriched_books


def main():
    """Main function"""
    # Load the books database
    db_file = Path('books_database.json')
    if not db_file.exists():
        print("Error: books_database.json not found!")
        print("Please run parse_books.py first.")
        return

    with open(db_file, 'r', encoding='utf-8') as f:
        books = json.load(f)

    print(f"Loaded {len(books)} books from database\n")

    # Ask user if they want to process all books or just a sample
    print("Options:")
    print("  1. Process first 10 books (for testing)")
    print("  2. Process all books")
    choice = input("\nEnter your choice (1 or 2): ").strip()

    if choice == '1':
        books = books[:10]
        print(f"\nProcessing first 10 books for testing...\n")
    else:
        print(f"\nProcessing all {len(books)} books...\n")

    # Enrich the books
    enriched_books = enrich_books(books)

    # Save enriched data
    output_file = 'books_enriched.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enriched_books, f, ensure_ascii=False, indent=2)

    # Statistics
    covers_found = sum(1 for b in enriched_books if b.get('cover_url'))
    descriptions_found = sum(1 for b in enriched_books if b.get('description'))

    print(f"\n" + "="*50)
    print(f"Processing complete!")
    print(f"Saved to: {output_file}")
    print(f"\nStatistics:")
    print(f"  Total books: {len(enriched_books)}")
    print(f"  Covers found: {covers_found} ({covers_found/len(enriched_books)*100:.1f}%)")
    print(f"  Descriptions found: {descriptions_found} ({descriptions_found/len(enriched_books)*100:.1f}%)")
    print("="*50)


if __name__ == '__main__':
    main()
