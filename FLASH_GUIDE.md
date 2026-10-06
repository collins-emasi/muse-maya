# Flashing Muse Firmware to T-Display-S3

## Prerequisites
- T-Display-S3 device connected via USB-C data cable
- `esptool.py` installed: `pip install esptool`
- Firmware files from GitHub Actions build

## Step 1: Get the Firmware

Once the GitHub Actions build completes:

1. Go to: https://github.com/collins-emasi/muse-maya/actions
2. Click the latest "Build Muse Firmware" run
3. Scroll to "Artifacts" section
4. Download "muse-firmware" (contains .bin files)
5. Extract the ZIP file

## Step 2: Find Your Device Port

### macOS/Linux:
```bash
ls -la /dev/tty.usb* /dev/cu.usb* 2>/dev/null
# Look for /dev/cu.usbserial-* or /dev/ttyUSB*
```

### Windows:
```bash
# Check Device Manager or:
wmic logicaldisk get name
```

## Step 3: Put Device in Flash Mode

1. **Hold the BOOT button** on your T-Display-S3
2. **While holding BOOT**, press and release the RESET button
3. Release the BOOT button
4. Device is now in flash mode (screen won't respond)

## Step 4: Flash the Firmware

### Option A: Using ESP-IDF (if you have it)

```bash
cd muse-gadget-sdk/esp32
idf.py -B build flash --port /dev/cu.usbserial-XXXXX
```

### Option B: Using esptool.py (Recommended)

```bash
# Download/unzip firmware from GitHub Actions first

# Flash all components at once:
esptool.py --chip esp32s3 --port /dev/cu.usbserial-XXXXX \
  --baud 460800 --before default_reset --after hard_reset write_flash \
  --flash_mode dio --flash_freq 40m --flash_size keep \
  0x0 bootloader.bin \
  0x8000 partition-table.bin \
  0x10000 muse-gadget.bin
```

Replace `/dev/cu.usbserial-XXXXX` with your actual device port.

## Step 5: Verify Flash

After flashing completes:

```bash
# Optional: Monitor device output
idf.py -B build monitor --port /dev/cu.usbserial-XXXXX
```

You should see:
- Boot messages
- Network scanning
- Device ready to pair message

## Step 6: Pair with Muse App

1. Download Muse app on your phone (iOS/Android)
2. Open the app
3. Look for QR code on your T-Display-S3 screen
4. Scan QR code with Muse app
5. Follow pairing instructions

## Troubleshooting

### Device not recognized
- Try different USB cable (must be data cable, not power-only)
- Restart device: Press RESET button

### Flash verification fails
- Device may not be in flash mode; retry Step 2
- Try lower baud rate: `--baud 115200`

### Blank screen after flash
- This is normal! Give it 10 seconds to boot
- Check serial output with `monitor` command

### Device boots but no pairing QR code
- Check if firmware built successfully in Actions
- Device may need network configuration first

## Success Indicators

✅ Device boots and shows Muse welcome screen
✅ QR code appears for app pairing
✅ Serial output shows "Device ready"
✅ Muse app can detect and pair device

---

**Need help?**
- Check GitHub Actions logs: https://github.com/collins-emasi/muse-maya/actions
- Espressif docs: https://docs.espressif.com/projects/esp-idf/
- Muse SDK docs: https://github.com/facebookincubator/muse-gadget-sdk
