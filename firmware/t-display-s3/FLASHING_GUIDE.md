# T-Display-S3 Firmware Flashing Guide

## Overview
This guide walks through flashing the compiled Muse firmware to a LilyGO T-Display-S3 ESP32-S3 board.

## Prerequisites
- LilyGO T-Display-S3 board
- USB-C cable (data + power)
- `esptool.py` installed: `pip install esptool`
- Firmware binaries from successful build

## Firmware Files
- **bootloader/bootloader.bin** (21 KB) - Board bootloader
- **partition_table/partition-table.bin** (3 KB) - Flash partition layout
- **muse-gadget.bin** (1.6 MB) - Main Muse application firmware

## Step 1: Prepare the Device

### Connect via USB
Plug the T-Display-S3 into your Mac using a USB-C cable.

### Identify the Serial Port
```bash
ls -la /dev/cu.usbserial*
# Should show: /dev/cu.usbserial-XXXXXXXXX
```

If you see multiple, use `system_profiler SPUSBDataType | grep -A 10 "T-Display"` to identify the correct one.

### Verify Connection
```bash
python3 -m esptool --port /dev/cu.usbserial-XXXXXXXXX chip_id
# Should return chip_id: 0x????
```

## Step 2: Enter Bootloader Mode

The T-Display-S3 enters bootloader mode automatically when flashing via esptool. However, if you need to manually enter it:

1. Hold **BOOT** button (near USB-C)
2. Press **RESET** button (right of BOOT)
3. Release **RESET** then **BOOT**
4. Device enters DFU mode

## Step 3: Erase Flash (First Time Only)

```bash
python3 -m esptool --chip esp32s3 --port /dev/cu.usbserial-XXXXXXXXX \
  --baud 921600 erase_flash
```

This wipes the entire 16MB flash. Takes 30-60 seconds.

## Step 4: Flash Firmware

Run this command to flash all three binary components:

```bash
python3 -m esptool --chip esp32s3 --port /dev/cu.usbserial-XXXXXXXXX \
  --baud 921600 --before default_reset --after hard_reset write_flash \
  0x0000 bootloader/bootloader.bin \
  0x8000 partition_table/partition-table.bin \
  0x10000 muse-gadget.bin
```

### What This Does
- `0x0000` → Bootloader at start of flash
- `0x8000` → Partition table (required for OTA updates)
- `0x10000` → Main application firmware

### Expected Output
```
esptool.py v4.6.2
Found 1 serial ports
Serial port /dev/cu.usbserial-XXXXXXXXX
Connecting....
Chip is ESP32-S3 (revision v0.2)
Features: WiFi, BLE, Embedded PSRAM
Crystal is 40MHz
MAC: 18:xx:xx:xx:xx:xx
Uploading stub...
Running stub...
Stub running...

[==========         ] Writing at 0x0010f240 (79%)
```

### Typical Timing
- Erase: 30-60 seconds
- Flash: 3-5 minutes total
- Boot: 5-10 seconds

## Step 5: Boot and Verify

1. Once flashing completes, the device auto-resets
2. Watch the serial output for boot messages:
   ```
   I (23) boot: ESP-IDF v6.0.1 2nd stage bootloader
   I (23) boot: compile time XXX
   ```

3. The T-Display-S3 display should show startup animation

## Step 6: Check Serial Logs

Monitor device output while booting:

```bash
python3 -m esptool --port /dev/cu.usbserial-XXXXXXXXX \
  --baud 115200 read_flash_status
```

For continuous logs:
```bash
picocom -b 115200 /dev/cu.usbserial-XXXXXXXXX
# Press Ctrl-A then Ctrl-X to exit
```

## Troubleshooting

### "Failed to connect to ESP32"
- Ensure USB cable is data-capable (not charging-only)
- Try different USB port
- Manually enter bootloader mode (see Step 2)
- Try slower baud rate: `--baud 115200`

### "JTAG mismatch"
- Check you're using `--chip esp32s3` (not esp32 or esp32c3)
- Verify T-Display-S3 board model

### "Flash write errors"
- Try erasing flash first: `erase_flash`
- Lower baud rate to 115200
- Use shorter USB cable

### Device doesn't boot after flashing
- Check partition table at offset 0x8000
- Verify muse-gadget.bin wasn't truncated (should be ~1.6MB)
- Try flashing just bootloader first: `write_flash 0x0000 bootloader.bin`

### Display Shows Nothing
- Device may boot into recovery mode
- Try: hold BOOT, press and hold RESET for 3 seconds
- Release both buttons, power cycle

## Next Steps

After successful flashing:

1. **Configure WiFi and Credentials**
   - Use Muse Companion App (iOS/Android)
   - Scan QR code from device display
   - Follow OAuth device code flow

2. **Test Voice Input**
   - Tap microphone icon on display
   - Speak your request
   - Device should respond with visual feedback

3. **Verify Logs**
   - Monitor serial port for errors
   - Check `BUILD_STATUS.md` for known issues

## Advanced: Backup Current Firmware

Before flashing, save existing firmware:

```bash
python3 -m esptool --chip esp32s3 --port /dev/cu.usbserial-XXXXXXXXX \
  --baud 921600 read_flash 0x0000 16777216 original_flash.bin
```

This creates a 16MB backup of the entire flash for recovery.

## References
- [ESP32-S3 Documentation](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/index.html)
- [esptool.py GitHub](https://github.com/espressif/esptool)
- [LilyGO T-Display-S3 Specs](https://github.com/Xinyuan-LilyGO/T-Display-S3)

