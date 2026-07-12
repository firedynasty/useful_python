# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based web scraping repository focused on extracting and processing content from various websites. The codebase includes three main categories of scrapers:

1. **General Web Scrapers** - Extract article content from web pages using Chrome remote debugging
2. **NBA Basketball Data Scrapers** - Sports analytics focused on scraping NBA game statistics and four factors data from Basketball Reference
3. **AI-Powered Document Analyzers** - Streamlit applications that analyze documents using local Ollama models

## Key Commands

### Chrome Remote Debugging Setup (Required for most scrapers)
```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug_profile

# Windows  
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

# Linux
google-chrome --remote-debugging-port=9222
```

### General Web Scraping
- **Simple content extraction**: `python 01-scrape_single.py`
- **Batch scraping with file output**: `python 04i-scraper.py` (saves to `./scraped_from_websites/`)
- **Interactive clipboard scraper**: `python 04-scraper.py`

### NBA Data Scraping (in basketball-reference subdirectories)
- **Extract four factors data**: `python scrape_with_argument8.py nba_schedule.csv`
- **Batch mode**: `python scrape_with_argument8.py nba_schedule.csv --batch`
- **Limited scraping**: `python scrape_with_argument8.py nba_schedule.csv --limit 5`

### AI Document Analysis
- **Career coach app**: `streamlit run career-coach.py`
- **Economic report analyzer**: `streamlit run economic-report.py`
- **Medical report analyzer**: `streamlit run medical-report.py`

## Architecture & Code Patterns

### Chrome Integration Pattern
All web scrapers use Chrome remote debugging via Selenium WebDriver with a consistent pattern:
- Connect to Chrome instance running on port 9222
- Use BeautifulSoup for HTML parsing
- Apply content selectors to extract main article content
- Clean and format text using html2text

### Content Extraction Strategy
The scrapers use a hierarchical approach to find main content:
1. Try specific CSS selectors (article, .article-content, .main-content, etc.)
2. Fall back to body content if specific selectors fail
3. Remove unwanted elements (scripts, styles, iframes)
4. Convert to plain text with markdown cleanup

### NBA Data Processing Pipeline
For basketball data scraping:
1. Load game schedule from CSV
2. Extract four factors statistics from box score URLs
3. Create individual game CSV files
4. Combine into comprehensive datasets
5. Generate one-row-per-game reporting format

### AI Integration Pattern
Streamlit apps follow a consistent architecture:
- Use OpenAI-compatible client pointing to local Ollama server (localhost:11434)
- Support multiple document formats (PDF, DOCX, TXT)
- Stream responses for real-time display
- Organize analysis into tabs for different perspectives

## Development Guidelines

### Dependencies
Core libraries used across the project:
- `selenium` + `webdriver-manager` for browser automation
- `beautifulsoup4` for HTML parsing
- `html2text` for content conversion
- `pandas` for data manipulation (NBA scrapers)
- `streamlit` + `openai` for AI applications
- `pyperclip` for clipboard operations

### Error Handling
- Always include try/except blocks with specific error messages
- Provide troubleshooting steps for Chrome connection issues
- Implement retry logic for web scraping operations
- Use graceful fallbacks when content extraction fails

### File Organization
- Individual scrapers are numbered sequentially (01-, 02-, 04-, etc.)
- NBA-specific code is organized in `basketball-reference/` subdirectories
- Scraped content is saved to `./scraped_from_websites/` with timestamped filenames
- Data processing outputs go to `data/` subdirectories

### Code Style
- Use snake_case for variables and functions
- Include descriptive docstrings with Args/Returns sections
- 4-space indentation, lines generally under 100 characters
- Import order: standard library, third-party, local modules
- Add metadata (URL, title, date) to scraped content for context