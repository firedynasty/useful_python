# File Sorter

AI-powered file organizer that deduplicates, routes, and distills `.md`/`.txt` files into topic subfolders using OpenAI.

## The Problem

You have a folder with 75+ files — Chrome download duplicates, mixed topics, no structure. Opening them all in Typora is unwieldy.

## The Solution

Three scripts that turn a messy folder into organized, distilled reading material:

```
~/Downloads/iran/           ~/Downloads/iran/
  day_11_scorecard.md          scorecards/day_11_scorecard.md
  day_11_scorecard (1).md      strategy/strategy.md
  strategy.md          →       doctrine/keenan_doctrine.md
  keenan_doctrine.md           concise/scorecards/day_11_scorecard.md  (distilled)
  iran_war.md                  concise/strategy/strategy.md            (distilled)
  ...75 files                  ...organized into topic subfolders
```

## Requirements

```bash
pip install openai pyyaml
```

Set your API key:
```bash
export OPENAI_API_KEY=sk-...
```

## Usage

### Step 1 — Propose folder topics

OpenAI reads your filenames and drafts topic subfolders for the YAML config.

```bash
# Preview the proposed YAML
python propose_config.py ~/Downloads/iran Iran

# Write it to archive_config.yaml
python propose_config.py ~/Downloads/iran Iran --append
```

Re-running `--append` replaces the existing subject block — never duplicates.

### Step 2 — Sort files

```bash
# Dry run — preview the sort plan
python smart_archive.py ~/Downloads/iran Iran

# Execute — dedupes and moves files
python smart_archive.py ~/Downloads/iran Iran --move
```

This will:
- Delete `filename (1).md` copies that are byte-identical to `filename.md`
- Route each file into its YAML-defined topic subfolder
- Send unmatched files to the fallback subfolder (e.g. `misc/`)

#### Content-aware routing

For files that landed in `misc/` because the filename gave no signal, add `--content-aware` to sample file contents and ask `gpt-4o` to pick the right topic:

```bash
python smart_archive.py ~/Downloads/iran Iran --content-aware --move
```

Only unmatched files get an API call — keyword matches are free.

### Step 3 — (Optional) Distill into concise summaries

`gpt-4o` rewrites each file into a "good-to-know" version — keeping facts, cutting filler. Originals are never touched.

```bash
# List all files with full paths + char counts
python distill_folder.py ~/Downloads/iran --list

# Run distillation
python distill_folder.py ~/Downloads/iran
```

#### Protecting files from distillation

Copy paths from `--list` output directly into `prevent_distill.txt` in the source folder — the `(N chars)` suffix is stripped automatically:

```
# ~/Downloads/iran/prevent_distill.txt
/Users/stanleytan/Downloads/iran/misc/iran_score_card_prompt.md (487 chars)
/Users/stanleytan/Downloads/iran/iran-war/iranwar-intel.txt (1203 chars)
```

Protected files are moved out before distillation and restored after.

## Scripts

| Script | Purpose |
|---|---|
| `propose_config.py` | AI drafts YAML topic subfolders from filenames |
| `smart_archive.py` | Dedupe + route files into topic subfolders |
| `distill_folder.py` | AI distills each file into a slim `concise/` copy |
| `summarize_file.py` | Content reader (supports `.md`, `.txt`, `.pdf`, `.docx`, `.rtf`) |

## Config

`archive_config.yaml` holds one subject block per folder you sort:

```yaml
Iran:
  path: /Users/stanleytan/Downloads/iran
  routes:
    scorecards:
      - scorecard
      - day_
    doctrine:
      - keenan_doctrine
      - kennan_doctrine
    strategy:
      - strategy
      - objectives
    misc: []  # fallback — empty list catches unmatched files
```

Keywords are matched as case-insensitive substrings against filenames. First match wins. One route with an empty list `[]` acts as the fallback.

## All Flags

```
propose_config.py <source> <subject>
  --append              Write/replace subject block in archive_config.yaml
  --model MODEL         OpenAI model (default: gpt-4o)

smart_archive.py <source> <subject>
  --move                Execute (default is dry run)
  --content-aware       AI fallback for filename-unmatched files
  --content-model MODEL Model for content-aware (default: gpt-4o)
  --content-chars N     Chars to sample per file (default: 500)
  --no-dedupe           Skip Chrome duplicate removal
  --list                Show all subjects in config

distill_folder.py <source>
  --list                Show full paths + char counts, no distilling
  --dry-run             Show plan, no API calls
  --overwrite           Redo already-distilled files
  --limit N             Process first N files only (cost testing)
  --model MODEL         OpenAI model (default: gpt-4o)
  --out PATH            Custom output folder (default: <source>/concise)
```

## License

MIT
