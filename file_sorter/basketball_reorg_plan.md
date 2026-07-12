# Basketball Video Reorganization Plan

Date: 2026-07-10

## The Problem

The basketball notes folder (`~/documents/notes/hobbies/02-basketball`) has deep nesting — folders within folders within folders. Files get lost, duplicates appear because you forget where you put something, and generic filenames like `clip_1.mp4` or `Screen Recording 2026-04-13...` mean nothing outside their parent folder.

Example of current nesting:
```
02-basketball/
  game-film_breakdowns/
    game_highlights/
      harden_/
        clip_1.mp4      ← meaningless without "harden" context
        clip_2.mp4
      trae/
        trae_1.mp4
      little_man/
        clip_1.mp4      ← same name, different folder
  skills_shooting/
    vid_step-back/
      step_back1.mp4
    vid_pull_up/
      hip_flip.mp4
  skills_dribbling/
    vid_dribbling/
      ...
```

## The Goal

Flat category folders. One level deep. Mixed file types (videos, text, PDFs together). Let filenames carry the context, not folder depth. 



The key to sorting is that **taxonomy** is given,





```
02-basketball_b/
  skills_shooting/        ← .mp4, .txt, .pdf all here
  skills_dribbling/
  skills_driving/
  skills_defense/
  skills_post-play/
  team-concepts_plays/
  team-concepts_cutting/
  workouts_drills/
  game-film_breakdowns/
  misc/
```

## The Pipeline (4 scripts, 5 steps)

### Step 1: Dry-run flatten-rename

```bash
# Dry run (just shows the plan, nothing is copied)
python flatten_rename.py \
  ~/documents/notes/hobbies/02-basketball \
  ~/documents/notes/hobbies/02-basketball_b \
  Basketball

# With -i / --interactive: prompts you when no YAML route matches a folder
python flatten_rename.py \
  ~/documents/notes/hobbies/02-basketball \
  ~/documents/notes/hobbies/02-basketball_b \
  Basketball -i
```

This reads `archive_config.yaml` to understand the category names (called "routes"), then for every file:

1. If the file is **nested** (inside any subfolder), it **always** prepends folder context to the filename — the folder structure is about to disappear, so context must be baked into the name
2. If the file is at the **root level** and has a descriptive name (e.g. a coach clip), it stays unchanged
3. Walks up the directory tree looking for a folder name that matches a YAML route (by exact name or keyword match)
4. Collects the intermediate folders between the YAML route and the file as **context**
5. Bakes that context into the filename

The YAML route name itself is NOT added to the filename — that's redundant because `smart_archive.py` will sort it into that folder in the next step.

#### The `-i` (interactive) flag

When `flatten_rename.py` walks up a file's folder tree and **no folder matches any YAML route**, the default behavior is to silently use whatever folder names it finds as a prefix. With `-i`, it pauses and prompts you:

```
  No YAML route match for: /Users/.../reference_articles/analytics.txt
  Available routes:
    1. game-film_breakdowns
    2. game-notes
    3. misc
    4. reference
    5. rules
    6. skills_defense
    7. skills_dribbling
    ...
    s. skip (keep filename as-is)
    o. open file
  Choice for [reference_articles]:
```

- Type a **number** to pick a route as the prefix
- Type **s** to skip (keep the filename unchanged)
- Type **o** to open the file in its default app so you can see what it is before deciding
- Type any **custom text** to use as a prefix

Choices are **cached by folder** — once you pick for `reference_articles`, all files in that folder get the same prefix automatically.

#### Rename examples

| Original path | YAML route hit | Context folders | New filename |
|---|---|---|---|
| `game-film_breakdowns/game_highlights/harden_/clip_1.mp4` | `game-film_breakdowns` | game_highlights, harden | `game_highlights_harden_clip_1.mp4` |
| `skills_shooting/vid_step-back/step_back1.mp4` | `skills_shooting` | *(vid_ skipped)* | `skills_shooting_step_back1.mp4` |
| `skills_post-play/postup/Screen Recording 2024-12-16 at 2.05.51 PM.mp4` | `skills_post-play` | postup | `postup_2024-12-16_20551PM.mp4` |
| `Danny Cooper - Save this drill...mp4` | *(not generic)* | — | `Danny Cooper - Save this drill...mp4` (unchanged) |
| `reference_articles/vid_workouts/workout_1.mp4` | *(no route match)* | reference_articles | `reference_articles_workout_1.mp4` |

**Files with descriptive names (coach clips, YouTube downloads) are left untouched.** Only generic names get the folder context prepended.

#### Special rules
- `vid_*` and `video` wrapper folders are skipped (they add no meaning)
- Trailing underscores on folder names are stripped (`harden_` becomes `harden`)
- Screen Recording timestamps are compressed (`Screen Recording 2026-04-13 at 1.00.09 PM.mp4` becomes `{context}_2026-04-13_10009PM.mp4`)
- Filename collisions get a `_2`, `_3` suffix

### Step 2: Execute the flatten

Review the dry-run output. If it looks right:

```bash
python flatten_rename.py \
  ~/documents/notes/hobbies/02-basketball \
  ~/documents/notes/hobbies/02-basketball_b \
  Basketball --move
```

This **copies** (not moves) every file into `02-basketball_b/` as a single flat directory. The original `02-basketball/` is untouched.

### Step 3: Sort into category folders

```bash
python smart_archive.py \
  ~/documents/notes/hobbies/02-basketball_b \
  Basketball
  
python smart_archive.py \
  ~/documents/notes/hobbies/02-basketball_b \
  Basketball --move
```

This reads the same `archive_config.yaml` and matches each filename against keyword routes:

```yaml
Basketball:
  path: ~/documents/notes/hobbies/02-basketball_b
  routes:
    skills_shooting:
      - shooting
      - jumper
      - shot
      - pull up
      - step back
      - fade
    skills_dribbling:
      - dribble
      - handle
      - crossover
    skills_driving:
      - drive
      - finish
      - bump
      - layup
    # ... etc
    misc: []          # catchall for unmatched files
```

First keyword match wins. Dry-run by default — add `--move` to execute.

For files that don't match any keyword, `smart_archive.py` also supports `--content-aware` which sends a content preview to OpenAI for classification. Probably not needed for videos, but useful for `.txt` and `.pdf` files with ambiguous names.

### Step 4: Strip redundant prefixes

After sorting, many filenames start with the folder name they're already sitting in — that's redundant:

```
skills_dribbling/skills_dribbling_trae_1.mp4   ← "skills_dribbling" appears twice
game-film_breakdowns/game-film_breakdowns_harden_clip_1.mp4
```

```bash
# Dry run
python strip_prefix.py ~/documents/notes/hobbies/02-basketball_b

# Execute
python strip_prefix.py ~/documents/notes/hobbies/02-basketball_b --move
```

This renames in-place (no copy). For each subfolder, if a filename starts with `{folder_name}_`, that prefix is stripped:

```
skills_dribbling/skills_dribbling_trae_1.mp4  →  skills_dribbling/trae_1.mp4
game-film_breakdowns/game-film_breakdowns_commentary.md  →  game-film_breakdowns/commentary.md
```

Skips files where stripping would cause a collision with an existing file.

## Why this order matters

**Flatten-rename BEFORE sort.** If you sort first, `clip_1.mp4` has no keywords to match — it goes straight to `misc/`. By flattening first and baking `harden` into the filename, the sorter can now see `game_highlights_harden_clip_1.mp4` and match on `highlight` → `game-film_breakdowns/`.

## After this: Dropbox videos

The Dropbox basketball folder (`/videos/basketball`, 190 files) is not synced locally. To merge it into the same library:

### Option A: Full pipeline (scripted)

1. Download the Dropbox `/videos/basketball` folder to `~/Downloads/dropbox_basketball/`
2. Run the same pipeline — flatten-rename drops new files into `02-basketball_b`, then sort + strip

```bash
python flatten_rename.py ~/Downloads/dropbox_basketball ~/documents/notes/hobbies/02-basketball_b Basketball -i --move
python smart_archive.py ~/documents/notes/hobbies/02-basketball_b Basketball --move
python strip_prefix.py ~/documents/notes/hobbies/02-basketball_b --move
```

The flatten script checks for existing files in the destination — if `amenThompson1.mp4` already exists from local notes, the Dropbox copy becomes `amenThompson1_2.mp4` instead of overwriting.

### Option B: Manual Finder sorting with Quick Action

For hands-on sorting using the AppleScript Quick Action (move selected files to another Finder tab/window):

1. Download Dropbox videos to `~/Downloads/dropbox_basketball/`
2. Create the category folders from the YAML:

```bash
python create_folders.py ~/documents/notes/hobbies/02-basketball_b Basketball
```

This reads `archive_config.yaml` and creates all the route folders:

```
02-basketball_b/
  skills_shooting/
  skills_dribbling/
  skills_driving/
  skills_defense/
  skills_post-play/
  skills_passing/
  team-concepts_plays/
  team-concepts_cutting/
  workouts_drills/
  game-film_breakdowns/
  game-notes/
  reference/
  rules/
  web-project/
  misc/
```

3. Open Finder with multiple tabs — one for the downloaded Dropbox folder, others for each category folder
4. Select files, right-click → Quick Action to move them to the destination tab
5. Works well for the coach clips (Danny Cooper, Reid Ouse, etc.) where you can read the filename and know the category immediately

### Dedup across both collections

Before merging, check for byte-identical duplicates already spotted between the two:

| File | Local notes location | Dropbox location |
|---|---|---|
| `amenThompson1/2.mp4` | `skills_driving/drive/` | root |
| `fingerfoll.mp4` | `skills_layups/` | `individual/` |
| `notravel.mp4` | `rules/rules/` | root |
| `myself-jun-12.mp4` | `skills_shooting/` | `shooting/` |
| `spinmoveA1.pdf` | `skills_spin-move/` | root |
| Reid Ouse "Spin Seal" | — | `individual/` AND `latest/` |
| Danny Cooper "BUMPS" | — | `drills/` AND `twitter/` |

## Files involved

- `create_folders.py` — Create category folders from YAML routes
- `flatten_rename.py` — Step 1-2: YAML-aware flatten + rename
- `smart_archive.py` — Step 3: keyword-based sort into category folders
- `strip_prefix.py` — Step 4: remove redundant folder-name prefixes from filenames
- `archive_config.yaml` — shared config defining the Basketball routes
- This file (`basketball_reorg_plan.md`) — you're reading it
