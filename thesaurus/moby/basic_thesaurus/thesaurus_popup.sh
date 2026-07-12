#!/bin/bash
# Thesaurus popup script for Karabiner integration
# Run with: bash /path/to/thesaurus_popup.sh
# Or from Karabiner: osascript /path/to/thesaurus_dialog.applescript

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
osascript "$SCRIPT_DIR/thesaurus_dialog.applescript"
