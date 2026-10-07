#!/usr/bin/env bash
# Apply source changes only. Does not build, open a device or flash firmware.
set -euo pipefail
PACKAGE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SDK_ROOT=${1:?Usage: install.sh /path/to/muse-gadget-sdk}
BASE=b139b45064b4dcecf7bfe97e75bc7f99c10c28b6
[[ $(git -C "$SDK_ROOT" rev-parse HEAD) == "$BASE" ]] || {
  echo "This package targets SDK commit $BASE. Review/rebase it for other revisions." >&2
  exit 2
}
git -C "$SDK_ROOT" diff --quiet
git -C "$SDK_ROOT" diff --cached --quiet
git -C "$SDK_ROOT" apply --check "$PACKAGE_ROOT/patches/t-display-s3-sdk-support.patch"
git -C "$SDK_ROOT" apply "$PACKAGE_ROOT/patches/t-display-s3-sdk-support.patch"
echo 'T-Display-S3 source support applied. Configure your own SDK token and build with ESP-IDF v6.0.1.'
