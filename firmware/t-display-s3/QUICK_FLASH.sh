#!/bin/bash
# Quick flashing script for T-Display-S3
# Usage: ./QUICK_FLASH.sh /dev/cu.usbserial-XXXXXXXXX

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <serial_port>"
    echo "Example: $0 /dev/cu.usbserial-XXXXXXXXX"
    echo ""
    echo "Available serial ports:"
    ls -la /dev/cu.usbserial* 2>/dev/null || echo "No serial ports found"
    exit 1
fi

PORT=$1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔧 T-Display-S3 Firmware Flashing Script"
echo "=========================================="
echo "Serial Port: $PORT"
echo "Firmware dir: $SCRIPT_DIR"
echo ""

# Check if firmware files exist
if [ ! -f "$SCRIPT_DIR/bootloader/bootloader.bin" ]; then
    echo "❌ Error: bootloader/bootloader.bin not found"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/partition_table/partition-table.bin" ]; then
    echo "❌ Error: partition_table/partition-table.bin not found"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/muse-gadget.bin" ]; then
    echo "❌ Error: muse-gadget.bin not found"
    exit 1
fi

echo "✅ All firmware files found"
echo ""

# Verify connection
echo "📡 Verifying connection..."
if ! python3 -m esptool --port "$PORT" chip_id > /dev/null 2>&1; then
    echo "❌ Cannot connect to device at $PORT"
    echo "Please check:"
    echo "  - USB cable is connected and data-capable"
    echo "  - Correct serial port is specified"
    echo "  - Device is powered on"
    exit 1
fi
echo "✅ Device connected"
echo ""

# Erase
echo "🗑️  Erasing flash (this takes 30-60 seconds)..."
python3 -m esptool --chip esp32s3 --port "$PORT" \
    --baud 921600 erase_flash

echo "✅ Flash erased"
echo ""

# Flash
echo "📝 Flashing firmware..."
python3 -m esptool --chip esp32s3 --port "$PORT" \
    --baud 921600 --before default_reset --after hard_reset write_flash \
    0x0000 "$SCRIPT_DIR/bootloader/bootloader.bin" \
    0x8000 "$SCRIPT_DIR/partition_table/partition-table.bin" \
    0x10000 "$SCRIPT_DIR/muse-gadget.bin"

echo ""
echo "✅ Flashing complete!"
echo ""
echo "📱 Device should boot in 5-10 seconds"
echo "🎨 Look for startup animation on the display"
echo ""
echo "Next steps:"
echo "  1. Wait for device to fully boot"
echo "  2. Open Muse Companion App on your phone"
echo "  3. Scan QR code from device display"
echo "  4. Follow OAuth device code flow"
echo ""
echo "For help, see FLASHING_GUIDE.md"
