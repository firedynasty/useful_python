# Steps: Chinese Lyrics to Final Gloss CSV

## Step 0: Get the lyrics

Save the Chinese + Pinyin lyrics to `lyrics.txt` in this format:

```
想听 你听过的音乐
Xiǎng tīng nǐ tīng guò de yīn yuè
想看 你看过的小说
Xiǎng kàn nǐ kàn guò de xiǎo shuō

想到 你到过的地方
Xiǎng dào nǐ dào guò dì dì fāng
```

Alternating: Chinese line, Pinyin line. Blank lines between verses.

## Step 1: Translate lyrics via OpenAI

```
python lyrics_to_csv.py --input lyrics.txt --output gem_table.csv
```

Sends each verse to GPT-4o for English translation. Outputs a 3-column CSV: `Chinese`, `Pinyin`, `Translation`.

## Step 2: Flatten to paired lines

```
python make_adjusted.py --input gem_table.csv --output gem_adjusted.txt
```

Splits each verse cell by `\n`, pairs translation + pinyin line by line:

```
I want to listen to the music you've heard
Xiǎng tīng nǐ tīng guò de yīn yuè

I want to read the novels you've read
Xiǎng kàn nǐ kàn guò de xiǎo shuō
```

## Step 3: Generate word-by-word gloss via OpenAI

```
python generate_gloss.py --input gem_table.csv --output gem_preformatted.csv
```

Sends each verse to GPT-4o for word-by-word breakdown. Returns CSV: `Chinese`, `Pinyin`, `English meaning`.

## Step 4: Merge glosses with lyric lines

```
python merge_glosses.py --adjusted gem_adjusted.txt --gloss gem_preformatted.csv --output gem_output.csv
```

Two-pointer merge: inserts English + Pinyin above each gloss group, matched by last pinyin word.

## Quick Run

```bash
export OPENAI_API_KEY=sk-...
python lyrics_to_csv.py --input lyrics.txt --output gem_table.csv
python make_adjusted.py --input gem_table.csv --output gem_adjusted.txt
python generate_gloss.py --input gem_table.csv --output gem_preformatted.csv
python merge_glosses.py --adjusted gem_adjusted.txt --gloss gem_preformatted.csv --output gem_output.csv
```

## Pipeline Diagram

```
lyrics.txt  (Chinese + Pinyin)
     |
     | Step 1: lyrics_to_csv.py (OpenAI translates to English)
     v
gem_table.csv  (Chinese, Pinyin, Translation)
     |
     |--- Step 2: make_adjusted.py ---> gem_adjusted.txt
     |
     |--- Step 3: generate_gloss.py -> gem_preformatted.csv
     |                                       |
     +---------------------------------------+
                       |
                       | Step 4: merge_glosses.py
                       v
                gem_output.csv (final)
```
