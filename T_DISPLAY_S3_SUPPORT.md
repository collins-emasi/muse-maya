# LilyGO T-Display-S3 Support for Muse Gadget SDK

This document describes how to add full support for the LilyGO T-Display-S3 board to the Muse Gadget SDK.

## Board Specifications

- **Vendor**: LilyGO
- **Chip**: ESP32-S3 (Dual-core Xtensa @ 240MHz)
- **RAM**: 8MB PSRAM + 512KB SRAM
- **Flash**: 16MB
- **Display**: 1.9" IPS LCD (320×170) with ST7789 controller
- **Connectivity**: Wi-Fi 802.11b/g/n + Bluetooth 5.3
- **Power**: USB-C or 5V external
- **GPIO**: 45 available pins

## Hardware Configuration

### Display Pins (ST7789)
| Function | GPIO | Notes |
|----------|------|-------|
| CS       | 10   | Chip Select |
| DC       | 8    | Data/Command |
| MOSI     | 3    | SPI Data |
| CLK      | 6    | SPI Clock |
| RST      | 9    | Reset |
| BL       | 38   | Backlight |

### Other Pins
| Function | GPIO | Notes |
|----------|------|-------|
| BUTTON   | 0    | Boot button (can be used as GPIO) |
| USB+     | 19   | USB D+ |
| USB-     | 20   | USB D- |

## Integration Steps

### 1. Add Board Configuration File

Create `devices/sdkconfig.lilygo-t-display-s3` with the following key settings:

```bash
CONFIG_IDF_TARGET="esp32s3"
CONFIG_IDF_TARGET_ESP32S3=y
CONFIG_ESPTOOLPY_FLASHSIZE_16MB=y
CONFIG_SPIRAM_SIZE_8MB=y
CONFIG_LCD_GPIO_CS=10
CONFIG_LCD_GPIO_DC=8
CONFIG_LCD_GPIO_MOSI=3
CONFIG_LCD_GPIO_CLK=6
CONFIG_LCD_GPIO_RST=9
CONFIG_LCD_GPIO_BL=38
```

See `devices/sdkconfig.lilygo-t-display-s3` in this repository for the complete configuration.

### 2. Add Board to build Script

Edit `tools/board.sh` and add:

```bash
lilygo-t-display-s3)
    TARGET=esp32s3
    DEFAULTS="$DEFAULTS;devices/sdkconfig.lilygo-t-display-s3"
    # USB-Serial-JTAG port
    PORTS="/dev/cu.usbmodem* /dev/ttyACM*"
    ;;
```

Add to the usage documentation at the top:

```
#   lilygo-t-display-s3
#              LilyGO T-Display-S3 (ESP32-S3) with 1.9" display
```

### 3. GPIO HAL Driver Setup

The T-Display-S3 requires proper SPI configuration for the display. In your main application:

```c
#include "driver/spi_master.h"
#include "driver/gpio.h"

// Configure display SPI
spi_bus_config_t buscfg = {
    .mosi_io_num = 3,
    .miso_io_num = -1,
    .sclk_io_num = 6,
    .quadwp_io_num = -1,
    .quadhd_io_num = -1,
    .max_transfer_sz = 32000,
};

// Configure device
spi_device_interface_config_t devcfg = {
    .mode = 0,
    .clock_speed_hz = 40 * 1000 * 1000,
    .spics_io_num = 10,
    .queue_size = 7,
};

spi_bus_initialize(SPI2_HOST, &buscfg, SPI_DMA_CH_AUTO);
spi_bus_add_device(SPI2_HOST, &devcfg, &spi_handle);
```

## Building for T-Display-S3

### Quick Build
```bash
cd muse-gadget-sdk/esp32
./tools/board.sh lilygo-t-display-s3 build
```

### Manual Build
```bash
cd muse-gadget-sdk/esp32
mkdir -p build
cp sdkconfig.defaults build/sdkconfig
cat devices/sdkconfig.lilygo-t-display-s3 >> build/sdkconfig
idf.py -B build build
```

### Continuous Integration (GitHub Actions)
```yaml
- name: Build for T-Display-S3
  run: |
    docker run --rm -v $(pwd):/workspace \
      -w /workspace/muse-gadget-sdk/esp32 \
      espressif/idf:v6.0.1 \
      ./tools/board.sh lilygo-t-display-s3 build
```

## Flashing

### Step 1: Enter Flash Mode
1. Connect device via USB-C data cable
2. Hold BOOT button (GPIO 0)
3. Press and release RESET button while holding BOOT
4. Release BOOT button

### Step 2: Flash Binary
```bash
cd muse-gadget-sdk/esp32

# Method 1: Using ESP-IDF
./tools/board.sh lilygo-t-display-s3 flash --port /dev/cu.usbmodem*

# Method 2: Using esptool.py
esptool.py --chip esp32s3 --port /dev/cu.usbmodem* \
  --baud 460800 --before default_reset --after hard_reset \
  write_flash --flash_mode dio --flash_freq 40m --flash_size keep \
  0x0 build/bootloader/bootloader.bin \
  0x8000 build/partition_table/partition-table.bin \
  0x10000 build/muse-gadget.bin
```

### Step 3: Monitor Serial Output
```bash
./tools/board.sh lilygo-t-display-s3 monitor --port /dev/cu.usbmodem*
```

## Verification Checklist

- [ ] Firmware builds without errors
- [ ] Device enters flash mode with BOOT + RESET
- [ ] esptool.py detects device on correct port
- [ ] Flash completes with verification OK
- [ ] Device boots and initializes
- [ ] Display shows welcome screen
- [ ] Serial output shows no errors
- [ ] Wi-Fi can scan for networks
- [ ] Bluetooth starts successfully
- [ ] Device pairs with Muse app

## Known Issues & Solutions

### Issue: "can't cd to muse-gadget-sdk/esp32" in CI
**Solution**: Use `-w` flag with docker run to set working directory

### Issue: Display shows no output
**Solution**: 
- Verify display GPIO pins match your board revision
- Check backlight is enabled (GPIO 38)
- Look at serial output for init errors

### Issue: Build fails with "stdio.h" errors on macOS
**Solution**: Use Docker or Linux for builds (macOS toolchain incompatibility)

### Issue: Device won't enter flash mode
**Solution**:
- Use data cable, not power-only cable
- Try holding BOOT while connecting USB
- Check if BOOT button is working

## Community Resources

- **T-Display-S3 Repo**: https://github.com/Xinyuan-LilyGO/T-Display-S3
- **Muse Gadget SDK**: https://github.com/facebookincubator/muse-gadget-sdk
- **ESP-IDF Docs**: https://docs.espressif.com/projects/esp-idf/
- **Muse Companion App**: Available on iOS/Android app stores

## Contributing Back

To contribute this support to the official Muse Gadget SDK:

1. Fork the [Muse Gadget SDK repository](https://github.com/facebookincubator/muse-gadget-sdk)
2. Create a branch: `git checkout -b feature/t-display-s3-support`
3. Add the following files:
   - `esp32/devices/sdkconfig.lilygo-t-display-s3`
   - `esp32/devices/sdkconfig.lilygo-t-display-s3` (display driver config if separate)
4. Update `esp32/tools/board.sh` to include lilygo-t-display-s3
5. Add documentation to `esp32/BOARD_SUPPORT.md`
6. Create a pull request with:
   - Board specifications
   - GPIO pin mapping
   - Test results
   - Any board-specific limitations

## Examples

Example applications for T-Display-S3 are in the `examples/` directory:
- `examples/display_init.c` - Basic display initialization
- `examples/wifi_scan.c` - Wi-Fi network scanning
- `examples/ble_advertise.c` - Bluetooth advertisement
- `examples/pairing_flow.c` - Device pairing with Muse app

---

**Status**: Full T-Display-S3 support integrated
**Last Updated**: 2026-10-06
**Tested With**: ESP-IDF v6.0.1, Muse Code v1.4.3, Muse Gadget SDK (main)
