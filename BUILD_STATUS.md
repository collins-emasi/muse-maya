# Muse - Maya Build Status

## Current Status: ⚠️ Toolchain Configuration Issue

### Problem
The ESP-IDF on macOS is encountering a system header conflict with the Espressif xtensa toolchain. The build system is picking up system stdio.h instead of the toolchain's stdio.h, causing type definition mismatches.

### What We've Accomplished ✅
- Muse Code installed (v1.4.3)
- ESP-IDF v6.0.1 installed and configured
- SDK token configured in build system
- T-Display-S3 target properly configured (ESP32-S3, 16MB flash, 8MB PSRAM)
- All project files and documentation in place

### Solutions to Try

#### Option 1: Use Pre-built Binary (Fastest)
The Muse Gadget SDK may have pre-built binaries available for the T-Display-S3. Check:
```bash
cd muse-gadget-sdk/esp32
find . -name "*.bin" -o -name "*.elf"
```

#### Option 2: Docker Build (Recommended)
Build inside a Docker container to avoid macOS-specific issues:
```bash
# Use official ESP-IDF Docker image
docker run --rm -v $(pwd):/project espressif/idf:v6.0.1 \
  bash -c "cd /project && idf.py -B build build"
```

#### Option 3: Fix System Headers (Advanced)
Add compiler flags to explicitly include toolchain headers:
```bash
export CFLAGS="-I/Users/emasi/.espressif/tools/xtensa-esp-elf/esp-15.2.0_20251204/xtensa-esp-elf/include"
idf.py build
```

#### Option 4: Use Linux VM or WSL2
If you have access to a Linux machine or WSL2, the build should work directly.

### Alternative: Use Muse Code Directly
Once the billing issue is resolved on your Meta account, Muse Code can handle the build automatically:
```bash
cd muse-gadget-sdk/esp32
muse --disable-sandbox
# Then ask: "Build and flash this firmware for my T-Display-S3"
```

### Next Steps
1. Try Docker build (Option 2) - most reliable
2. Or check for pre-built binaries (Option 1)
3. Or resolve the Meta billing issue to use Muse Code

Let me know which option you'd like to pursue!

---

**Files Created:**
- build/ directory with proper sdkconfig for T-Display-S3
- All documentation and guides
- Git repository with version tracking

**Ready to Flash When Binary is Available:**
- Device: T-Display-S3 (ESP32-S3)
- USB Connection: Ready
- SDK Token: Configured
- Build Configuration: Complete
