# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run script: `python process_texts.py -i <input_directory> -o <output_file>`
- Lint code: `pylint process_texts.py`
- Type check: `mypy process_texts.py`

## Code Style Guidelines
- **Imports**: Standard library first, then third-party, then local
- **Formatting**: PEP 8, 4-space indentation, max line length 100
- **Types**: Include docstrings with parameter types and return types
- **Naming**: snake_case for variables/functions, CamelCase for classes
- **Error Handling**: Use try/except with specific exceptions
- **Comments**: Minimal but descriptive, explain "why" not "what"
- **Function Design**: Follow single responsibility principle
- **File Encoding**: UTF-8 to support multiple languages (Chinese, Hebrew, etc.)