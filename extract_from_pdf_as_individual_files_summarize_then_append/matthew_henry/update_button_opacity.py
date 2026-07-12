#!/usr/bin/env python3
"""Update dark mode button to be more transparent."""

import os
import glob

OLD_BUTTON_STYLE = '''  /* Toggle button */
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
  }'''

NEW_BUTTON_STYLE = '''  /* Toggle button */
  .dark-mode-toggle {
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 9999;
    padding: 8px 16px;
    border: 1px solid rgba(0,0,0,0.2);
    border-radius: 20px;
    cursor: pointer;
    font-size: 14px;
    background: rgba(50,50,50,0.15);
    color: #333;
    box-shadow: none;
    backdrop-filter: blur(2px);
  }
  .dark-mode-toggle:hover {
    background: rgba(50,50,50,0.3);
  }
  body.dark-mode .dark-mode-toggle {
    background: rgba(255,255,255,0.15);
    color: #e0e0e0;
    border-color: rgba(255,255,255,0.2);
  }
  body.dark-mode .dark-mode-toggle:hover {
    background: rgba(255,255,255,0.3);
  }'''

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    if OLD_BUTTON_STYLE in content:
        content = content.replace(OLD_BUTTON_STYLE, NEW_BUTTON_STYLE)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    htm_files = glob.glob(os.path.join(script_dir, 'MHC*.HTM'))

    updated = 0
    for filepath in sorted(htm_files):
        if update_file(filepath):
            updated += 1

    print(f"Updated {updated} files with transparent button.")

if __name__ == '__main__':
    main()
