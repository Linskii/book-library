#!/usr/bin/env python3
"""
Quick script to upgrade existing cover URLs to higher quality (zoom=5)
"""

import json

# Load existing database
with open('books_database.json', 'r', encoding='utf-8') as f:
    books = json.load(f)

# Upgrade cover URLs to highest quality
upgraded = 0
import re
for book in books:
    if book.get('cover_url'):
        # Replace any zoom level with zoom=50 (ultra-high resolution!)
        old_url = book['cover_url']
        book['cover_url'] = re.sub(r'zoom=\d+', 'zoom=50', book['cover_url'])
        if old_url != book['cover_url']:
            upgraded += 1

# Save back
with open('books_database.json', 'w', encoding='utf-8') as f:
    json.dump(books, f, ensure_ascii=False, indent=2)

print(f"✅ Upgraded {upgraded} cover URLs to ultra-high quality (zoom=50)")
print(f"📊 Total books: {len(books)}")
print(f"🖼️  Books with covers: {sum(1 for b in books if b.get('cover_url'))}")
