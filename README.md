# useful_python

Backup of Python utility scripts for text processing, media conversion, language learning, and automation.

## Categories

### Text/Document Processing
- `extract_from_pdf/` — Extract text from PDFs
- `extract_from_pdf_as_images/` — Convert PDF pages to images then OCR
- `extract_from_scanned_images/` — OCR via OpenAI/Claude APIs
- `extract_code_from_files/` — Pull code blocks from documents
- `convert_docx_to_text/` — DOCX to plain text
- `convert_html_to_docx/` — HTML to DOCX
- `convert_html_to_txt/` — HTML to text
- `split_md_file_by_header/` — Split markdown by headings
- `make_md_file/` — Generate markdown files
- `make_json_from_text/` — Text to JSON conversion
- `makePdfFromTxt.py` — Plain text to PDF

### Media/Video
- `create_subtitles/` — Generate subtitles for videos
- `create_videos_from/` — Create videos from images/text
- `create_language_video/` — Language learning videos with TTS
- `create_language_video_2/` — Enhanced multilingual video creation
- `add_subtitle_image/` — Burn subtitles into images
- `video_editor/` — Video editing utilities
- `make_video_galleries/` — Generate HTML video galleries
- `py-audio-capture/` — Audio recording utilities

### Language Learning
- `textToSpeech/` — TTS with Kokoro, Google, and system voices
- `transcribe_audio/` — Speech-to-text (Whisper, Groq, Google)
- `memorize/` — Scripture/text memorization tool
- `merging/` — Merge translations with glosses (Spanish, Filipino, Hebrew, Cantonese, Mandarin)
- `grab_transcript/` — Pull transcripts from media

### Data Processing
- `break_up_csvs/` — Split large CSVs
- `make_csvs_smaller_by_random/` — Random sample from CSVs
- `make_csvs_to_json/` — CSV to JSON
- `xlsx_to_csvs/` — Excel to CSV conversion
- `grouping/` — Group/categorize data
- `file_sorter/` — Sort and organize files

### Web/Scraping
- `53-webpage_scraper/` — Web scrapers with AI summarization
- `grab_bible/` — Bible text API fetcher
- `grab_shakespeare/` — Shakespeare text fetcher
- `getDropBoxLinks/` — Dropbox link retrieval
- `local_server_redirect/` — Local dev server utilities

### Productivity
- `chat_with_openai/` — Terminal ChatGPT interface
- `navigate_computer/` — AI-powered folder navigation (Ollama)
- `compare_resume/` — Resume skill matcher
- `mental_math/` — Mental math practice
- `rename_files_folders_with_prefix/` — Batch rename utility
- `create_strong_password.py` — Password generator
- `generateQRCode.py` — QR code generator

### Presentations
- `make_powerpoint_slides/` — Generate PowerPoint from content
- `make_powerpoint_worship/` — Worship slides generator
- `make_powerpoint_resize_first/` — Image resize + PowerPoint

## Notes

- API keys are read from environment variables (not hardcoded)
- Media files (audio, video, images, PDFs) are gitignored — only scripts are backed up
- Credential files (service_account_key.json, etc.) are gitignored
