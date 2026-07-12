#!/usr/bin/env python3
"""Add dark mode toggle to all Matthew Henry Commentary HTML files."""

import os
import glob
import re

# CSS and JS to inject
DARK_MODE_STYLE = '''
<style>
  /* Dark mode styles */
  body.dark-mode {
    background: #1a1a1a !important;
    background-image: none !important;
    color: #e0e0e0 !important;
  }
  body.dark-mode h1, body.dark-mode h2, body.dark-mode h3,
  body.dark-mode b, body.dark-mode i, body.dark-mode font {
    color: #e0e0e0 !important;
  }
  body.dark-mode a {
    color: #6db3f2 !important;
  }
  body.dark-mode a:visited {
    color: #b39ddb !important;
  }
  body.dark-mode hr {
    border-color: #444 !important;
  }
  body.dark-mode table {
    background: transparent !important;
  }
  /* Toggle button */
  .dark-mode-toggle {
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 9999;
    padding: 8px 16px;
    border: none;
    border-radius: 20px;
    cursor: pointer;
    font-size: 14px;
    background: #333;
    color: #fff;
    box-shadow: 0 2px 5px rgba(0,0,0,0.3);
  }
  body.dark-mode .dark-mode-toggle {
    background: #f0f0f0;
    color: #333;
  }
</style>
'''

DARK_MODE_BUTTON = '''
<button class="dark-mode-toggle" onclick="toggleDarkMode()">Dark Mode</button>
'''

DARK_MODE_SCRIPT = '''
<script>
function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');
  var btn = document.querySelector('.dark-mode-toggle');
  if (document.body.classList.contains('dark-mode')) {
    btn.textContent = 'Light Mode';
    localStorage.setItem('mhc-dark-mode', 'true');
  } else {
    btn.textContent = 'Dark Mode';
    localStorage.setItem('mhc-dark-mode', 'false');
  }
}
// Check saved preference on load
if (localStorage.getItem('mhc-dark-mode') === 'true') {
  document.body.classList.add('dark-mode');
  document.querySelector('.dark-mode-toggle').textContent = 'Light Mode';
}
</script>
'''

def add_darkmode_to_file(filepath):
    """Add dark mode to a single HTML file."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Skip if already has dark mode
    if 'dark-mode-toggle' in content:
        print(f"Skipping (already has dark mode): {os.path.basename(filepath)}")
        return False

    # Add style before </HEAD>
    if '</HEAD>' in content:
        content = content.replace('</HEAD>', DARK_MODE_STYLE + '</HEAD>')
    elif '</head>' in content:
        content = content.replace('</head>', DARK_MODE_STYLE + '</head>')

    # Add button after <body...>
    body_match = re.search(r'<body[^>]*>', content, re.IGNORECASE)
    if body_match:
        body_tag = body_match.group()
        content = content.replace(body_tag, body_tag + '\n' + DARK_MODE_BUTTON, 1)

    # Add script before </BODY>
    if '</BODY>' in content:
        content = content.replace('</BODY>', DARK_MODE_SCRIPT + '</BODY>')
    elif '</body>' in content:
        content = content.replace('</body>', DARK_MODE_SCRIPT + '</body>')

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    htm_files = glob.glob(os.path.join(script_dir, 'MHC*.HTM'))

    print(f"Found {len(htm_files)} HTM files")

    updated = 0
    for filepath in sorted(htm_files):
        if add_darkmode_to_file(filepath):
            updated += 1

    print(f"\nDone! Updated {updated} files.")

if __name__ == '__main__':
    main()
