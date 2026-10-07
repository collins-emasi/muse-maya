# Standard T-Display-S3 audit and repair

Audit started October 6, 2026, America/Los_Angeles. Target confirmed by the owner: **standard 1.9-inch T-Display-S3, USB only, no external wiring**. This report distinguishes observations from code deductions and untested hardware functions. It supersedes the previous repair summaries.

## What was actually happening

The screen was illuminated, but the running firmware did **not** complete startup. A passive serial capture, without requesting a reset, recorded repeated boots and the same failure sequence:

1. ESP-IDF v6.0.1 loaded the app at `0x20000`.
2. No PSRAM was initialized (`psram=0K`).
3. The selected Muse board initialized an SPI display on the wrong pins.
4. `app_run()` also tried to initialize the ideaspark SPI display backend. It logged `SPI bus already initialized` and `ideaspark ST7789 init failed: ESP_ERR_INVALID_STATE`.
5. The wrong driver enabled the correctly mapped backlight, GPIO38. Its “panel initialized” message meant that software submitted transactions; it did not verify that the physical LCD received them.
6. Internal heap after Wi-Fi was about 50 KiB; the largest block was about 31 KiB. BLE logged `hci inits failed` and `nimble host init failed`.
7. `ble_server_start()` ignored the failed return from `nimble_port_init()` and called `ble_svc_gap_init()` anyway. The firmware panicked with `LoadProhibited`, address `0x00000004`, and rebooted.

The ELF hash in the log matched the old build's ELF. `addr2line` resolved the failing stack to:

```text
ble_gatts_count_cfg -> ble_svc_gap_init -> ble_server_start
-> start_ble_setup_server_if_needed -> open_setup_window
-> app_run -> app_main -> main_task
```

The full redacted capture is in `audit-evidence/pre-fix/serial-boot.txt`. Redacted pre-edit copies of the driver, generated config, defaults and flash manifest are beside it. These observations establish multiple firmware faults. They do not establish that any previously lost board suffered permanent electrical damage.

## Hardware sources and exact applicability

The manufacturer has already implemented this display in ESP-IDF. Native upstream Muse support was absent; the board is not an undocumented new electrical interface. The task is to integrate the known hardware path into Muse's board abstraction.

Sources inspected locally, including the schematic's visual connections:

- [LilyGO ESP-IDF reference](https://github.com/Xinyuan-LilyGO/LilyGo-Display-IDF), commit `b1a1cc54994bf1b417e3bb30c437bbe1036bff7f`: `main/product_pins.h`, `main/display_s3.c`, `sdkconfig.defaults.t-display-s3`.
- [LilyGO standard board repository](https://github.com/Xinyuan-LilyGO/T-Display-S3), commit `ec889e789b3cf093412689a143f7f37b42b56af7`: `schematic/T_Display_S3.pdf`, `datasheet/ST7789V_SPEC_V1.4.pdf`, `lib/TFT_eSPI/User_Setups/Setup206_LilyGo_T_Display_S3.h` and `TFT_Drivers/ST7789_Init.h`.
- Local **ESP-IDF v6.0.1**: `esp_lcd_io_i80.h`, `esp_lcd_panel_st7789.c`, NimBLE initialization and service registration sources.
- Actual resolved **esp_lvgl_adapter 0.6.4**, **LVGL 9.5.0**: display allocation, registration, color conversion, DMA completion and flush implementations.

The physical chip's ROM/eFuse reads reported ESP32-S3 revision v0.2, `Embedded PSRAM 8MB (AP_3v3)`, Wi-Fi, BLE, dual cores and 240 MHz support. Flash identification reported 16 MB. The native USB descriptor was `303a:1001`, MAC/USB serial `24:58:7c:d3:96:30`. Secure Boot and flash encryption were disabled. These reads do not burn eFuses.

### Baseline versus this board

| Property | SDK default C5 board | ideaspark status-display profile | Actual standard T-Display-S3 |
|---|---|---|---|
| Processor | ESP32-C5, RISC-V | Classic ESP32, Xtensa | ESP32-S3R8, dual-core Xtensa LX7 |
| Flash | Default 8 MB | Board-specific | 16 MB W25Q128-class external flash |
| PSRAM | Quad mode in shared defaults | No PSRAM profile | 8 MB **octal** embedded PSRAM |
| Screen transport | Status LED | **SPI** ST7789 | **8-bit I80/8080 parallel** ST7789V |
| Screen window | None | 170 x 320 portrait | 170 x 320 physical; 320 x 170 landscape |
| Status hardware | GPIO27 RGB LED | Its own panel driver | Muse LVGL panel; no independent LED driver |
| Buttons | GPIO28 | Board-specific | BOOT GPIO0, USER GPIO14 |
| USB console | Native Serial/JTAG | UART through a bridge | Native USB on GPIO19/20 |
| Touch/audio | None | None | None on the owner's standard board |

The ST7789 family supports several interface modes, but the board's wiring determines the usable mode. A compatible controller name alone does not justify copying another board's SPI bus. AMOLED/Pro/Long boards have different panel hardware and are outside this port.

### Pin-by-pin reconciliation

| Signal | Manufacturer / repaired mapping | Previous implementation | Consequence |
|---|---|---|---|
| LCD chip select | GPIO6, active low | GPIO10 | Never properly selected the LCD; GPIO6 was driven as a clock |
| LCD data/command | GPIO7 | GPIO8 | Toggled the **write strobe**, not D/C |
| LCD write strobe | GPIO8 | Missing | No defined parallel write transfers |
| LCD read strobe | GPIO9, held **HIGH** | Used as reset | Pulsed RD instead of resetting; did not enforce inactive read state |
| LCD reset | GPIO5, active low | GPIO9 | Actual LCD reset was never driven |
| LCD D0 | GPIO39 | Missing | No data bus |
| LCD D1 | GPIO40 | Missing | No data bus |
| LCD D2 | GPIO41 | Missing | No data bus |
| LCD D3 | GPIO42 | Missing | No data bus |
| LCD D4 | GPIO45 | Missing | No data bus |
| LCD D5 | GPIO46 | Missing | No data bus |
| LCD D6 | GPIO47 | Missing | No data bus |
| LCD D7 | GPIO48 | Missing | No data bus |
| Backlight enable/PWM | GPIO38, active high | GPIO38 | This was correct; illumination did not demonstrate working LCD data |
| Power hold/enable | GPIO15 HIGH during operation | Missing | Breaks battery-powered operation; explicitly initialized now |
| BOOT | GPIO0, active low | GPIO0 | Correct pin, but button state/meaning needed completion |
| USER | GPIO14, active low | Missing | Could not reach the two-button settings menu |
| Battery ADC | GPIO4, divider | Missing | Intentionally left unsupported; USB prevents valid battery measurement |
| Native USB | GPIO19/20 | Not repurposed | Retained for USB logs, serial commands and programming |
| SPI MOSI | **No such LCD signal** | GPIO3 | Unrelated header/strap pin was driven unnecessarily |

RD stays high before the I80 peripheral begins writing. That prevents the panel from driving its data outputs during ESP writes. Pin values come from the vendor reference and schematic; no speculative pin changes or voltage adjustments were used.

## Startup, drawing, input and connection trace

### Build selection

1. `build-t-display-s3.sh` activates ESP-IDF v6.0.1 and builds into the separate `build-t-display-s3-audited/` directory.
2. Defaults load in this order: shared SDK defaults; `devices/sdkconfig.muse`; `devices/sdkconfig.muse-lilygo-t-display-s3`; this project's compatibility partition overlay; local ignored credential defaults.
3. Kconfig selects `MUSE_BOARD_LILYGO_T_DISPLAY_S3`, makes `MUSE_ENABLED=y`, and derives `MUSE_BOARD_ID="lilygo_t_display_s3"`.
4. `components/muse/CMakeLists.txt` compiles precisely `boards/board_lilygo_t_display_s3.c` for the board. The dependency rule includes the LVGL adapter for that board ID. The resolved adapter is 0.6.4, compatible with the resolved LVGL 9.5.0.
5. The Muse status backend forwards connection state to the UI. No ideaspark, C5 LED or other display driver initializes hardware in this profile.
6. CMake refuses an incompatible LilyGO configuration: wrong status backend, absent/quad/ignored PSRAM, wrong flash capacity/USB console, or security eFuse provisioning.
7. `tools/verify-t-display-s3.py` compares the generated config to the requested board/UI overlay, compares it to generated JSON, parses the actual partition binary, checks app headroom and erase-sector overlap, checks which board source was compiled, and records source/config/binary hashes. Flashing refuses stale results.
8. SDK `tools/muse/board.sh` and the avatar tool recognize this board. Within this enclosing project, the SDK helper delegates to `tools/sdk-t-display-s3.sh`, which routes builds/flashes through the compatibility wrappers. It retains the expected avatar-error log and propagates build failures. It cannot silently switch this provisioned board to the generic fresh-board layout. A separate bench/screenshot profile is explicitly rejected here until its compatibility workflow is configured.

A generated `sdkconfig` takes precedence over later edits to default files. The original build was retained for evidence; the repair started in a fresh directory. Future overlay changes must be propagated to the generated config or a fresh build directory, and the verifier will reject unapplied board settings.

### Reset through board initialization

1. The ROM loads the second-stage bootloader.
2. The bootloader reads the partition table and selected OTA application. Early application startup initializes the specified **octal PSRAM**, runs its memory test, and adds it to the allocator.
3. `main/main.c:app_main()` starts diagnostic logging, calls `muse_glue_start()`, then calls `app_run()`.
4. `muse_glue_start()` creates the readiness event group, registers the Link adapters and companion BLE service, and starts `muse_boot` on core 1 and `muse_keep` on an internal stack.
5. `muse_boot` waits for `BIT_STORAGE`; it does not race NVS initialization.
6. `app_run()` creates its gates, initializes config/NVS and known Wi-Fi storage, sets the device identity, then calls `muse_glue_storage_ready()`.
7. The boot task can now call `muse_app_run(muse_board_get())`. The chosen board is logged by name.
8. `board->init()` preloads RD=HIGH, backlight=LOW, GPIO15=HIGH and configures those outputs, waits for power settling, initializes GPIO0 and GPIO14 inputs, and samples their initial held state. It configures GPIO38 LEDC PWM with zero initial duty.
9. `muse_app_run()` loads stored settings, initializes state/battery handling, sets the startup caption and calls `muse_ui_start()`.

### Panel and LVGL handoff

1. `display_start()` clears the optional touch result; this standard board has no touch input.
2. It creates the I80 bus using ordered D0..D7, D/C=7, WR=8, an 8-bit width, and 10 MHz timing used by the LilyGO ESP-IDF reference.
3. It creates active-low CS=6 panel IO with 8-bit commands/parameters and D/C low for commands, high for data. `swap_color_bytes=false` is deliberate.
4. It creates the ST7789 driver with RST=5, RGB order and 16-bit pixels. Hardware reset and the IDF base initialization precede panel-specific commands. IDF's hardware-reset release wait is 10 ms; the port adds 110 ms before SLPOUT. The controller's reset-timing restriction requires 120 ms before SLPOUT, including resets of an already awake panel (ST7789V specification, pp. 49–50). IDF then waits 100 ms after SLPOUT; the port conservatively adds 20 ms before vendor commands and display use.
5. The vendor panel commands configure COLMOD, porch, gate control, VCOM, power parameters, frame rate and positive/negative gamma. They are taken from LilyGO's actual 1.9-inch display, rather than invented from another panel.
6. Inversion is enabled. `swap_xy=true`, `mirror(false,true)` and gap `(0,35)` establish a landscape 320 x 170 window, screen facing the user and USB on the left. The underlying controller RAM is 240 x 320; the physical 170-column window needs the 35-pixel margin. A `(0,35)` gap without swapping axes was insufficient.
7. DISPON is sent. The backlight remains off while UI creation completes.
8. The LVGL adapter initializes on core 1, priority 5. Interface `OTHER` is its correct category for SPI/QSPI/**I80**. Adapter rotation stays zero because the panel's orientation has already been configured.
9. The adapter allocates two internal 320 x 32 x 2 draw buffers, 20,480 bytes each. The I80 maximum transfer has the same size. IDF 6 GDMA uses a 32-byte burst; the S3 supports 16/32/64-byte burst values. Burst size is distinct from buffer alignment. The S3 AHB GDMA v1 transmit path does not impose the RX path's 4-byte payload-length rule, so odd-pixel RGB565 rectangles can be transmitted without padding. The adapter registers a color-transfer completion callback on the panel IO and starts the LVGL task.
10. `muse_ui_start()` checks its image mutex and display lock, builds the compact screen, menu and overlays, checks the frame timer, marks the UI ready and unlocks it. At 320 x 170 the avatar canvas is 113 x 113, leaving room for the header and captions.
11. Each 40 ms `frame_tick` updates the animation, state, captions and brightness. Avatar dirty-cell comparisons restrict drawing to changed areas. LVGL's partial refresh builds RGB565 strips.
12. The adapter compacts row stride, **swaps native RGB565 bytes once** for interface OTHER, and calls `esp_lcd_panel_draw_bitmap()` with exclusive rectangle end coordinates.
13. The ST7789 driver adds the display gap, sends CASET/RASET and RAMWR. I80/GDMA writes the big-endian bytes on the parallel bus. The IO completion callback tells LVGL when the buffer can be reused. Enabling another byte swap in I80 would corrupt colors.

IDF transmit success is not a read-back of panel identity or displayed pixels. RD is intentionally inactive; visual observation remains a separate acceptance condition.

### Settings, buttons and sleep

- The input task polls at 10 ms and debounces three samples. GPIO0 produces talk/select edges. GPIO14 edges are shifted into the AUX bits, which open and step through the no-touch menu. While a pairing confirmation is pending, BOOT confirms it; while the menu is open, BOOT selects.
- A BOOT button held during programming is seeded as already pressed, so initialization does not fabricate a new confirmation edge.
- Both buttons are included in the blocking button-wait implementation. Current firmware does not enable unvalidated automatic light sleep or display pausing; normal input polling remains active.
- Brightness is clamped to 0..100 before conversion to 0..255 PWM duty. The saved value is applied by the UI rather than forcing full brightness before the screen exists.
- Screen sleep sets PWM off and sends SLPIN. Waking sends SLPOUT and waits the same full 120 ms before drawing. The panel retains its GRAM.
- Selecting power off now has a real handler. It waits for released buttons, configures GPIO0/14 deep-sleep wake, blanks/sleeps the panel, and enters deep sleep. On USB this is a sleep state, not a physical USB power cut. GPIO15 is not driven low based on an untested battery shutdown assumption.
- No `read_power` implementation is installed: valid battery/USB discrimination cannot be inferred from this board's USB-invalid ADC reading. The UI must not show invented battery measurements.
- There is no onboard microphone or speaker. `muse_app_run()` explicitly skips voice startup. The shared text client and captions can operate after provisioning; this port does not create audio hardware by changing GPIOs.

### BLE, Wi-Fi and remote state

1. `app_run()` initializes Wi-Fi and the Noise control client. Large JSON/TLS/UI allocations can use PSRAM; Wi-Fi hot paths are moved out of scarce IRAM by the Muse overlay. NimBLE host allocations use external RAM, leaving internal space for controller and DMA needs.
2. An unpaired board opens setup and starts the BLE server. A configured board keeps companion advertising off unless requested.
3. BLE startup checks RX/TX mutex allocation and `nimble_port_init()` before touching any service tables. It stops and deinitializes on service registration/name failures; it sets `s_started` only after successful service setup and host launch.
4. `start_ble_setup_server_if_needed()` derives its success flag from the BLE server's actual state. A failed start no longer marks the app as initialized or proceeds to report advertising.
5. Pairing requires an authenticated handshake and the physical confirmation policy. The board's BOOT edge reaches `muse_link_talk_press()` and `app_confirm_pairing_press()`; credentials are saved by Link.
6. `muse_keep` waits for both `BIT_LINK` and `BIT_MUSE`. It applies settings, reloads credentials after provisioning, joins known networks and manages reconnect backoff. UI startup therefore does not depend on Wi-Fi association or cloud availability.
7. Noise control/tunnel state changes go through `led_status`'s **MUSE** forwarding backend into `muse_glue_led_state()` and `muse_link_set_state()`. The avatar and connection indicators receive the same state as the network stack.
8. OTA is disabled for this custom board until a board-specific server image is verified. The application remains development-signed without enabling hardware Secure Boot. No eFuse-burning procedure is part of this repair.

## Findings and disposition

| # | Irregularity / mistake | Evidence and repair |
|---|---|---|
| 1 | SPI used for a parallel-wired LCD | Replaced with IDF I80 bus and correct D0..D7 wiring |
| 2 | Wrong CS/DC/reset pins; WR missing | Reconciled every control signal against manufacturer source and schematic |
| 3 | RD used as reset and not held inactive | GPIO9 now preloaded/configured HIGH before transfers |
| 4 | GPIO3 unnecessarily driven | LCD code no longer claims a MOSI signal or that pin |
| 5 | Missing power hold/enable | GPIO15 initialized HIGH; battery shutdown remains explicitly untested |
| 6 | Competing ideaspark display backend | Generated config corrected to MUSE only; CMake/verifier reject conflict |
| 7 | Quad PSRAM in early defaults; later PSRAM disabled to avoid boot trouble | Octal PSRAM enabled, missing-memory fallback disabled, memory test enabled |
| 8 | Wrong baseline/global defaults overwritten with a partial board config | Restored upstream shared defaults; isolated board/UI/compatibility overlays |
| 9 | Invented/nonexistent Kconfig options gave false confidence | Removed LCD GPIO/SPI host/UART enable/Gadget storage pseudo-options; verify actual applied config |
| 10 | Inadequate internal memory budget | Correct PSRAM, Muse allocator/RTOS/Wi-Fi settings, external NimBLE allocations and smaller 32-line draw buffers |
| 11 | Ignored failed BLE initialization caused confirmed reboot loop | Added error handling before GAP/GATT; decoded and tested the exact failing path |
| 12 | Unchecked/leaked TX mutex on retries | Check allocation and reuse existing mutex |
| 13 | GATT registration/name errors merely logged | Abort startup and clean up initialized NimBLE instead of advertising an incomplete server |
| 14 | App marked BLE started even after failure | App reflects actual BLE server success and reports failure |
| 15 | Landscape dimensions with no axis swap/mirror | Correct panel orientation and crop; RGB instead of BGR |
| 16 | Missing panel-specific tuning | Apply vendor's porch/gate/power/frame-rate/gamma settings |
| 17 | Color byte-order ambiguity | Traced actual adapter; one software swap, no duplicate hardware swap |
| 18 | Backlight forced to maximum before UI registration | Zero initial duty, saved UI brightness, bounded PWM input |
| 19 | Unchecked image mutex/display lock/frame timer/input queue | Added specific allocation/lock checks so errors cannot silently become null-pointer use |
| 20 | Missing second-button/menu path | GPIO14 initialized, polled, included in wake/wait and board hints |
| 21 | Missing required power-off callback | Implemented deep-sleep off/wake; menu no longer calls NULL |
| 22 | Missing panel sleep/wake settling | Added SLPIN/SLPOUT handler with 120 ms wake settling |
| 23 | Failure paths leaked partially created display resources | Delete panel, IO and bus on failed startup; behavioral test injects each failure |
| 24 | Existing generated config hid subsequent edits | Fresh build directory plus complete overlay/generated-value checks |
| 25 | Flash scripts wrote app at `0x10000`, inconsistent with actual `0x20000` slot | Use generated `flasher_args.json`, include otadata and validate compiled table |
| 26 | Flash scripts omitted otadata, selected stale/first ports, and used unsupported monitoring commands | Replaced root/legacy wrappers with a validated backup/flash path and real serial capture |
| 27 | Shell success checked after `echo`, losing esptool failure status | Scripts now use `set -euo pipefail` and Python error propagation |
| 28 | UART logging while tools used native USB | USB Serial/JTAG is now primary console, matching hardware connector and Muse commands |
| 29 | SDK board/USB/avatar helpers did not know the custom board | Added `t-display-s3` alias, USB mapping, command discovery and avatar board mapping |
| 30 | Old SPI example and “fixed successfully” documents encouraged incorrect reuse | Removed executable wrong-pin example; marked historical guides as superseded and made current workflow prominent |
| 31 | SDK token copied into tracked configuration templates and an old guide | Removed from shared/board defaults and the guide; carried the existing token into ignored, permission-restricted local defaults |
| 32 | Removed `MBEDTLS_HKDF_C` option still requested by Muse overlay under IDF 6 | Removed obsolete setting; ESP-IDF 6 uses PSA Crypto. Applied-settings verifier caught it |
| 33 | Unvalidated automatic PM settings and generic OTA default | Disabled automatic PM and OTA for this port; USB/deep-sleep functions are separately checked |
| 34 | Partition changes proposed without preserving current NVS/OTA geometry | Kept this board's entire existing geometry and checked it against a full on-device backup before writes |
| 35 | IDF 6 DMA burst incorrectly treated as old SRAM alignment | First repair hardware boot caught the assertion; use IDF 6 I80 default 32-byte burst, with S3-supported 16/32/64 checked in the harness |
| 36 | Generic IDF reset wait is insufficient before SLPOUT on a warm panel reset | Add 110 ms after IDF's 10 ms reset-release wait; harness rejects initialization before 120 ms |
| 37 | Boot logged “BLE advertising” unconditionally after setup-start failure | Success-path log now says advertising was requested; actual radio state is reported by BLE/heartbeat events |
| 38 | Wi-Fi country log read past the fixed three-byte `wifi_country_t.cc` field; lookup error was ignored | Hardware capture exposed stray bytes; use `%.3s`, initialized storage and checked lookup status |
| 39 | Generic SDK/avatar helper would rebuild/flash with different partition geometry | Enclosing-project routing now uses compatibility wrappers; separate tests check delegation, port/identity selection, error logs/status, and reject an unconfigured bench path |

## Build and flash validation

The app is signed with the SDK development key, with **hardware Secure Boot, flash encryption and eFuse manufacturer pairing disabled**. All code and flash actions use the existing 3.3 V board design. No external wiring, voltage modifications, `erase-flash`, force-flash or eFuse writes were used.

This project's compatibility layout, verified from the running board and actual compiled partition table:

| Partition | Offset | Size |
|---|---:|---:|
| Bootloader write | `0x0000` | 21,200 bytes in the audited build |
| Partition table write | `0x8000` | 3,072 bytes |
| NVS (preserved) | `0x11000` | `0x6000` |
| otadata | `0x17000` | `0x2000` |
| PHY data (not rewritten) | `0x19000` | `0x1000` |
| ota_0 | `0x20000` | `0x270000` |
| ota_1 | `0x290000` | `0x270000` |
| prod_data | `0x500000` | `0x1000` |
| prod_bak | `0x501000` | `0x1000` |

The primary app is **2,035,712 bytes**, within the **2,555,904-byte** app slot, with **20.35% free**. These values must be regenerated for future builds; the flash scripts do not assume these sizes.

Before writes, the flash helper validates source/config/binary hashes, identifies the USB and chip MAC, checks S3R8 embedded PSRAM and 16 MB flash, reads security state, saves all 16,777,216 flash bytes, and compares **all partition types, subtypes, offsets and sizes** to the new table. Backups contain private credentials, are mode 0600 and Git-ignored. The helper uses the generated four-file flash plan, excludes NVS erase sectors, preserves image headers, verifies every written file, then resets the chip.

Completed host/build checks:

- Fresh standard T-Display-S3 build: passed, with applied-profile validation and app size check.
- Existing AIPI Muse UI profile, built in an isolated source copy: passed.
- SDK default ESP32-C5 profile, built in an isolated source copy: passed.
- SDK host suite: **183 tests run, passed, one skipped**. The skip is the host PSA/mbedcrypto-dependent Noise-core test because its host library is unavailable; the ESP32 production code still built.
- New compiled board harness: verifies manufacturer pin order, inactive RD/power-before-bus, landscape/crop, color-swap setting, buffer sizes, held-button state, nullable touch output, bounded PWM and 120 ms wake timing. Injects failure at each fallible startup call and checks that partial panel resources are released.
- New compiled BLE harness: tests RX/TX allocation failures, controller initialization failure, every service-registration/name failure, successful startup, and retries without repeated mutex allocation.
- Separate flash-plan suite: **9 tests passed**, using disposable copies of the actual build. It rejects absent octal PSRAM, a competing display backend, security provisioning, wrong chip, wrong app offset, an extra NVS write, a changed binary, and changed NVS geometry; the valid build passes.
- SDK/avatar compatibility-routing suite: **5 tests passed** against fake USB descriptors and wrappers, with no hardware writes. Build/flash delegation, selected USB identity, unmatched-board rejection, build-error propagation/logging and bench-layout rejection are exercised.
- Shell syntax and non-hardware flash-plan dry run: passed.

## Hardware acceptance and limits

The first repair build exposed an IDF 6 GDMA assertion caused by my incorrect 4-byte burst setting. That hardware failure is retained in `audit-evidence/first-repair-gdma-failure.txt`; it was corrected to the IDF default 32-byte burst and the harness was strengthened to check the S3-supported values. That failed boot was not treated as success.

The next hardware boot (`audit-evidence/post-fix-boot.txt`) reached:

```text
esp_psram: Found 8MB PSRAM device
esp_psram: SPI SRAM memory test OK
board.tdisplay: ST7789V I80: 8 data lines, 10 MHz, RGB565, 320x170, gap (0,35)
muse_ui: UI up: 320x170, 113 px Muse, 40 ms frames
muse: ready: free heap 20647 internal, 7210008 psram
```

There was no panic/reboot in that 25-second capture. BLE advertised, accepted a connection and reached the physical-confirmation state. The owner then confirmed **“Avatar/text visible; menu works.”** This establishes physical display output and GPIO14/menu operation independently of software logs. The local USB `>status` command also responded with `board="LilyGO T-Display-S3"`.

The subsequent passive capture (`audit-evidence/post-fix-running.txt`) recorded repeated heartbeats through 50 seconds with `setup=done wifi=up ws=up raw=up ble=off`, without panic or reboot. Provisioning and network-session progress were therefore observed on the actual board, rather than inferred from a build. This is a short functional observation, not a long-duration soak.

The final build adds the 120 ms reset-to-SLPOUT restriction, truthful BLE-request logging, and the bounded Wi-Fi country log. It was backed up, flashed and verified at all four generated offsets. Its separate final boot results are recorded below. The preceding reset-timing verification remains in `audit-evidence/reset-timing-boot.txt`.

**Final installed firmware:** `audit-evidence/final-boot.txt` records a complete 40-second reset/boot capture. PSRAM passed its test; UI startup completed at 1.531 s; Muse reported ready at 2.965 s with 22,403 bytes free internal heap and 7,210,668 bytes free PSRAM. Preserved pairing reconnected Wi-Fi and both network sessions by the 11-second heartbeat. Those states remained up through the 36-second heartbeat, with roughly 21 KiB free internal memory, an 11 KiB largest internal block and 6,142 KiB free PSRAM. There is no panic, assertion, reboot or display-transfer error in that final capture. This memory margin is measured for this short run and is not a guarantee for arbitrary future workload sizes.

Final source build/flash validation is current: the installed app is 2,035,712 bytes and all four flash-file digests verified. `audit-evidence/flash.txt`, `build-t-display-s3.txt`, `build-aipi-final.txt`, `build-default-c5-final.txt`, `host-tests.txt`, `flash-plan-tests.txt` and `sdk-routing-tests.txt` preserve the corresponding evidence. The firmware remains running after verification.

Battery operation/ADC accuracy, battery shutdown, external audio, touch variants, long-duration network soak and production OTA rollout remain unverified. Screen sleep/deep-sleep wake handlers were traced and checked in the board harness where applicable, but a full physical sleep/wake cycle was not exercised. There is no basis to diagnose permanent damage to earlier boards from this firmware evidence.

## Scope and reproducible follow-up

This audit covers the selected standard-board build and its active boot, display, UI, input, settings, BLE provisioning and network-state paths, plus build/flash helpers and contradictory project instructions. Other boards' peripheral drivers and hardware absent from this USB-only board are not proof-tested by this audit. The findings above are concrete repairs; they are not a guarantee that a large SDK contains no remaining defects.

Run `./build-t-display-s3.sh`, then `python3 tools/test-verify-t-display-s3.py` and `python3 tools/test-sdk-t-display-s3.py`. Flash this identified board with `./flash-t-display-s3.sh /dev/cu.usbmodem1101 24:58:7c:d3:96:30`. The flash helper rejects stale artifacts, verifies board identity and partition compatibility, creates its backup with private permissions, and makes a full backup before writing. It revalidates artifacts after the backup read, before any write. Fresh boards can use the canonical SDK overlay; this already provisioned board must keep the enclosing project's compatibility overlay to preserve its existing storage geometry.

## Shareable SDK contribution

`dist/t-display-s3-sdk-support-v0.1.0.zip` contains a clean source contribution against upstream SDK commit `b139b45064b4dcecf7bfe97e75bc7f99c10c28b6`, rather than the three earlier local GPIO-debugging commits. The consolidated archive includes one complete patch for 24 SDK source/documentation files, an installer, one README containing hardware/workflow/limits/validation and suggested PR text, vendor license notices and checksums. Source-file hashes are recorded in the manifest; a duplicate source overlay and separate review patches are no longer shipped.

During preparation, combined and sequential patches applied cleanly; all installed files matched the validated source. The canonical SDK profile built in that separate clean checkout, with a 4 MiB app slot and about 51.5% free. Its 183-test host suite passed with one optional host-crypto skip. The consolidated archive was extracted again, all checksums and CRCs verified, and its extracted installer applied successfully to another clean baseline.

No private credentials, generated sdkconfig, firmware image, flash backup, personal device identity or local filesystem paths are included. This board's project-specific compatibility bridge and partition overlay are excluded from the upstream contribution. The hardware validation remains on the preserved existing layout; no generic-layout firmware was flashed over it during packaging.

Obsolete root guides, expired login instructions, old examples/firmware copies, redundant wrappers/patches and the stale CI recipe were removed. The root keeps only `README.md` and this audit. The current audited build, canonical profile, credentials, source, tests, vendor notices and useful evidence remain. Original pre-repair and latest provisioned full-flash backups were checked against their saved SHA-256 hashes before three intermediate copies were deleted.
