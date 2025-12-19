# 📚 Mamas Bibliothek - Book Library Project

A beautiful digital library showcasing 20 years of reading journey! This project parses book data from text files, enriches it with cover images and metadata from Google Books API, and presents it as a modern, searchable website.

## 🌟 Features

- **535+ Books** from 2006-2020
- **Automatic Cover Images** fetched from Google Books API
- **Search & Filter** by title, author, or year
- **Modern UI** with dark theme
- **Responsive Design** works on all devices
- **Personal Notes** preserved from original lists

## 📁 Project Structure

```
book-library/
├── books1.txt              # Original book list (2006-2013)
├── books2.txt              # Original book list (2014-2016)
├── books3.txt              # Original book list (2017-2020)
├── books4.txt              # Original book list (2017-2025)
├── parse_books.py          # Script to parse text files into JSON
├── fetch_covers.py         # Script to fetch cover images
├── books_database.json     # Parsed book data
├── books_enriched.json     # Book data with covers & metadata
├── index.html              # Main website
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Parse the Books

```bash
python3 parse_books.py
```

This will create `books_database.json` with 535 books.

### 2. Fetch Cover Images (Optional but Recommended)

```bash
python3 fetch_covers.py
```

Choose option 2 to process all books. This will:
- Fetch cover images from Google Books API
- Add descriptions, ISBNs, publishers, etc.
- Create `books_enriched.json`

**Note:** Processing all 535 books takes ~5-10 minutes due to API rate limiting.

### 3. View the Website

Open `index.html` in your browser, or:

```bash
python3 -m http.server 8000
```

Then visit: http://localhost:8000

## 🌐 Deploy to GitHub Pages

1. Commit all files to your repository:
```bash
git add .
git commit -m "Add book library website"
git push origin main
```

2. Enable GitHub Pages:
   - Go to repository Settings
   - Navigate to "Pages"
   - Set Source to "main branch"
   - Save

3. Your site will be live at: `https://your-username.github.io/book-library/`

## 📊 Statistics

- **Total Books:** 535
- **Time Range:** 2006-2020
- **Top Authors:**
  - Nicholas Sparks: 15 books
  - Tess Gerritsen: 15 books
  - Michael Robotham: 15 books
  - Ken Follett: 13 books
  - Sebastian Fitzek: 13 books

## 🛠️ Technical Details

### Parsing Logic

The parser handles various formats:
- Author: Title (Date) Notes
- Series information (Band X, Fall X)
- Location info for authors
- Personal notes and ratings

### API Integration

Uses Google Books API to fetch:
- Cover images
- Book descriptions
- ISBN numbers
- Publishers
- Categories
- Page counts

### Search & Filter

- Real-time search across titles and authors
- Filter by top 10 authors
- Responsive grid layout
- Smooth animations

## 📝 Original Format Example

```
Kepler, Lars (Bergisch Gladbach): Der Hypnotiseur (Band 1)
Sparks, Nicholas:  Zeit im Wind (Mai 06) zum heulen
```

## 🎨 Customization

To customize the website:

1. **Colors:** Edit CSS variables in `index.html`:
```css
:root {
    --primary: #6366f1;
    --background: #0f172a;
    --surface: #1e293b;
    /* ... */
}
```

2. **Layout:** Adjust grid columns in `.books-grid`:
```css
.books-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
}
```

## 🤝 Contributing

This is a personal project, but feel free to fork and adapt it for your own book collections!

## 📜 License

MIT License - Feel free to use and modify!

---

Made with ❤️ for Mama's 20-year reading journey
