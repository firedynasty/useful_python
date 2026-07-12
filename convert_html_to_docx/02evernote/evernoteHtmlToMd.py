#!/usr/bin/env python3
"""Extract text from an Evernote HTML export into Markdown.

Usage: evernote_to_md.py <input.html> [output.md]

If output path is omitted, writes to stdout.
"""
import sys
import re
from html.parser import HTMLParser


class EvernoteExtractor(HTMLParser):
    # Tags whose contents (and the tag itself) we ignore entirely.
    # Void elements (no closing tag) must NOT be listed here, since they
    # would bump in_skip without ever decrementing.
    SKIP_TAGS = {'style', 'script', 'svg', 'symbol', 'icons',
                 'head', 'g', 'defs', 'clippath', 'mask'}
    # Void elements: nothing inside, no closing tag. Just ignore quietly.
    VOID_TAGS = {'meta', 'link', 'br', 'hr', 'img', 'input', 'area',
                 'base', 'col', 'embed', 'param', 'source', 'track', 'wbr',
                 'path', 'use', 'circle', 'rect', 'line', 'polygon',
                 'polyline', 'ellipse', 'stop'}

    def __init__(self):
        super().__init__()
        self.stack = []           # list of (tag, classes)
        self.elements = []        # collected output items in order
        self.h1_texts = []        # raw h1 contents (for title/url)
        self.in_skip = 0
        self.in_codeblock = 0     # depth counter for <en-codeblock>
        self.codeblock_lines = [] # lines collected inside current code block
        self._codeblock_buf = []  # text buffer for current line in code block
        self.current = None       # {type, text, depth}

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID_TAGS:
            return
        if tag in self.SKIP_TAGS:
            self.in_skip += 1
            return
        if self.in_skip:
            return

        attrs_d = dict(attrs)
        classes = (attrs_d.get('class') or '').split()

        if tag == 'en-codeblock':
            self.in_codeblock += 1
            self.codeblock_lines = []
            return
        if self.in_codeblock:
            # Inside a code block, track divs for newline separation
            return

        self.stack.append((tag, classes))

        if self.current:
            return  # already collecting; descendants just contribute text

        if tag in ('h1', 'h2', 'h3', 'h4'):
            self.current = {'type': tag, 'text': [], 'depth': len(self.stack)}
        elif tag == 'div' and 'para' in classes:
            in_list = any('list-content' in c for (_t, c) in self.stack[:-1])
            self.current = {
                'type': 'list-item' if in_list else 'para',
                'text': [],
                'depth': len(self.stack),
            }

    def handle_startendtag(self, tag, attrs):
        if tag in self.SKIP_TAGS or self.in_skip:
            return
        if self.current and tag == 'br':
            self.current['text'].append('\n')

    def handle_endtag(self, tag):
        if tag in self.VOID_TAGS:
            return
        if tag == 'en-codeblock':
            if self.in_codeblock > 0:
                self.in_codeblock -= 1
            if self.in_codeblock == 0 and self.codeblock_lines:
                # Strip trailing empty lines
                while self.codeblock_lines and not self.codeblock_lines[-1].strip():
                    self.codeblock_lines.pop()
                code_text = '\n'.join(self.codeblock_lines)
                self.elements.append(('codeblock', code_text))
                self.codeblock_lines = []
            return
        if self.in_codeblock:
            # Each closing </div> inside a code block marks end of a line
            if tag == 'div':
                self.codeblock_lines.append(
                    ''.join(self._codeblock_buf) if hasattr(self, '_codeblock_buf') else '')
                self._codeblock_buf = []
            return
        if tag in self.SKIP_TAGS:
            if self.in_skip > 0:
                self.in_skip -= 1
            return
        if self.in_skip:
            return

        # If this close matches the opening depth of what we're collecting, flush.
        if self.current and len(self.stack) == self.current['depth']:
            self._flush()

        # Pop matching tag from stack
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack.pop(i)
                break

    def handle_data(self, data):
        if self.in_skip:
            return
        if self.in_codeblock:
            if not hasattr(self, '_codeblock_buf'):
                self._codeblock_buf = []
            self._codeblock_buf.append(data)
            return
        if self.current:
            self.current['text'].append(data)

    def _flush(self):
        if not self.current:
            return
        text = ''.join(self.current['text'])
        # Collapse runs of spaces/tabs; keep newlines (Evernote uses them in paras)
        text = re.sub(r'[ \t]+', ' ', text)
        text = '\n'.join(line.strip() for line in text.split('\n'))
        text = text.strip()
        if text:
            if self.current['type'] == 'h1':
                self.h1_texts.append(text)
            else:
                self.elements.append((self.current['type'], text))
        self.current = None


def extract(html):
    parser = EvernoteExtractor()
    parser.feed(html)
    parser._flush()

    title = parser.h1_texts[0] if parser.h1_texts else ''
    url = ''
    for h in parser.h1_texts:
        m = re.search(r'https?://\S+', h)
        if m:
            url = m.group(0)
            break

    lines = []
    if title:
        lines.append(f'# {title}')
    if url:
        lines.append(url)
    if title or url:
        lines.append('')

    prev_kind = None
    for typ, text in parser.elements:
        if typ in ('h2', 'h3', 'h4'):
            prefix = {'h2': '## ', 'h3': '### ', 'h4': '#### '}[typ]
            if prev_kind:
                lines.append('')
            lines.append(prefix + text)
            prev_kind = 'h'
        elif typ == 'list-item':
            if prev_kind and prev_kind != 'list':
                lines.append('')
            lines.append(f'- {text}')
            prev_kind = 'list'
        elif typ == 'codeblock':
            if prev_kind:
                lines.append('')
            lines.append('```')
            lines.append(text)
            lines.append('```')
            prev_kind = 'code'
        elif typ == 'para':
            if prev_kind:
                lines.append('')
            lines.append(text)
            prev_kind = 'p'

    result = '\n'.join(lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip() + '\n'


def main():
    if len(sys.argv) < 2:
        print("Usage: evernote_to_md.py <input.html> [output.md]", file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        html = f.read()
    md = extract(html)
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"✓ Wrote {sys.argv[2]}")
    else:
        sys.stdout.write(md)


if __name__ == '__main__':
    main()

