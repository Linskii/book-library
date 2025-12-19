#!/usr/bin/env python3
"""
Quick script to upgrade existing cover URLs to higher quality (zoom=5)
"""

import json

# Load existing database
with open('books_database.json', 'r', encoding='utf-8') as f:
    books = json.load(f)

# Upgrade cover URLs
upgraded = 0
for book in books:
    if book.get('cover_url') and 'zoom=1' in book['cover_url']:
        book['cover_url'] = book['cover_url'].replace('zoom=1', 'zoom=5')
        upgraded += 1

# Save back
with open('books_database.json', 'w', encoding='utf-8') as f:
    json.dump(books, f, ensure_ascii=False, indent=2)

print(f"✅ Upgraded {upgraded} cover URLs to higher quality (zoom=5)")
print(f"📊 Total books: {len(books)}")
print(f"🖼️  Books with covers: {sum(1 for b in books if b.get('cover_url'))}")
