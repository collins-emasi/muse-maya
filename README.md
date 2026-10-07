# Standard T-Display-S3 SDK support

Muse Gadget SDK port for the **standard LilyGO T-Display-S3, 1.9-inch ST7789V
LCD**: 320×170 landscape, 8-bit I80, ESP32-S3R8, 16 MB flash and 8 MB octal
PSRAM. The avatar/text and USER menu were physically confirmed working.

## Build and flash this project

Requires ESP-IDF **v6.0.1**. From this directory:

```sh
git submodule update --init --recursive
./build-t-display-s3.sh
./flash-t-display-s3.sh /dev/cu.usbmodem1101 24:58:7c:d3:96:30 --dry-run
./flash-t-display-s3.sh /dev/cu.usbmodem1101 24:58:7c:d3:96:30
```

The port can change after reconnecting. The second argument is this identified
board's MAC; verify another board's identity before using it. The flash helper
checks hardware, preserves the existing partition layout, makes a full private
backup and verifies the written files. Pairing/NVS are preserved.

The current build is `muse-gadget-sdk/esp32/build-t-display-s3-audited/`.
Credentials remain in ignored `build-config/t-display-s3/sdkconfig.private`.
Recovery backups and raw verification logs remain in ignored, local-only
`audit-evidence/`; they are excluded from Git because captures and generated
configs can contain provisioning data. Shared results are in the audit below.

BOOT/GPIO0 selects and confirms pairing; USER/GPIO14 opens/advances the menu.
This standard board has no audio or touch. Battery operation, physical
sleep/wake and production OTA remain unverified.

## Share the SDK port

[Download the support ZIP](dist/t-display-s3-sdk-support-v0.1.0.zip).
It contains one complete SDK patch, an installer, one consolidated
[README](dist/t-display-s3-sdk-support-v0.1.0/README.md), license notices and
checksums. It excludes credentials, firmware binaries and private backups.

Release templates live in `support/t-display-s3/`; the packaging helper is
`tools/package-t-display-s3.py`. The release uses the SDK's generic fresh-board
layout. This already provisioned project's compatibility layout remains local.

## Verification and reference

```sh
python3 tools/test-verify-t-display-s3.py
python3 tools/test-sdk-t-display-s3.py
```

The detailed hardware comparison, call trace, findings and measured results
are in [T_DISPLAY_S3_AUDIT.md](T_DISPLAY_S3_AUDIT.md).
Upstream SDK instructions remain in [its ESP32 README](muse-gadget-sdk/esp32/README.md).
The SDK's Apache-2.0 license and LilyGO's MIT notice are preserved.
