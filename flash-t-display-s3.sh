#!/usr/bin/env bash
# Flash only the audited build using its own generated offsets and full backup.
set -euo pipefail
TASK_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
if [[ $# -lt 2 ]]; then
  echo "Usage: $0 PORT VERIFIED_BOARD_MAC [--dry-run|--backup-only]" >&2
  echo "For the board diagnosed in this project: $0 /dev/cu.usbmodem1101 24:58:7c:d3:96:30" >&2
  exit 2
fi
TASK_PORT=$1; TASK_MAC=$2; shift 2
if ! python3 -c 'import esptool' >/dev/null 2>&1; then
  for d in "${IDF_PATH:-}" "$HOME/esp/esp-idf-v6.0.1" "$HOME/esp/esp-idf"; do
    if [[ -n "$d" && -f "$d/export.sh" ]]; then . "$d/export.sh" >/dev/null; break; fi
  done
fi
python3 "$TASK_ROOT/tools/flash-t-display-s3.py" --port "$TASK_PORT" --expected-mac "$TASK_MAC" "$@"
