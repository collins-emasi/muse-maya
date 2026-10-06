# Muse - Maya Quick Start Guide

## Setup Checklist

- [ ] Install Muse Code: `curl -fsSL https://dev.meta.ai/install.sh | sh`
- [ ] Get SDK token from [gadgets.muse.ai/settings/sdk-tokens](https://gadgets.muse.ai/settings/sdk-tokens)
- [ ] Install Muse app on your phone
- [ ] Have a USB data cable ready
- [ ] Identify your ESP32 board model

## Supported Boards

**Easiest to start with:**
- ESP32-C5 DevKitC-1 (works out of the box, no config needed)

**Also supported:**
- ESP32-S3 variations (Waveshare AMOLED, M5Stack, etc.)
- ESP32-C6 boards with/without PSRAM
- Home Assistant Voice Preview
- Seeed SenseCAP products
- And 20+ others (see AGENTS.md for full list)

## Quick Build & Flash

### Using Muse Code (Recommended)

```bash
cd muse-gadget-sdk/esp32
muse --disable-sandbox
```

Then ask Muse Code:
```
Build this firmware for my ESP32-C5 DevKitC-1 and flash it.
```

Watch the log, then:
```
Watch the serial log and tell me when it's ready to pair.
```

### Manual Build with ESP-IDF

Requires ESP-IDF v6.0.1 installed and activated.

```bash
cd muse-gadget-sdk/esp32

# For ESP32-C5 DevKitC-1 (default)
idf.py build
idf.py flash monitor

# For other boards
tools/board.sh BOARD build      # Replace BOARD with your device
tools/board.sh BOARD flash monitor
```

## Important Notes

1. **SDK Token Required**: Every build needs `CONFIG_GADGET_SDK_TOKEN="mgst_…"` 
   - Set via `idf.py menuconfig` or directly in `build/sdkconfig`
   - Never commit your token!

2. **Board Configurations**: Different boards have different overlays
   - Default: `sdkconfig.defaults`
   - Board-specific: `devices/sdkconfig.BOARDNAME`

3. **USB Serial Port**: Flashing requires direct access to the serial port
   - May need to run outside sandbox environments

## Development Workflow

1. **Modify firmware** in `main/` (main.c, app.c, etc.)
2. **Rebuild**: `idf.py build`
3. **Flash**: `idf.py flash`
4. **Monitor**: `idf.py monitor` (Ctrl+] to exit)

## Common Commands

```bash
# Full build + flash + monitor in one go
idf.py build && idf.py flash && idf.py monitor

# Menuconfig (interactive settings)
idf.py menuconfig

# Clean rebuild
idf.py clean
idf.py fullclean

# Monitor logs only (don't reflash)
idf.py monitor
```

## Pairing Your Device

Once flashed and ready:
1. Press the device's BOOT button (or equivalent)
2. Open the Muse app on your phone
3. Scan the QR code from the device display
4. Follow the app's pairing flow

## Troubleshooting

**"Module not found" errors during build**: Check ESP-IDF version (must be v6.0.1)

**LED not working**: Some boards have different LED color orders
- Try toggling `CONFIG_HOMEHUB_LED_RGB_ORDER` in menuconfig

**Serial port permission denied**: May need `sudo` or udev rules on Linux

**Device won't flash**: Check USB cable is data-capable, try different USB port

## Next Steps

- Read [muse-gadget-sdk/esp32/AGENTS.md](muse-gadget-sdk/esp32/AGENTS.md) for detailed build recipes
- Check [muse-gadget-sdk/esp32/README.md](muse-gadget-sdk/esp32/README.md) for full documentation
- Explore device overlays in `muse-gadget-sdk/esp32/devices/` for hardware customization
- Join the Muse developer community for support

## Resources

- [Muse Code IDE](https://developer.meta.com/ai/lp/muse-code/)
- [Muse Gadget SDK Repository](https://github.com/facebookincubator/muse-gadget-sdk)
- [SDK Terms](https://gadgets.muse.ai/sdk-terms)
- [Muse Gadgets Dashboard](https://gadgets.muse.ai/)
