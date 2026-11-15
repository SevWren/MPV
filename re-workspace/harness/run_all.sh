#!/usr/bin/env bash
# One-command full test runner for webm.lua fixes
# Requires: mpv, ffmpeg (from conda-forge or system), LuaJIT
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Locate mpv and ffmpeg
MPV=$(which mpv 2>/dev/null || echo "")
FFMPEG=$(which ffmpeg 2>/dev/null || echo "")
LUAJIT=$(which luajit 2>/dev/null || echo "")

if [ -z "$MPV" ] || [ -z "$FFMPEG" ]; then
  echo "ERROR: mpv and ffmpeg required. Install via: conda install -c conda-forge mpv ffmpeg"
  exit 1
fi

# Create a test video if it doesn't exist
INPUT=/tmp/webm_test_input.mp4
if [ ! -f "$INPUT" ]; then
  ffmpeg -y -f lavfi -i "testsrc=duration=2:size=320x240:rate=30" \
    -f lavfi -i "sine=frequency=440:duration=2" \
    -c:v libx264 -c:a aac -t 2 "$INPUT" 2>/dev/null
fi

echo "=== Static analysis tests (Python) ==="
python3 "$SCRIPT_DIR/tests/test_all_fixes.py"

echo ""
echo "=== Runtime TDD cycle (real mpv + LuaJIT) ==="
python3 "$SCRIPT_DIR/tests/tdd_runtime_full_cycle.py"

echo ""
echo "ALL TEST SUITES PASSED"
