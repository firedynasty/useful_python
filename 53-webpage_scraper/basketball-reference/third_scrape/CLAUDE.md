# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- **Run Scraper**: `python scrape_with_argument7.py nba_schedule.csv`
- **Run with Limit**: `python scrape_with_argument7.py nba_schedule.csv --limit 5` 
- **Batch Mode**: `python scrape_with_argument7.py nba_schedule.csv --batch`
- **Combine Data**: `python data/01ins-combine_four_factors.py --four-factors-dir ./data/four_factors --schedule nba_schedule.csv --output nba_report.csv`
- **Convert to ML Format**: `python data/04ins-convert-to-ml-format.py --input nba_report.csv --output converted_report.csv`
- **Filter Schedule**: `python ins05-parse_down_nba_schedule.py nba_schedule.csv nba_report.csv`

## Code Style Guidelines

- **Imports**: Standard order is: built-in libraries, third-party libraries, local modules
- **Docstrings**: Use descriptive docstrings for functions with Args/Returns sections
- **Error Handling**: Use try/except blocks with specific exception handling and detailed error messages
- **Variable Naming**: Use snake_case for variables and functions, clear descriptive names
- **Type Hints**: Not currently used but could be added gradually
- **Formatting**: 4-space indentation, line length generally under 100 characters
- **Comments**: Comment complex logic, not obvious behavior
- **Data Processing**: Use pandas for data manipulation, DataFrame operations preferred over loops