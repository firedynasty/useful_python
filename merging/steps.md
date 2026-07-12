# Steps: Colorcodedlyrics to Final Gloss CSV

## Step 0: Save the HTML

Go to colorcodedlyrics.com, inspect the page, copy the 3-column `<div class="wp-block-columns">` section containing Romanization, Hangul, and Translation. Save it to a `.html` file.

```
celebrity.html
```

## Step 1: Parse HTML to CSV

```
python colorcode_to_csv.py --input celebrity.html --output celebrity_table.csv
```

Extracts the 3 WordPress columns into a CSV with columns: `Romanization`, `Korean`, `Translation`. Each row is one verse. Lines within a verse are preserved as newlines inside the cell.

## Step 2: Flatten to paired lines

```
python make_adjusted.py --input celebrity_table.csv --output celebrity_adjusted.txt
```

Splits each multiline cell by `\n` and pairs them line by line:

```
The world's edge
sesange moseori

Sharply angled
gubujeonghage keobeorin
```

## Step 3: Generate word-by-word gloss via OpenAI

```
export OPENAI_API_KEY=sk-...
python generate_gloss.py --input celebrity_table.csv --output celebrity_preformatted.csv
```

Sends each verse's Korean + romanization to GPT-4o. Returns a CSV with columns: `Korean`, `Romanization`, `English meaning` — one row per word/morpheme, particles split into separate rows.

## Step 4: Merge glosses with lyric lines

```
python merge_glosses.py --adjusted celebrity_adjusted.txt --gloss celebrity_preformatted.csv --output celebrity_output.csv
```

Two-pointer walk: for each lyric pair, inserts the English + romanization as 2 rows, then consumes gloss rows until the last romanization word matches. If no match, the 2 lines are inserted and the pointer stays put.

If `OPENAI_API_KEY` is set, automatically verifies all matches with GPT.

## Pipeline Diagram

```
colorcodedlyrics.com
        |
        | (copy 3-column div, save to .html)
        v
   celebrity.html
        |
        | Step 1: colorcode_to_csv.py
        v
   celebrity_table.csv
        |
        |--- Step 2: make_adjusted.py ---> celebrity_adjusted.txt
        |
        |--- Step 3: generate_gloss.py -> celebrity_preformatted.csv
        |                                        |
        +----------------------------------------+
                         |
                         | Step 4: merge_glosses.py
                         v
                  celebrity_output.csv (final)
```

## Quick Run (all steps)

```bash
python colorcode_to_csv.py --input celebrity.html --output celebrity_table.csv
python make_adjusted.py --input celebrity_table.csv --output celebrity_adjusted.txt
export OPENAI_API_KEY=sk-...
python generate_gloss.py --input celebrity_table.csv --output celebrity_preformatted.csv
python merge_glosses.py --adjusted celebrity_adjusted.txt --gloss celebrity_preformatted.csv --output celebrity_output.csv
```
