# File Sorter Pipeline

Three scripts, run in order. All commands assume you're in the `file_sorter/` directory.

---

## Step 1 — Propose folder topics (first time or when refreshing)

OpenAI reads your filenames and drafts topic subfolders for the YAML config.

```bash
# Preview the proposed YAML — prints to terminal, nothing written yet
python propose_config.py ~/Downloads/iran Iran

# Write it to archive_config.yaml (replaces existing Iran block if present)
python propose_config.py ~/Downloads/iran Iran --append
```

Re-run `--append` any time the folder has changed — it replaces the existing block, never duplicates.

---

## Step 2 — Sort files into topic subfolders

```bash
# Preview the sort plan (dry run, no files moved)
python smart_archive.py ~/Downloads/iran Iran

# Execute — dedupes Chrome (1) copies, moves files into topic subfolders
python smart_archive.py ~/Downloads/iran Iran --move
```

What it does:
- Deletes `filename (1).md` copies that are byte-identical to `filename.md`
- Routes each file by filename keyword → matching topic subfolder in YAML
- Unmatched files go to the fallback subfolder (e.g. `misc/`)

After this your folder looks like:
```
~/Downloads/iran/
  scorecards/
  strategy/
  doctrine/
  misc/          ← unmatched files land here
  ...
```

### Optional: content-aware routing for unmatched files

For files that landed in `misc/` because the filename gave no signal, this samples
their content and asks `gpt-4o` to pick the right topic:

```bash
python smart_archive.py ~/Downloads/iran Iran --content-aware --move
```

Only files with `matched: no match` get an API call — everything else is free.

---

## Step 3 — (Optional) Distill into concise summaries

`gpt-4o` rewrites each `.md`/`.txt` — keeping facts/claims/takeaways, cutting filler —
into a parallel `concise/` tree. Originals are never touched.

### 3a — See what will be distilled

```bash
python distill_folder.py ~/Downloads/iran --list
```

Prints every file with its full path and character count:
```
/Users/stanleytan/Downloads/iran/scorecards/day_11_scorecard.md (8423 chars)
/Users/stanleytan/Downloads/iran/strategy/strategy.md (3201 chars)
...
```

### 3b — Protect files you don't want distilled

Copy any full paths from the listing above into `prevent_distill.txt` in the source folder:

```
# ~/Downloads/iran/prevent_distill.txt
/Users/stanleytan/Downloads/iran/misc/iran_score_card_prompt.md
/Users/stanleytan/Downloads/iran/iran-war/iranwar-intel.txt
```

Those files are automatically moved out before distillation runs and moved back in after.

### 3c — Run distillation

```bash
python distill_folder.py ~/Downloads/iran
```

Output after running:
```
~/Downloads/iran/
  scorecards/day_11_scorecard.md            ← original, untouched
  concise/scorecards/day_11_scorecard.md    ← distilled copy (30–50% length)
  concise/strategy/strategy.md
  concise/_index.md                         ← table of contents
  ...
```

At the end it prints a full listing of what was written:
```
Concise output:
/Users/stanleytan/Downloads/iran/concise/scorecards/day_11_scorecard.md (487 chars)
/Users/stanleytan/Downloads/iran/concise/strategy/strategy.md (312 chars)
...
```

Re-running skips files already in `concise/`. Use `--overwrite` to redo them.

### 3d — Open in Typora

```bash
typoraed ~/Downloads/iran/concise/scorecards
typoraed ~/Downloads/iran/concise/strategy
```

---

## Quick reference

| Script | What it does |
|---|---|
| `propose_config.py` | AI reads filenames → drafts YAML topic subfolders |
| `smart_archive.py` | Dedupes + routes files into topic subfolders |
| `distill_folder.py` | AI rewrites each file into a slim `concise/` copy |

Config lives in `archive_config.yaml` — one subject block per folder you sort.

### All flags

**propose_config.py**
```
python propose_config.py <source> <subject>            # print proposed YAML
python propose_config.py <source> <subject> --append   # write to archive_config.yaml
python propose_config.py <source> <subject> --model gpt-4o-mini  # cheaper model
```

**smart_archive.py**
```
python smart_archive.py <source> <subject>                    # dry run
python smart_archive.py <source> <subject> --move             # execute
python smart_archive.py <source> <subject> --content-aware    # AI fallback for unmatched
python smart_archive.py <source> <subject> --no-dedupe        # skip duplicate removal
python smart_archive.py --list                                 # show all subjects in config
```

**distill_folder.py**
```
python distill_folder.py <source>              # distill all files
python distill_folder.py <source> --list       # show files + char counts, nothing distilled
python distill_folder.py <source> --dry-run    # show plan, no API calls
python distill_folder.py <source> --overwrite  # redo already-distilled files
python distill_folder.py <source> --limit 3    # test on first 3 files (cost check)
```
