# T-Display-S3 Example Code

This directory contains example code for building Muse applications on the LilyGO T-Display-S3 board.

## Examples

### display_init.c
Basic initialization of the ST7789 display controller.

**Features:**
- SPI bus configuration for display
- GPIO setup for control pins (DC, RST, BL)
- Reset sequence
- ST7789 command initialization
- Backlight control

**To use:**
```bash
cp display_init.c ../muse-gadget-sdk/esp32/main/
cd ../muse-gadget-sdk/esp32
./tools/board.sh lilygo-t-display-s3 build flash
```

## Hardware Connections

Connect the T-Display-S3 as follows for these examples:

```
T-Display-S3 Pin  →  Signal  →  Use
──────────────────────────────────
GPIO 3            →  MOSI    →  SPI data in
GPIO 6            →  CLK     →  SPI clock
GPIO 10           →  CS      →  Chip select
GPIO 8            →  DC      →  Data/Command
GPIO 9            →  RST     →  Reset
GPIO 38           →  BL      →  Backlight
GND               →  GND     →  Ground
```

## Building Examples

All examples are designed to work with the Muse Gadget SDK build system:

```bash
# Build for T-Display-S3
./tools/board.sh lilygo-t-display-s3 build

# Flash to device
./tools/board.sh lilygo-t-display-s3 flash --port /dev/cu.usbmodem*

# Monitor serial output
./tools/board.sh lilygo-t-display-s3 monitor --port /dev/cu.usbmodem*
```

## Serial Output

After flashing, you should see output like:

```
I (0) cpu_start: Starting scheduler on APP CPU.
I (11) LCD_INIT: T-Display-S3 Display Initialization Example
I (11) LCD_INIT: Initializing SPI bus...
I (11) LCD_INIT: SPI bus initialized
I (11) LCD_INIT: Initializing ST7789 display...
I (112) LCD_INIT: Display initialized successfully!
I (112) LCD_INIT: Display ready for use!
I (112) LCD_INIT: Resolution: 320×170 pixels
I (113) LCD_INIT: Color mode: 16-bit RGB565
```

## Adding Your Own Examples

1. Create a `.c` file in this directory
2. Add documentation in this README
3. Test with the build system
4. Submit as a PR to contribute back to Muse SDK

## Troubleshooting

**Display doesn't initialize:**
- Check GPIO pin assignments match your board revision
- Verify SPI clock frequency (40MHz recommended)
- Check serial output for error messages
- Ensure backlight power is correct

**SPI communication errors:**
- Verify CS, CLK, MOSI pins on breadboard
- Try reducing SPI clock speed (20MHz)
- Check for loose connections

**Device won't flash:**
- Hold BOOT button while pressing RESET
- Try lower baud rate: `--baud 115200`
- Check USB cable (data cable, not power-only)

---

**Last Updated**: 2026-10-06
**Tested With**: ESP-IDF v6.0.1, T-Display-S3 (rev 1.5)
