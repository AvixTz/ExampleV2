# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Native Ad Studio is a web-based tool for creating native advertising content by extracting and manipulating article content from URLs. It features a Flask backend for web scraping and a single-page HTML/CSS/JavaScript frontend.

## Architecture

### Backend (server.py)
- Flask web server serving both API endpoints and static files
- Single extraction endpoint `/api/extract` that scrapes article content using BeautifulSoup
- Content extraction pipeline:
  1. Fetches HTML with custom User-Agent headers
  2. Extracts title using multiple selector fallbacks (h1, .entry-title, etc.)
  3. Extracts subtitle from meta tags or h2 elements
  4. Finds main image from Open Graph tags or article images
  5. Collects all images with filtering (minimum size 80x80, excludes icons/logos)
  6. Parses content blocks (paragraphs, headings, images, blockquotes) from main content container
- Returns structured JSON with title, subtitle, mainImage, favicon, images array, and content blocks

### Frontend (static/index.html)
- Single-file HTML application with embedded CSS and JavaScript
- RTL/Hebrew language support (lang="he", dir="rtl")
- Two-column grid layout: 360px sidebar + main canvas
- Features include URL extraction, content editing, image selection, and native ad creation

## Commands

### Setup
```bash
pip install -r requirements.txt
```

### Run Server
```bash
python server.py
```
Server runs on http://localhost:5000 with debug mode enabled.

## Key Dependencies
- Flask 3.0.0 - Web framework
- Flask-CORS 4.0.0 - Cross-origin resource sharing
- requests 2.31.0 - HTTP client for fetching URLs
- beautifulsoup4 4.12.2 - HTML parsing
- lxml 4.9.3 - HTML/XML parser for BeautifulSoup

## Important Implementation Details

### Content Extraction Selectors
When modifying extraction logic in [server.py](server.py), note the selector priority order:
- Title: h1 → .entry-title → .post-title → .article-title → title
- Subtitle: meta[name="description"] → meta[property="og:description"] → .entry-summary → h2 → .subtitle
- Main image: meta[property="og:image"] → meta[name="twitter:image"] → .featured-image img → .post-thumbnail img → article img
- Content container: .entry-content → .post-content → article → .content → .post-body

### Image Filtering Rules
Images are filtered based on:
- Minimum dimensions of 80x80 pixels (when width/height attributes present)
- URL patterns containing 'icon', 'logo', 'avatar', 'emoji', 'ads', 'banner' only excluded if under 150x150
- Lazy-loading attributes checked: src, data-src, data-lazy-src, data-original

### Content Block Types
The extraction returns structured content blocks with types:
- `image` - Image URLs with alt text
- `heading` - H1-H4 elements with text longer than 10 characters
- `quote` - Blockquotes with text longer than 20 characters
- `text` - Paragraphs with text longer than 30 characters
