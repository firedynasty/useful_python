# Scripture Memorization Quiz

A Python CLI tool for practicing scripture memorization. Paste in numbered verses, listen to them read aloud, then recite and get graded.

## Requirements

- macOS (uses `pbpaste` for clipboard and `say` for text-to-speech)
- Python 3
- For `--bulk` mode only: `pip install openai` and `export OPENAI_API_KEY=sk-...`

## Usage

### Default Mode (No AI)

```bash
python scripture_quiz.py
```

1. Choose to load scripture from clipboard or paste it in
2. Type a verse number to hear it read aloud (as many times as you want)
3. Press Enter to start the quiz
4. Recite one verse at a time (paste from your speech-to-text app)
5. Get graded instantly - no internet needed

### Bulk Mode (Uses OpenAI)

```bash
python scripture_quiz.py --bulk
```

Recite all verses in one go (e.g. "1 blessed is the man 2 but his delight..."). OpenAI splits your recitation by verse number, then each verse is graded individually.

## Scripture Format

Each verse number must be on its own line, followed by the verse text:

```
1
Blessed is the man who doesn't walk in the counsel of the wicked, nor stand on the path of sinners, nor sit in the seat of scoffers;

2
but his delight is in Yahweh's law. On his law he meditates day and night.

3
He will be like a tree planted by the streams of water, that produces its fruit in its season, whose leaf also does not wither. Whatever he does shall prosper.
```

Numbering does not need to start at 1. For example, verses 6-9 work fine.

## Grading

- Uses longest common subsequence to compare your words against the original
- Case-insensitive, ignores punctuation
- Shows percentage score, missed words, and a review of any verse below 100%
- Verses you skip (press Enter with no input) are marked as Skipped

## Example Session

```
=== Scripture Memorization Quiz ===

Use clipboard for scripture? (y/n): y

Loaded from clipboard (312 chars)

Found 3 verses: 1, 2, 3
----------------------------------------

Listen to verse # (or Enter to start quiz): 1
  Reading verse 1...

Listen to verse # (or Enter to start quiz):

--- Verse 1 ---
Your recitation: blessed is the man who doesnt walk in the counsel of the wicked
  85% - Great!
  Missed words: nor, stand, path, sinners, nor, sit, seat, scoffers

--- Verse 2 ---
Your recitation:
  Skipped

--- Verse 3 ---
Your recitation: he will be like a tree planted by the streams of water
  50% - Keep practicing
  Missed words: that, produces, its, fruit, in, its, season, whose, leaf, also, does, not, wither, whatever, he, does, shall, prosper

========================================
RESULTS
========================================
  Verse 1: 85%
  Verse 2: Skipped
  Verse 3: 50%

  Overall: 45%
```
