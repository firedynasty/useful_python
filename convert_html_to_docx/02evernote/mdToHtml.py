#!/usr/bin/env python3
"""Convert Markdown to Typora-style HTML.

Usage: mdToHtml.py <input.md> [output.html]

If output path is omitted, writes to stdout.
"""
import sys
import re
import html

# ---------------------------------------------------------------------------
# Typora HTML template  (Github theme)
# ---------------------------------------------------------------------------

TYPORA_CSS = r"""
:root { --bg-color: #ffffff; --text-color: #333333; --select-text-bg-color: #B5D6FC; --select-text-font-color: auto; --monospace: "Lucida Console",Consolas,"Courier",monospace; }
html { font-size: 14px; background-color: var(--bg-color); color: var(--text-color); font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; }
body { margin: 0px; padding: 0px; font-size: 1rem; line-height: 1.428571; overflow-x: hidden; }
body.typora-export { padding-left: 30px; padding-right: 30px; }
#write { margin: 0 auto; height: auto; width: inherit; word-break: normal; overflow-wrap: break-word; position: relative; padding-top: 36px; }
img { max-width: 100%; height: auto; vertical-align: middle; }
h1, h2, h3, h4, h5, h6 { position: relative; margin-top: 1rem; margin-bottom: 1rem; font-weight: bold; line-height: 1.4; }
h1 { font-size: 2rem; }
h2 { font-size: 1.8rem; }
h3 { font-size: 1.6rem; }
h4 { font-size: 1.4rem; }
h5 { font-size: 1.2rem; }
h6 { font-size: 1rem; }
p { margin-top: 1rem; margin-bottom: 1rem; }
a { color: #4183C4; cursor: pointer; }
blockquote { margin: 1rem 0px; border-left: 4px solid #dfe2e5; padding: 0 15px; color: #777777; }
ul, ol { padding-left: 30px; }
li { margin: 0px; position: relative; }
li p { margin: 0.5rem 0px; }
table { padding: 0; word-break: initial; border-collapse: collapse; border-spacing: 0px; width: 100%; overflow: auto; }
table tr { border: 1px solid #dfe2e5; margin: 0; padding: 0; }
table tr:nth-child(2n), thead { background-color: #f8f8f8; }
table th { font-weight: bold; border: 1px solid #dfe2e5; border-bottom: 0; margin: 0; padding: 6px 13px; }
table td { border: 1px solid #dfe2e5; margin: 0; padding: 6px 13px; }
hr { height: 2px; padding: 0; margin: 16px 0; background-color: #e7e7e7; border: 0 none; overflow: hidden; }
code, pre, tt { font-family: var(--monospace); }
code { background-color: #f3f4f4; padding: 0 2px; border: 1px solid #e7eaed; border-radius: 3px; font-size: 0.9em; }
pre { white-space: pre-wrap; }
pre code { background-color: transparent; border: none; padding: 0; font-size: inherit; }
.md-fences { background-color: #f8f8f8; border: 1px solid #e7eaed; border-radius: 3px; margin-bottom: 15px; margin-top: 15px; padding: 8px 4px 6px 4px; font-size: 0.9em; display: block; }
mark { background: rgb(255, 255, 0); color: rgb(0, 0, 0); }
""".strip()

TYPORA_THEME_CSS = r"""
:root { --side-bar-bg-color: #fafafa; --control-text-color: #777; }
html { font-size: 16px; -webkit-font-smoothing: antialiased; }
body { font-family: "Open Sans","Clear Sans","Helvetica Neue",Helvetica,Arial,sans-serif; color: rgb(51, 51, 51); line-height: 1.6; }
#write { max-width: 860px; margin: 0 auto; padding: 30px; padding-bottom: 100px; }
@media only screen and (min-width: 1400px) { #write { max-width: 1024px; } }
a { color: #4183C4; }
h1, h2, h3, h4, h5, h6 { position: relative; margin-top: 1rem; margin-bottom: 1rem; font-weight: bold; line-height: 1.4; }
h1 { font-size: 2.25em; line-height: 1.2; border-bottom: 1px solid #eee; }
h2 { font-size: 1.75em; line-height: 1.225; border-bottom: 1px solid #eee; }
h3 { font-size: 1.5em; line-height: 1.43; }
h4 { font-size: 1.25em; }
h5 { font-size: 1em; }
h6 { font-size: 1em; color: #777; }
p, blockquote, ul, ol, dl, table { margin: 0.8em 0; }
li>ol, li>ul { margin: 0 0; }
hr { height: 2px; padding: 0; margin: 16px 0; background-color: #e7e7e7; border: 0 none; }
ul, ol { padding-left: 30px; }
blockquote { border-left: 4px solid #dfe2e5; padding: 0 15px; color: #777777; }
table tr { border: 1px solid #dfe2e5; margin: 0; padding: 0; }
table tr:nth-child(2n), thead { background-color: #f8f8f8; }
table th { font-weight: bold; border: 1px solid #dfe2e5; border-bottom: 0; margin: 0; padding: 6px 13px; }
table td { border: 1px solid #dfe2e5; margin: 0; padding: 6px 13px; }
.md-fences, code, tt { border: 1px solid #e7eaed; background-color: #f8f8f8; border-radius: 3px; padding: 2px 4px 0px 4px; font-size: 0.9em; }
code { background-color: #f3f4f4; padding: 0 2px 0 2px; }
.md-fences { margin-bottom: 15px; margin-top: 15px; padding-top: 8px; padding-bottom: 6px; }
""".strip()

HTML_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset='UTF-8'><meta name='viewport' content='width=device-width initial-scale=1'>
<style type='text/css' id="style-base">{base_css}</style>
<link rel='stylesheet' href='https://fonts.googleapis.com/css?family=Open+Sans:400italic,700italic,700,400&amp;subset=latin,latin-ext' type='text/css' />
<style type='text/css' id="style-theme_css">{theme_css}</style>
<title>{title}</title>
</head>
<body class='typora-export'><div class='typora-export-content'>
<div id='write' class=''>{body}</div></div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Markdown → HTML conversion
# ---------------------------------------------------------------------------

def _inline(text):
    """Convert inline markdown (bold, italic, code, images, links) to HTML."""
    # Images: ![alt](src)
    text = re.sub(
        r'!\[([^\]]*)\]\(([^)]+)\)',
        r'<img src="\2" alt="\1">',
        text,
    )
    # Links: [text](url)
    text = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        r'<a href="\2">\1</a>',
        text,
    )
    # Inline code: `code`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # Bold+italic: ***text*** or ___text___
    text = re.sub(r'(\*{3}|_{3})(.+?)\1', r'<strong><em>\2</em></strong>', text)
    # Bold: **text** or __text__
    text = re.sub(r'(\*{2}|_{2})(.+?)\1', r'<strong>\2</strong>', text)
    # Italic: *text* or _text_  (but not inside words for _)
    text = re.sub(r'(?<!\w)\*([^*]+)\*(?!\w)', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', r'<em>\1</em>', text)
    # Strikethrough: ~~text~~
    text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)
    # Highlight: ==text==
    text = re.sub(r'==(.+?)==', r'<mark>\1</mark>', text)
    # Bare URLs (not already in a tag)
    text = re.sub(
        r'(?<!["\'>=/])(https?://\S+)',
        r'<a href="\1">\1</a>',
        text,
    )
    return text


def md_to_html(md_text):
    """Convert markdown text to Typora-style inner HTML."""
    lines = md_text.split('\n')
    out = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Blank line → empty paragraph (Typora uses <p>&nbsp;</p>)
        if line.strip() == '':
            # Only emit &nbsp; if between content (mimics Typora spacing)
            out.append('<p>&nbsp;</p>')
            i += 1
            continue

        # Fenced code block: ``` or ~~~
        m = re.match(r'^(`{3,}|~{3,})\s*(.*)', line)
        if m:
            fence = m.group(1)[0]
            fence_len = len(m.group(1))
            lang = m.group(2).strip()
            code_lines = []
            i += 1
            while i < len(lines):
                if re.match(r'^' + re.escape(fence) * fence_len, lines[i]):
                    i += 1
                    break
                code_lines.append(html.escape(lines[i]))
                i += 1
            lang_attr = f' class="language-{html.escape(lang)}"' if lang else ''
            code_html = '\n'.join(code_lines)
            out.append(f'<pre class="md-fences md-end-block" lang="{html.escape(lang)}"><code{lang_attr}>{code_html}</code></pre>')
            continue

        # Heading: # ... ######
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            text = _inline(html.escape(m.group(2)))
            out.append(f'<h{level}><span>{text}</span></h{level}>')
            i += 1
            continue

        # Horizontal rule: ---, ***, ___
        if re.match(r'^(\*{3,}|-{3,}|_{3,})\s*$', line):
            out.append('<hr />')
            i += 1
            continue

        # Unordered list
        if re.match(r'^(\s*)[*+-]\s', line):
            items, i = _collect_list(lines, i, ordered=False)
            out.append(_render_list(items, ordered=False))
            continue

        # Ordered list
        if re.match(r'^(\s*)\d+\.\s', line):
            items, i = _collect_list(lines, i, ordered=True)
            out.append(_render_list(items, ordered=True))
            continue

        # Blockquote
        if line.startswith('>'):
            bq_lines = []
            while i < len(lines) and lines[i].startswith('>'):
                bq_lines.append(re.sub(r'^>\s?', '', lines[i]))
                i += 1
            inner = md_to_html('\n'.join(bq_lines))
            out.append(f'<blockquote>{inner}</blockquote>')
            continue

        # Table
        if i + 1 < len(lines) and re.match(r'^\|?\s*-+[\s|:-]+$', lines[i + 1]):
            table_lines = []
            while i < len(lines) and ('|' in lines[i] or re.match(r'^\s*-+[\s|:-]+$', lines[i])):
                table_lines.append(lines[i])
                i += 1
            out.append(_render_table(table_lines))
            continue

        # Regular paragraph — collect consecutive non-blank, non-special lines
        para_lines = []
        while i < len(lines) and lines[i].strip() != '':
            # Stop if next line is a special block start
            if re.match(r'^(#{1,6}\s|`{3,}|~{3,}|>\s|(\*{3,}|-{3,}|_{3,})\s*$|\|)', lines[i]) and para_lines:
                break
            if re.match(r'^(\s*)[*+-]\s', lines[i]) and para_lines:
                break
            if re.match(r'^(\s*)\d+\.\s', lines[i]) and para_lines:
                break
            para_lines.append(lines[i])
            i += 1
        text = '<br/>\n'.join(_inline(html.escape(l)) for l in para_lines)
        out.append(f'<p><span>{text}</span></p>')

    return '\n'.join(out)


def _collect_list(lines, i, ordered):
    """Collect list items, handling continuation lines."""
    items = []
    pattern = r'^(\s*)\d+\.\s+(.*)' if ordered else r'^(\s*)[*+-]\s+(.*)'
    while i < len(lines):
        m = re.match(pattern, lines[i])
        if m:
            items.append(m.group(2))
            i += 1
        elif lines[i].strip() == '' or not items:
            break
        elif lines[i].startswith('  ') or lines[i].startswith('\t'):
            # Continuation of previous item
            items[-1] += '\n' + lines[i].strip()
            i += 1
        else:
            break
    return items, i


def _render_list(items, ordered):
    tag = 'ol' if ordered else 'ul'
    inner = ''.join(f'<li><p>{_inline(html.escape(item))}</p></li>' for item in items)
    return f'<{tag}>{inner}</{tag}>'


def _render_table(table_lines):
    """Render a markdown table to HTML."""
    if len(table_lines) < 2:
        return ''
    headers = [c.strip() for c in table_lines[0].strip('|').split('|')]
    # Skip separator line (index 1)
    rows = []
    for line in table_lines[2:]:
        cells = [c.strip() for c in line.strip('|').split('|')]
        rows.append(cells)

    thead = '<tr>' + ''.join(f'<th>{_inline(html.escape(h))}</th>' for h in headers) + '</tr>'
    tbody_rows = []
    for row in rows:
        tbody_rows.append('<tr>' + ''.join(f'<td>{_inline(html.escape(c))}</td>' for c in row) + '</tr>')
    tbody = ''.join(tbody_rows)
    return f'<table><thead>{thead}</thead><tbody>{tbody}</tbody></table>'


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def convert(md_text, title=''):
    body = md_to_html(md_text)
    return HTML_TEMPLATE.format(
        base_css=TYPORA_CSS,
        theme_css=TYPORA_THEME_CSS,
        title=html.escape(title),
        body=body,
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: mdToHtml.py <input.md> [output.html]", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    with open(input_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    # Derive title from filename
    import os
    title = os.path.splitext(os.path.basename(input_path))[0]

    result = convert(md_text, title=title)

    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"✓ Wrote {sys.argv[2]}")
    else:
        sys.stdout.write(result)


if __name__ == '__main__':
    main()
