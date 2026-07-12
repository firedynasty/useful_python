# Steps: Hebrew Lyrics to Final Gloss CSV

## Step 0: Get the lyrics

Save romanized Hebrew lyrics to `lyrics.txt`. Section headers like `[Verse 1]` are supported.

## Step 1: Translate + get Hebrew script via OpenAI

```
export OPENAI_API_KEY=sk-...
python lyrics_to_csv.py --input lyrics.txt --output hebrew_table.csv
```

Sends each verse to GPT-4o to get Hebrew script + English translation. Outputs: `Romanization`, `Hebrew`, `Translation`.

## Step 2: Flatten to paired lines

```
python make_adjusted.py --input hebrew_table.csv --output hebrew_adjusted.txt
```

## Step 3: Generate word-by-word gloss via OpenAI

```
python generate_gloss.py --input hebrew_table.csv --output hebrew_preformatted.csv
```

## Step 4: Merge glosses with lyric lines

```
python merge_glosses.py --adjusted hebrew_adjusted.txt --gloss hebrew_preformatted.csv --output hebrew_output.csv
```

## Quick Run

```bash
export OPENAI_API_KEY=sk-...
python lyrics_to_csv.py --input lyrics.txt --output hebrew_table.csv
python make_adjusted.py --input hebrew_table.csv --output hebrew_adjusted.txt
python generate_gloss.py --input hebrew_table.csv --output hebrew_preformatted.csv
python merge_glosses.py --adjusted hebrew_adjusted.txt --gloss hebrew_preformatted.csv --output hebrew_output.csv
```
