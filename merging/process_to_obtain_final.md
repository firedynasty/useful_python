# Process to Obtain Final korean_output.csv

## Overview

Full pipeline: start with Korean song lyrics, generate a word-by-word gloss via OpenAI, then merge the gloss back with the lyric lines to produce a final study CSV.

## Full Pipeline

### Step 0: Obtain the lyrics table

Start with an HTML lyrics table (`lyrics_grouped_table.html`) containing three columns: Romanization, Korean, Translation. Each row is a verse/section with multiple lines joined by `<br>`. This can be sourced from lyric sites or created manually.

Export or convert the HTML table to `korean_table.csv` with two columns: `Romanization` and `Translation`.

### Step 1: Generate the word-by-word gloss via OpenAI

**Recommended approach:** Send each verse's Korean text + romanization to GPT and ask it to break down every word/morpheme.

```
export OPENAI_API_KEY=sk-...
python generate_gloss.py --input korean_table.csv --output "korean -preformatted.csv"
```

**Prompt strategy for GPT:**

Give it one verse at a time (not the whole song at once) to keep output focused. For each verse, provide the Korean text and romanization, then ask:

> Break down each word/morpheme in this Korean verse. For each word return:
> - Korean (the word as written)
> - Romanization
> - English meaning (include particle/grammar notes in parentheses)
>
> Group by verse section (Verse 1, Pre-Chorus, Chorus, etc.).
> Return as CSV rows: Korean,Romanization,English meaning

**Model recommendation:** `gpt-4o` gives the best accuracy for Korean morphological analysis. `gpt-4o-mini` works for common vocabulary but may miss nuanced particles or contracted forms.

**Tips for better gloss output:**
- Include the romanization in your prompt so GPT's romanization stays consistent with the lyrics table (avoids `doego` vs `dwego` mismatches later)
- Ask GPT to preserve song order
- Ask it to include section headers (Verse 1, Pre-Chorus, etc.) as separator rows
- For particles attached to stems (e.g. 별이라도 = 별 + 이라도), tell GPT to split them into separate rows

**Output:** `korean -preformatted.csv` - three columns (`Korean`, `Romanization`, `English meaning`), section headers as rows, words in song order, no sentence-level separators between groups.

### Step 2: Flatten the lyrics table (`make_adjusted.py`)

```
python make_adjusted.py
```

Reads `korean_table.csv` and splits each multiline cell by `\n`. Pairs up each romanization line with its English translation line and writes them out as:

```
English translation
romanization

English translation
romanization
```

**Output:** `korean_table_adjusted.txt` - a flat file with 54 lyric line pairs, each pair separated by a blank line.

### Step 3: Merge glosses with lyric lines (`merge_glosses.py`)

```
python merge_glosses.py
```

Uses two pointers to walk through both files in order:

1. **Lyric pointer** - moves through `korean_table_adjusted.txt` pairs top to bottom
2. **CSV pointer** - moves through `korean -preformatted.csv` gloss rows top to bottom

For each lyric pair:
- Extract the **last word** of the romanization line (e.g. `boyeosseulkka` from `byeorirado geureoke boyeosseulkka`)
- Insert the English + romanization as 2 new rows into column 1 of the output
- Consume gloss rows from the CSV until hitting a row whose romanization (column B) matches that last word
- If no match is found ahead, the 2 lines are still inserted and the CSV pointer stays where it is (this produces 4 lines back to back when two unmatched pairs are consecutive)

This is the key matching logic: the last romanization word of a sentence uniquely identifies where a gloss group ends. Once matched, those lyric lines are "sliced out" (consumed) so repeated sections like the chorus match to the correct instance.

### Step 4: GPT verification (optional)

If `OPENAI_API_KEY` is set, the script sends the full output to GPT to double-check that each gloss group's words actually belong to the lyric line above them. GPT reports any mismatches as JSON.

## Output Format

`korean_output.csv` with three columns: `Korean`, `Romanization`, `English meaning`

```
Would even a star look like that?,,
byeorirado geureoke boyeosseulkka,,
별,byeol,star
이라도,irado,even / at least (particle)
그렇게,geureoke,like that / in that way
보였을까,boyeosseulkka,would it have appeared / looked?
Your eyes are locked in thoughts,,
saenggage jamgin nunppit,,
생각,saenggage,thought / thinking (에: locative — 'in thought')
에,e,in / at (locative particle)
잠긴,jamgin,submerged / lost in (adjective)
눈빛,nunppit,eye-light / gaze / look in the eyes
```

## Known Edge Cases

- **Duplicate last words**: Words like `gata` (seems like), `shipeo` (want), `molla` (don't know) appear as the last word in multiple lyric lines. The sequential two-pointer approach handles this by consuming in order, but occasionally a word matches slightly early. GPT verification catches these.
- **No-gloss pairs**: Lines like "Gimme gimme gimme gimme gimme love" or "Baby please just stay, just stay" have no Korean word glosses. These appear as just 2 lines (English + romanization) with no gloss rows underneath.
- **Romanization spelling differences**: Minor variations between the CSV and the lyrics table (e.g. `doego` vs `dwego`, `boyineun` vs `boineun`) can cause missed matches. GPT verification can catch and correct these.

## Quick Reference

```
Lyrics HTML/source
       |
       v
   korean_table.csv  (Romanization, Translation columns)
       |
       |---> Step 1: GPT gloss ----> "korean -preformatted.csv" (Korean, Romanization, English meaning)
       |
       |---> Step 2: make_adjusted.py ----> korean_table_adjusted.txt (flat english/romanization pairs)
       |                                         |
       |                                         v
       +-----------------------------------------+
                        |
                        v
              Step 3: merge_glosses.py
                        |
                        v
               korean_output.csv (final)
```
