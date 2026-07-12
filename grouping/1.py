import re
from collections import defaultdict

# Your filenames
files = [
    "12-07_TTTstanley_white_Italian_Game_.txt",
    "12-08_batonizurab_black_Ponziani_Opening_.txt",
    "12-08_ghabiiiix_black_Italian_Game_.txt",
    "12-08_MSY1986_black_Queen's_Pawn.txt",
    "12-08_TTTstanley_white_Italian_Game_.txt",
    "12-08_TTTstanley_white_Petrov's_Defense_.txt",
    "12-09_93myaj_black_Vienna_Gambit,.txt",
    "12-09_TTTstanley_white_Four_Knights.txt",
    "12-09_weradach_black_Four_Knights.txt",
    "12-18_francescodevivo_black_Italian_Game_.txt",
    "12-18_TTTstanley_white_Elephant_Gambit.txt",
    "12-18_TTTstanley_white_Philidor_Defense.txt",
    "12-18_TTTstanley_white_Sicilian_Defense_.txt",
    "12-19_gaps09_black_Queen's_Gambit.txt",
    "23_12-07_TTTstanley_white_Italian_Game_.txt",
    "chess_analysis_report_2025-12-07-15-00-36.txt",
    "chess_analysis_report_2025-12-07-18-39-13.txt"
]

# Parse filename function
def parse_filename(filename):
    # Skip analysis reports
    if filename.startswith("chess_analysis"):
        return {"type": "report", "filename": filename}
    
    # Pattern: DATE_OPPONENT_COLOR_OPENING_.txt
    match = re.match(r'(\d+-\d+|\d+_\d+-\d+)_(.+?)_(white|black)_(.+?)\.txt', filename)
    if match:
        return {
            "date": match.group(1),
            "opponent": match.group(2),
            "color": match.group(3),
            "opening": match.group(4).replace('_', ' ').strip(','),
            "filename": filename
        }
    return {"type": "unknown", "filename": filename}

# Group by color and opening
by_color_opening = defaultdict(list)
by_color = defaultdict(list)
by_opening = defaultdict(list)
reports = []

for file in files:
    parsed = parse_filename(file)
    
    if parsed.get("type") == "report":
        reports.append(file)
    elif "color" in parsed:
        color = parsed["color"]
        opening = parsed["opening"]
        
        by_color_opening[f"{color} - {opening}"].append(file)
        by_color[color].append(file)
        by_opening[opening].append(file)

# Display results
print("=" * 60)
print("GROUPED BY COLOR + OPENING:")
print("=" * 60)
for key in sorted(by_color_opening.keys()):
    print(f"\n{key.upper()} ({len(by_color_opening[key])} games):")
    for file in by_color_opening[key]:
        print(f"  - {file}")

print("\n" + "=" * 60)
print("GROUPED BY COLOR:")
print("=" * 60)
for color in ['white', 'black']:
    print(f"\n{color.upper()} ({len(by_color[color])} games):")
    for file in by_color[color]:
        print(f"  - {file}")

print("\n" + "=" * 60)
print("GROUPED BY OPENING:")
print("=" * 60)
for opening in sorted(by_opening.keys()):
    print(f"\n{opening} ({len(by_opening[opening])} games):")
    for file in by_opening[opening]:
        print(f"  - {file}")

if reports:
    print("\n" + "=" * 60)
    print("ANALYSIS REPORTS:")
    print("=" * 60)
    for report in reports:
        print(f"  - {report}")
