#!/usr/bin/env python3
"""Convert CSV to a styled HTML table.

Usage: csvToHtml.py <input.csv> [output.html]

If output path is omitted, writes to stdout.
"""
import csv
import html
import os
import sys

CSS = """
:root { --bg-color: #ffffff; --text-color: #333333; }
html { font-size: 14px; background-color: var(--bg-color); color: var(--text-color); font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; }
body { margin: 0; padding: 30px; font-size: 1rem; line-height: 1.4; }
h1 { font-size: 1.6rem; margin-bottom: 1rem; }
table { border-collapse: collapse; width: 100%; overflow: auto; }
tr { border: 1px solid #dfe2e5; }
thead tr, tr:nth-child(2n) { background-color: #f8f8f8; }
th { font-weight: bold; border: 1px solid #dfe2e5; padding: 6px 13px; text-align: left; white-space: nowrap; }
td { border: 1px solid #dfe2e5; padding: 6px 13px; }
a { color: #4183C4; }
""".strip()

HTML_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>{css}</style>
<title>{title}</title>
</head>
<body>
<h1>{title}</h1>
{table}
</body>
</html>
"""


def csv_to_html(csv_path):
    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return '<p>Empty CSV file.</p>'

    # First row as header
    headers = rows[0]
    data = rows[1:]

    thead = '<tr>' + ''.join(f'<th>{html.escape(h)}</th>' for h in headers) + '</tr>'
    tbody_rows = []
    for row in data:
        cells = ''.join(f'<td>{html.escape(c)}</td>' for c in row)
        tbody_rows.append(f'<tr>{cells}</tr>')
    tbody = '\n'.join(tbody_rows)

    return f'<table>\n<thead>{thead}</thead>\n<tbody>\n{tbody}\n</tbody>\n</table>'


def main():
    if len(sys.argv) < 2:
        print("Usage: csvToHtml.py <input.csv> [output.html]", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    title = os.path.splitext(os.path.basename(input_path))[0]
    table = csv_to_html(input_path)
    result = HTML_TEMPLATE.format(css=CSS, title=html.escape(title), table=table)

    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Done: {sys.argv[2]}")
    else:
        sys.stdout.write(result)


if __name__ == '__main__':
    main()
