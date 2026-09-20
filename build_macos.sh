#!/usr/bin/env bash
# Build binglish for macOS (run on a Mac, not Windows).
set -euo pipefail
cd "$(dirname "$0")"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "ERROR: this script must run on macOS." >&2
  exit 1
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "Creating venv..."
  python3 -m venv .venv
fi

./.venv/bin/pip install -U pip
./.venv/bin/pip install -r requirements.txt pyinstaller pytest
# Tray child process uses AppKit via pystray; keep pyobjc explicit.
./.venv/bin/pip install pyobjc-core pyobjc-framework-Cocoa || true
./.venv/bin/pip install tkmacosx || true

ICON_ARGS=()
if [[ -f assets/binglish.icns ]]; then
  ICON_ARGS=(--icon assets/binglish.icns)
elif [[ -f assets/binglish.ico ]]; then
  ICON_ARGS=(--icon assets/binglish.ico)
fi

echo "Running tests..."
PYTHONPATH="$PWD" ./.venv/bin/python -m pytest -q tests || {
  echo "Tests failed; abort build." >&2
  exit 1
}

# Shared PyInstaller flags:
# - tray runs in a multiprocessing child (binglish.ui.tray_proc) on macOS
# - pystray._darwin + PyObjC must be bundled for that child
# - freeze_support() is already in binglish/app.py __main__
HIDDEN=(
  --hidden-import binglish.ui.tray_proc
  --hidden-import binglish.ui.theme
  --hidden-import binglish.ui.ui_queue
  --hidden-import pystray._darwin
  --hidden-import objc
  --hidden-import Foundation
  --hidden-import AppKit
  --hidden-import PyObjCTools.MachSignals
  --collect-binaries pystray
)

echo "Building onedir app bundle (preferred for release)..."
./.venv/bin/pyinstaller --noconfirm --windowed \
  --name binglish \
  "${ICON_ARGS[@]}" \
  --add-data "assets/binglish.ico:." \
  --paths . \
  "${HIDDEN[@]}" \
  binglish/app.py

APP_PATH="dist/binglish.app"
BIN_PATH="dist/binglish/binglish"
if [[ ! -d "$APP_PATH" && -d "dist/binglish" ]]; then
  # Some PyInstaller versions emit a folder without wrapping .app when
  # --windowed is set; still usable as a directory distribution.
  APP_PATH="dist/binglish"
fi

echo
echo "Output: $APP_PATH"
if [[ -d "$APP_PATH" ]]; then
  # Checksums for GitHub Release notes
  if [[ -f "$APP_PATH/Contents/MacOS/binglish" ]]; then
    shasum -a 256 "$APP_PATH/Contents/MacOS/binglish" | tee dist/checksums-macos.txt
  else
    find dist -type f -name binglish -perm -111 -maxdepth 3 | head -1 | while read -r f; do
      shasum -a 256 "$f" | tee dist/checksums-macos.txt
    done
  fi
fi

echo
echo "Self-test (opens tray if GUI session exists):"
echo "  open \"$APP_PATH\""
echo "  # or: ./dist/binglish.app/Contents/MacOS/binglish"
echo
echo "Zip for GitHub Release:"
echo "  ditto -c -k --sequesterRsrc --keepParent \"$APP_PATH\" dist/binglish-macos.zip"
echo "  shasum -a 256 dist/binglish-macos.zip"
echo
echo "Users without Apple notarization:"
echo "  xattr -dr com.apple.quarantine /Applications/binglish.app"
echo "  # or right-click → Open on first launch"
