#!/usr/bin/env bash
# Bridge SDK/avatar calls to this project's existing storage-compatible build.
set -euo pipefail
TASK_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TASK_CMD=${1:?build or flash}; TASK_SELECTOR=${2:-}
if [[ -n "${MUSE_BENCH:-}" ]]; then
  echo 'This provisioned board uses the audited compatibility build; a separate bench profile is not configured.' >&2
  exit 2
fi
case "$TASK_CMD" in
  build)
    "$TASK_ROOT/build-t-display-s3.sh" 2>&1 | tee /tmp/muse_build_t-display-s3.log
    exit 0 ;;
  flash) ;;
  *) echo 'Expected build or flash.' >&2; exit 2 ;;
esac
if ! python3 -c 'import serial' >/dev/null 2>&1; then
  for d in "${IDF_PATH:-}" "$HOME/esp/esp-idf-v6.0.1" "$HOME/esp/esp-idf"; do
    if [[ -n "$d" && -f "$d/export.sh" ]]; then . "$d/export.sh" >/dev/null; break; fi
  done
fi
TASK_PORT=$(python3 "$TASK_ROOT/muse-gadget-sdk/esp32/tools/muse/ports.py" t-display-s3 "$TASK_SELECTOR")
TASK_MAC=$(python3 - "$TASK_PORT" <<'PY'
import sys
from serial.tools import list_ports
p=[p for p in list_ports.comports() if p.device==sys.argv[1] and (p.vid,p.pid)==(0x303a,0x1001)]
if len(p)!=1 or not p[0].serial_number:sys.exit('Cannot identify a unique native-USB board serial.')
print(p[0].serial_number)
PY
)
exec "$TASK_ROOT/flash-t-display-s3.sh" "$TASK_PORT" "$TASK_MAC"
