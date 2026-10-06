# Muse - Maya

Building custom gadgets and integrations with the **Meta Muse Gadget SDK**.

This project is separate from the original Maya Bot project and focuses on Muse-based IoT device development and integration.

## Project Structure

- **muse-gadget-sdk/** - Submodule containing the official Meta Muse Gadget SDK
  - `esp32/` - ESP32 firmware and device SDK
  - `linux/` - Linux device SDK
  - `skills/` - Pre-built Muse agent skills

## Getting Started

### Prerequisites

- macOS or Linux
- USB cable with data transfer capability
- [Muse Code](https://developer.meta.com/ai/lp/muse-code/) installed:
  ```bash
  curl -fsSL https://dev.meta.ai/install.sh | sh
  ```
- An SDK token from [gadgets.muse.ai](https://gadgets.muse.ai/settings/sdk-tokens)
- The Muse app on your phone

### Supported Hardware

- **ESP32-C5 DevKitC-1** (recommended - works out of the box)
- **Waveshare ESP32-S3 AMOLED**
- Other ESP32-compatible boards (requires device-specific config)

### Quick Start with Muse Code

```bash
cd muse-gadget-sdk/esp32
muse --disable-sandbox
```

Then ask Muse Code:
- "Build this firmware for my [board] and flash it"
- "Watch the serial log and tell me when it's ready to pair"

For more details, see [muse-gadget-sdk/esp32/README.md](muse-gadget-sdk/esp32/README.md) and [muse-gadget-sdk/esp32/AGENTS.md](muse-gadget-sdk/esp32/AGENTS.md).

## Development

All development tasks and AI-driven building happens through Muse Code and the AGENTS.md specifications in the submodule. The AI can:

- Build firmware for different ESP32 boards
- Flash devices over USB
- Monitor serial logs
- Add hardware support
- Customize UI and functionality

## Documentation

- [Muse Gadget SDK README](muse-gadget-sdk/README.md)
- [ESP32 Firmware Guide](muse-gadget-sdk/esp32/README.md)
- [Agent Capabilities](muse-gadget-sdk/esp32/AGENTS.md)

## License

This project includes the official Muse Gadget SDK which is licensed under the Apache License 2.0. See [muse-gadget-sdk/LICENSE](muse-gadget-sdk/LICENSE) for details.

---

**Note:** Built by hackers, for hackers, just for fun. Flashing custom firmware can brick boards and void warranties. Proceed at your own risk!
