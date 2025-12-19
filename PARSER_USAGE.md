# 📖 Parser Usage Guide

## New Parser for Preparsed Files

The `parse_preparsed.py` script works with your manually preparsed JSON files and makes it super easy to generate the final book database!

## 🚀 Quick Start

### Option 1: Quick Parse (No API Calls)
Uses only the data from your preparsed files - fast and no internet required!

```bash
python3 parse_preparsed.py 1
```

**Use this when:**
- You just want to normalize the data structure
- Your preparsed files already have all the descriptions
- You want a quick test run

### Option 2: Full Enrichment (With API)
Fetches missing cover images and metadata from Google Books API

```bash
python3 parse_preparsed.py 2
```

**Use this when:**
- You want to add book covers
- You want to fill in missing descriptions
- You want additional metadata (ISBN, publisher, page count, etc.)

**Note:** Processing all 238 books takes ~2 minutes due to API rate limiting (0.5s delay between requests)

### Option 3: Test Mode
Process just the first 10 books with API enrichment

```bash
python3 parse_preparsed.py 3
```

**Use this when:**
- Testing the API integration
- Checking if the enrichment works correctly

## 📊 What It Does

The parser:

1. **Loads** all 4 preparsed files (preparsed1.txt through preparsed4.txt)
2. **Parses dates** from formats like:
   - "April 06" → year: 2006, month: 4
   - "Januar 2025" → year: 2025, month: 1
   - "2015-11-06" → year: 2015, month: 11
3. **Extracts series info** from titles:
   - "Der Hypnotiseur (Band 1)" → title: "Der Hypnotiseur", volume: 1
4. **Separates locations** from notes:
   - Notes: "Sydney" → location: "Sydney", notes: null
   - Notes: "3. Fall 😐" → location: null, notes: "3. Fall 😐"
5. **Keeps your mum's notes** intact (they're precious!)
6. **Enriches missing data** from Google Books API (optional)
7. **Generates** books_database.json sorted by date

## 📁 Output Format

```json
{
  "author": "Kepler, Lars",
  "title": "Der Hypnotiseur",
  "series_volume": 1,
  "year": null,
  "month": null,
  "location": "Bergisch Gladbach",
  "notes": null,
  "description": "Vor den Toren Stockholms...",
  "google_books_id": "xyz123",
  "publisher": "Lübbe",
  "published_date": "2010",
  "page_count": 512,
  "categories": ["Fiction", "Thriller"],
  "language": "de",
  "isbn": "9783404161522",
  "cover_url": "https://books.google.com/..."
}
```

## 🎯 Current Statistics

- **Total books:** 238
- **Date range:** 2006-2025
- **Books with descriptions:** 219 (92%)
- **Top authors:** Nicholas Sparks, Charlotte Link, Tess Gerritsen (8 books each)

## 🔧 Updating the Website

After running the parser, just open [index.html](index.html) in your browser - it automatically loads the new `books_database.json`!

## 💡 Tips

- The parser preserves all your mum's personal notes (emojis, comments like "zum heulen", etc.)
- Series information is automatically extracted and stored separately
- Location info (like "Sydney", "Berlin") is smartly detected and separated from other notes
- The Google Books API is free but has rate limits, so be patient with full enrichment

## 📝 Notes

- The old parsers ([parse_books.py](parse_books.py) and [fetch_covers.py](fetch_covers.py)) are kept for reference
- Your original book files (books1-4.txt) remain untouched
- The preparsed files are the source of truth now
