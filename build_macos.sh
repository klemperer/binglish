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
./.venv/bin/pip install -r requirements.txt pyinstaller
# GUI helpers used by some dialogs on mac
./.venv/bin/pip install tkmacosx || true

# Prefer .icns if present; otherwise fall back to bundled ico (may look poor)
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

echo "Building onefile windowed binary..."
./.venv/bin/pyinstaller --noconfirm --onefile --windowed \
  --name binglish \
  "${ICON_ARGS[@]}" \
  --add-data "assets/binglish.ico:." \
  --paths . \
  binglish/app.py

echo
echo "Output: $PWD/dist/binglish"
shasum -a 256 dist/binglish | tee dist/checksums-macos.txt
echo
echo "Self-test (will open tray if GUI session exists):"
echo "  ./dist/binglish"
echo
echo "Optional .app-style distribution:"
echo "  pyinstaller --noconfirm --windowed --name binglish \\"
echo "    ${ICON_ARGS[*]} --add-data 'assets/binglish.ico:.' --paths . binglish/app.py"
echo "  # then zip dist/binglish.app and notarize if you have Apple Developer ID"
