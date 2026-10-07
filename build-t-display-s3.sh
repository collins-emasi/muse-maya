#!/usr/bin/env bash
# Reproducible build for the standard 1.9-inch LCD board in this project.
set -euo pipefail
TASK_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TASK_SDK="$TASK_ROOT/muse-gadget-sdk/esp32"
TASK_BUILD="$TASK_SDK/build-t-display-s3-audited"
if ! command -v idf.py >/dev/null 2>&1; then
  for d in "${IDF_PATH:-}" "$HOME/esp/esp-idf-v6.0.1" "$HOME/esp/esp-idf"; do
    if [[ -n "$d" && -f "$d/export.sh" ]]; then
      . "$d/export.sh" >/dev/null
      break
    fi
  done
fi
command -v idf.py >/dev/null || { echo 'Activate ESP-IDF v6.0.1 first.' >&2; exit 1; }
[[ $(idf.py --version) == *'v6.0.1'* ]] || { echo 'This project requires ESP-IDF v6.0.1.' >&2; exit 1; }
TASK_DEFAULTS="sdkconfig.defaults;devices/sdkconfig.muse;devices/sdkconfig.muse-lilygo-t-display-s3;$TASK_ROOT/build-config/t-display-s3/sdkconfig.lilygo-t-display-s3"
if [[ -f "$TASK_ROOT/build-config/t-display-s3/sdkconfig.private" ]]; then
  TASK_DEFAULTS="$TASK_DEFAULTS;$TASK_ROOT/build-config/t-display-s3/sdkconfig.private"
fi
cd "$TASK_SDK"
idf.py -B "$TASK_BUILD" -DIDF_TARGET=esp32s3 -DSDKCONFIG="$TASK_BUILD/sdkconfig" \
  -DSDKCONFIG_DEFAULTS="$TASK_DEFAULTS" "$@" build
python3 "$TASK_ROOT/tools/verify-t-display-s3.py" "$TASK_BUILD" --record
