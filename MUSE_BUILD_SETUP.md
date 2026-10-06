# Muse Build Setup for T-Display-S3

## Status: Ready for First Build

The Muse environment is partially set up. Here's what's left:

### 1. Initialize Muse Code (One-Time Setup)

```bash
cd /Users/emasi/Personal/Projects/Muse - Maya/muse-gadget-sdk/esp32
muse --disable-sandbox
```

This will:
- Open an interactive Muse Code session
- Ask you to trust the workspace (click "Trust")
- Prompt you to log in with your browser
- Set up the sandbox if needed

### 2. Build Commands in Muse Code

Once logged in, try these prompts:

**First build attempt:**
```
Build this firmware for my T-Display-S3 ESP32-S3 board. 
The board has 16MB flash, 8MB PSRAM, and a small display.
What do you need from me?
```

**If it asks for more board info:**
```
The T-Display-S3 is a generic ESP32-S3 with a built-in display. 
You can use the default ESP32-S3 DevKitC-1 configuration as a base.
The SDK token is already in the build/sdkconfig file.
```

**To build and flash:**
```
Build the firmware and flash it to the device.
```

**To watch the serial logs:**
```
Watch the serial log and tell me when the device is ready to pair.
```

## Pre-Build Configuration

The build directory is already configured with:
- ✅ SDK token: `mgst_bhfCfcSEEOrt96Kou_FoHP91BtFpMOnbSb95ZAUPbe0`
- ✅ Build directory: `./build/`
- ✅ Target: ESP32-S3 (compatible with T-Display-S3)

## Expected Build Process

Muse Code will:
1. Download ESP-IDF v6.0.1 (if not already cached)
2. Configure the build environment
3. Build the firmware binary
4. Detect your USB device
5. Flash the firmware via USB serial
6. Monitor the boot sequence

## Troubleshooting

### Port Permission Issues
```bash
# macOS: may just work
# Linux: you might need
sudo usermod -a -G dialout $USER
# Then log out and back in
```

### USB Not Detected
- Check the USB cable is data-capable (not power-only)
- Try a different USB port
- Hold the BOOT button while plugging in

### Build Fails
- Make sure you're in the esp32 directory
- Check that muse-gadget-sdk is a valid submodule: `git submodule status`
- Try `muse --disable-sandbox` to disable security sandbox if it's blocking file access

## Next Steps After Build

1. Device will show ready status in serial log
2. Open Muse app on your phone
3. Press the BOOT button on your device
4. Scan the QR code shown on device display
5. Follow Muse app pairing flow
