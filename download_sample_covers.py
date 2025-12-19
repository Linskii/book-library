#!/usr/bin/env python3
"""
Download a few sample covers to inspect image quality
"""

import json
import requests
from pathlib import Path

# Create samples directory
samples_dir = Path('sample_covers')
samples_dir.mkdir(exist_ok=True)

# Load database
with open('books_database.json', 'r', encoding='utf-8') as f:
    books = json.load(f)

# Get first 5 books with covers
books_with_covers = [b for b in books if b.get('cover_url')][:5]

print("Downloading sample covers...\n")

for i, book in enumerate(books_with_covers, 1):
    author = book['author'].replace('/', '-')
    title = book['title'].replace('/', '-')[:30]
    filename = f"{i}_{author}_{title}.jpg"
    filepath = samples_dir / filename

    print(f"{i}. Downloading: {author} - {title}")

    try:
        response = requests.get(book['cover_url'], timeout=10)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"   ✓ Saved to: {filepath}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

print(f"\n✅ Done! Check the '{samples_dir}' folder to inspect image quality")
