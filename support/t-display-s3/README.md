# T-Display-S3 support for the Muse Gadget SDK

Community port, version 0.1.0. Supports the **standard LilyGO T-Display-S3,
1.9-inch 170×320 ST7789V LCD**, in 320×170 landscape orientation.

This is a source contribution for
[facebookincubator/muse-gadget-sdk](https://github.com/facebookincubator/muse-gadget-sdk),
prepared against commit `b139b45064b4dcecf7bfe97e75bc7f99c10c28b6`.
It is not an official upstream release or a universal T-Display driver.

## What is included

- `patches/t-display-s3-sdk-support.patch`: all 24 SDK source/documentation changes.
- `install.sh`: checks the baseline and patch before applying; never builds or flashes.
- `README.md`: setup, hardware mapping, workflow, validation, limits and PR text.
- `LICENSE`, `NOTICE` and `licenses/`: SDK and vendor notices.
- `PACKAGE_MANIFEST.json` and `SHA256SUMS`: provenance and checksums.

No firmware binary, credentials, generated sdkconfig, private flash backup,
personal board identity or chat history is included. Recipients build with
their own SDK token.

## Install

Use a clean checkout at the stated baseline:

```sh
git clone https://github.com/facebookincubator/muse-gadget-sdk.git
cd muse-gadget-sdk
git checkout b139b45064b4dcecf7bfe97e75bc7f99c10c28b6
```

From the extracted package, run:

```sh
shasum -a 256 -c SHA256SUMS
./install.sh /path/to/muse-gadget-sdk
```

Alternatively, from the SDK root, review and apply the combined patch:

```sh
git apply --check /path/to/package/patches/t-display-s3-sdk-support.patch
git apply /path/to/package/patches/t-display-s3-sdk-support.patch
```

For a different SDK revision, rebase/review the patch and repeat validation.
The installer deliberately refuses an unverified baseline.

## Build and configure

Install/activate **ESP-IDF v6.0.1**. From the SDK's `esp32/` directory:

```sh
. /path/to/esp-idf/export.sh
idf.py -B build-muse-lilygo-t-display-s3 -DIDF_TARGET=esp32s3 \
  -DSDKCONFIG=build-muse-lilygo-t-display-s3/sdkconfig \
  '-DSDKCONFIG_DEFAULTS=sdkconfig.defaults;devices/sdkconfig.muse;devices/sdkconfig.muse-lilygo-t-display-s3' build
idf.py -B build-muse-lilygo-t-display-s3 menuconfig
```

Set your own `CONFIG_GADGET_SDK_TOKEN` under the SDK configuration menu.
The generated sdkconfig remains local. Rebuild:

```sh
idf.py -B build-muse-lilygo-t-display-s3 build
python3 -m unittest discover -s tests -p 'test_*.py'
```

`tools/muse/board.sh build t-display-s3` is also available; it clears managed
components after building, so use the direct build above before host tests
that compile the resolved cJSON source.

The profile loads `sdkconfig.defaults`, `devices/sdkconfig.muse`, then
`devices/sdkconfig.muse-lilygo-t-display-s3`. Existing generated sdkconfig
values override changed defaults: use a fresh build directory when changing
the board profile. Do not overwrite `sdkconfig.defaults` with a board overlay.

## Flash and verify

This profile uses the SDK's standard `partitions_muse.csv`, with its table at
`0x10000` and application at `0x20000`. **An already provisioned board may have
a different NVS/OTA layout.** Check the existing table and make a complete
16 MB backup before replacing an existing installation. Do not use this
generic layout as an in-place migration from an unknown layout; see
[storage compatibility](#storage-compatibility).

Identify the standard board and its port, then use the build's generated
flash plan rather than hand-written offsets:

```sh
python tools/muse/ports.py --list
python -m esptool --chip esp32s3 --port PORT read-mac
# Keep any backup private: it can contain Wi-Fi and pairing credentials.
umask 077
python -m esptool --chip esp32s3 --port PORT read-flash 0 0x1000000 /private/path/board-backup.bin
tools/muse/board.sh flash t-display-s3 PORT
python tools/muse/monitor.py PORT 30
```

Expect the PSRAM memory test to pass, `muse_ui: UI up: 320x170`, and
`muse: ready`, without panic or repeated reboot. Visually confirm an avatar
and text. USER/GPIO14 opens and advances the menu; BOOT/GPIO0 selects and
confirms pairing. The standard board has no touch, microphone or speaker.

## Hardware reference

Target: standard LilyGO T-Display-S3, ESP32-S3R8, 16 MB external flash,
8 MB octal PSRAM, 1.9-inch ST7789V LCD. USB-only hardware verification.

| Signal | GPIO / setting |
|---|---|
| LCD bus | 8-bit I80/8080 parallel, 10 MHz |
| CS | 6, active low |
| D/C | 7; command low, data high |
| WR | 8 |
| RD | 9, held HIGH/inactive before writes |
| Reset | 5, active low |
| D0..D7 | 39, 40, 41, 42, 45, 46, 47, 48, in that order |
| Backlight | 38, active high; 5 kHz, 8-bit PWM |
| Power hold/enable | 15 HIGH during operation |
| BOOT/select/confirm | 0, active low |
| USER/menu | 14, active low |
| Native USB | D−19, D+20; VID:PID 303a:1001 |
| Battery ADC | 4; not implemented in this port |
| Touch/audio | None onboard |

The landscape view is 320×170, screen facing you with USB on the left.
ST7789 settings: RGB565, inversion on, axes swapped, mirror(false,true),
gap(0,35). The ST7789V has 240×320 controller RAM; the module's visible
window requires the 35-pixel crop.

The display is **not SPI**, despite sharing a controller family with SPI
modules. Backlight illumination alone does not demonstrate LCD data output.
Do not substitute AMOLED/Pro/Long pins or a generic SPI ST7789 example.

### Sources inspected

- [LilyGO ESP-IDF implementation](https://github.com/Xinyuan-LilyGO/LilyGo-Display-IDF/tree/b1a1cc54994bf1b417e3bb30c437bbe1036bff7f):
  `main/product_pins.h`, `main/display_s3.c`, `sdkconfig.defaults.t-display-s3`.
- [Standard T-Display-S3 repository](https://github.com/Xinyuan-LilyGO/T-Display-S3/tree/ec889e789b3cf093412689a143f7f37b42b56af7):
  `schematic/T_Display_S3.pdf`, `datasheet/ST7789V_SPEC_V1.4.pdf`, TFT_eSPI Setup206.
- ESP-IDF v6.0.1 I80, ST7789 and S3 GDMA sources.
- esp_lvgl_adapter 0.6.4 and LVGL 9.5.0 allocation, flush and callback sources.

Panel gamma/power/porch values follow LilyGO's module-specific sequence.
The port adds the reset-to-SLPOUT wait required by ST7789V reset timing
(specification pp.49–50), and waits 120 ms after SLPOUT before display use.

## Runtime and build integration

1. Kconfig selects `MUSE_BOARD_LILYGO_T_DISPLAY_S3` and board ID
   `lilygo_t_display_s3`. CMake compiles the new board driver and resolves the
   LVGL adapter. The status backend is MUSE, avoiding a competing SPI driver.
2. The bootloader initializes 8 MB octal PSRAM and runs its memory test.
   A missing/misconfigured PSRAM device is not silently ignored.
3. `app_main()` starts Muse glue and Link. The Muse boot task waits for storage
   readiness before loading settings and calling `muse_app_run()`.
4. Board initialization preloads RD HIGH, backlight LOW and GPIO15 HIGH,
   configures the outputs, settles power, and initializes both buttons.
   Held button state is seeded so leaving the ROM loader is not a UI press.
5. The board creates an 8-bit I80 bus and panel IO, resets ST7789V, waits the
   full reset-to-SLPOUT interval, applies base and vendor panel commands,
   and sets inversion/orientation/crop. Initial backlight duty remains zero.
6. The adapter creates two internal 320×32 RGB565 draw buffers (20,480 bytes
   each). The bus allows an equally sized transfer and uses a 32-byte DMA burst.
   S3 GDMA supports 16/32/64-byte bursts; the old SRAM-alignment field cannot
   be copied into IDF 6's burst-size field.
7. The UI builds a compact 320×170 layout with a 113-pixel avatar and a 40 ms
   animation timer. Saved brightness is applied through bounded PWM.
8. LVGL creates partial RGB565 rectangles. The OTHER-interface adapter
   compacts row stride and swaps bytes once. Panel IO does not swap them again.
   The ST7789 driver sends CASET/RASET/RAMWR; I80/GDMA transmits pixel data.
   The completion callback releases the LVGL buffer. Odd-pixel rectangles
   need no RX-alignment padding on this S3 transmit path.
9. USER opens/advances the no-touch menu. BOOT selects or confirms a pending
   pairing. Sleep/deep-sleep handlers are implemented; physical sleep/wake
   validation is still pending.
10. Wi-Fi and BLE are owned by Link. NimBLE host allocations use external
    RAM; the controller starts before larger network allocations fragment
    internal memory. Failed controller/GATT startup no longer proceeds into
    NULL service state or claims successful setup.
11. Link connection states forward through the MUSE backend to the avatar
    and captions. UI startup does not require a completed cloud connection.
    No voice pipeline is started because this board has no audio hardware.

### Regression hardening included

The second patch checks BLE mutex/controller/GATT/name startup failures,
cleans up initialized NimBLE on service failure, preserves retry mutexes,
and reports actual startup success to the app. It checks the UI image mutex,
display lock, frame timer and input queue. The Wi-Fi diagnostic uses a
bounded three-byte country field and handles a failed lookup.

The board harness executes the production driver against independently
specified manufacturer pin expectations and injects every fallible startup
call. A separate compiled BLE harness exercises ten startup failure points.

## Supported scope and known limits

- Standard 1.9-inch T-Display-S3 only. AMOLED/Pro/Long variants are excluded.
- No onboard touch, microphone or speaker. This port provides display,
  buttons, settings, BLE provisioning and the SDK's text/network paths.
- Battery ADC reporting is absent. USB-connected readings are not a valid
  basis for a fabricated battery percentage.
- GPIO15 stays HIGH. Battery shutdown by dropping the power-hold line is
  not implemented from USB-only assumptions.
- Deep-sleep off/wake and panel sleep callbacks exist. A physical sleep/wake
  cycle and battery runtime were not tested.
- Automatic PM is disabled. Production OTA is disabled until the server
  provides a verified board-specific image.
- Hardware Secure Boot, flash encryption and eFuse manufacturer pairing
  are disabled in the development profile. App signing alone does not enable
  hardware Secure Boot.
- Startup and network-session reconnect were observed over short captures.
  Long-duration soak, all remote command workloads and memory exhaustion
  under arbitrary workloads were not tested.
- Upstream acceptance is pending. The package supports a stated SDK commit;
  future SDK/IDF/LVGL versions need renewed validation.

### Storage compatibility

The generic SDK profile uses `partitions_muse.csv`:

| Partition | Offset | Size |
|---|---:|---:|
| Partition table | 0x10000 | table sector |
| nvs | 0x11000 | 0xC000 |
| otadata | 0x1D000 | 0x2000 |
| phy_init | 0x1F000 | 0x1000 |
| ota_0 | 0x20000 | 4 MiB |
| ota_1 | 0x420000 | 4 MiB |
| prod_data | 0x820000 | 0x1000 |
| prod_bak | 0x821000 | 0x1000 |

The hardware verification board retained its previous smaller NVS/OTA
geometry using a project-local compatibility overlay. Those local offsets
are not substituted into the SDK-wide board profile. They are not a general
migration solution for other boards.

Before replacing an existing installation, read and preserve the actual
partition table and a complete flash backup. A changed NVS size/offset or OTA
layout needs an explicit migration/reprovisioning plan. The SDK's generic
flash helper does not automatically migrate private saved state. Use only
the manifest generated by the matching build, including otadata.

## Validation record

Version 0.1.0, validated October 7, 2026 UTC. SDK baseline:
`b139b45064b4dcecf7bfe97e75bc7f99c10c28b6`.

### Clean release-package validation

The package installer applied the combined contribution to a separate clean
checkout of the baseline. The two review patches were also checked sequentially during preparation.
The release now provides a single combined patch. All **24 added/modified SDK files** matched the validated source
byte-for-byte. The installer rejected a modified checkout before writes.

The clean applied checkout passed:

| Check | Result |
|---|---|
| Standard board build | Passed, ESP-IDF v6.0.1 |
| LVGL / adapter | 9.5.0 / 0.6.4 |
| Compiled board selection | Only `board_lilygo_t_display_s3.c` |
| Profile | MUSE backend, 16 MB flash, octal PSRAM with memory test, native USB |
| Security provisioning | Secure Boot, flash encryption and pairing eFuse authentication disabled |
| Generic partition layout | table 0x10000; otadata 0x1D000; app 0x20000 |
| App / slot size | 2,035,712 / 4,194,304 bytes; approximately 51.5% free |
| SDK token in validation build | Empty; recipient must configure their own |
| Host suite | 183 tests run; 182 passed, 1 skipped |

The skipped test requires a host PSA/mbedcrypto library unavailable in the
validation environment. The pairing test using ESP-IDF's real crypto source
ran with `IDF_PATH` configured. The firmware's production crypto compiled.

New behavioral tests compile and exercise the production board driver and BLE
startup against fakes. They check the independently specified vendor wiring,
reset timing, buffer/DMA parameters and every fallible startup call; BLE tests
check ten failure points and mutex reuse during retries.

### Hardware and cross-board observations

The same board driver and shared startup code were tested on one standard
USB-only T-Display-S3. The owner confirmed **avatar/text visible and menu works**.
PSRAM passed its on-device memory test. BLE provisioning, Wi-Fi and both SDK
network sessions reached their operational states. Pairing survived the final
reflash. The final 40-second boot capture contained no panic, assertion,
reboot or display-transfer error. The SDK app reached UI startup at about
1.5 seconds and ready at about 3 seconds; network sessions were up by the
11-second heartbeat.

The hardware board retained its existing project-specific partition layout;
the generic SDK layout was build-verified without being flashed over that
provisioned board. AIPI UI and default ESP32-C5 profiles also built successfully
with the shared code changes. Their hardware was not flashed/tested.

Project-local backup/flash safeguards and avatar-routing checks additionally
passed 14 tests. Those local migration helpers are deliberately excluded from
the native SDK contribution because their storage compatibility is specific
to that installation.

### Practical limits

This is short functional validation on one standard board, not a prolonged
soak or validation of every remote workload. Battery operation/shutdown,
physical sleep/wake and production OTA remain unverified. No claim of upstream
acceptance, variant compatibility or permanent-damage diagnosis is made.

## Suggested upstream PR description

Title: Add standard LilyGO T-Display-S3 Muse UI support

The standard 1.9-inch T-Display-S3 uses an 8-bit I80 ST7789V display and octal
PSRAM. SPI pin maps from other ST7789 boards illuminate its backlight without
driving the panel correctly. This contribution adds a manufacturer-referenced
I80 board driver, a canonical S3R8/16 MB profile, two-button navigation,
native USB tooling and board-selection integration.

The port configures inactive RD and power hold before transfers, applies the
module's panel commands and 320×170 landscape crop, uses the IDF 6 supported
DMA burst, and traces the LVGL adapter's single RGB565 byte swap. Startup
failures release partial panel resources. The accompanying hardening patch
prevents a failed NimBLE initialization from reaching NULL GAP/GATT state,
checks UI allocations, and bounds the Wi-Fi country diagnostic.

Validation: ESP-IDF v6.0.1; LVGL 9.5.0; esp_lvgl_adapter 0.6.4. A standard USB-only
board showed avatar/text and a working USER menu; octal PSRAM passed its test,
and provisioning/Wi-Fi/network sessions reached their operational states
without panic in the captures. T-Display-S3, AIPI and default C5 builds and the
183-test host suite passed, with one optional host-crypto test skipped.
Clean-baseline validation is recorded above.

Scope: standard LCD model only, no touch/audio or battery measurement. Physical
sleep/wake, battery shutdown, prolonged soak and production OTA are unverified.
The generic SDK partition layout is for a matching fresh installation; existing
layouts require compatibility checks and backup. No credentials or firmware
binary are part of this contribution.
