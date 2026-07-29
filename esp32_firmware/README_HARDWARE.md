# ESP32 Hardware & Wake-on-LAN Setup Guide

This guide explains how to set up your ESP32 board to turn on your PC remotely via **Wake-on-LAN (WoL)** or a physical relay header.

---

## 1. Finding Your PC's MAC Address (Windows)
1. Open PowerShell / Command Prompt on your PC.
2. Run:
   ```powershell
   getmac /v /fo list
   ```
   or
   ```powershell
   ipconfig /all
   ```
3. Find your active **Ethernet Adapter** (or Wi-Fi adapter if WoWLAN supported).
4. Copy the **Physical Address** (Format: `AA-BB-CC-DD-EE-FF`).
5. Open `esp32_firmware/src/main.cpp` and update `TARGET_MAC`:
   ```cpp
   uint8_t TARGET_MAC[6] = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF};
   ```

---

## 2. Enabling Wake-on-LAN in Windows & BIOS

### A. BIOS Setup:
1. Restart PC and enter BIOS setup (usually press `F2`, `DEL`, or `F12` on startup).
2. Go to **Advanced / Power Management / PCI Express Configuration**.
3. Enable **Wake on LAN**, **Power On By PCIe/PME**, or **Resume by LAN**.
4. Save & Exit.

### B. Windows Setup:
1. Open **Device Manager** (`Win + X` -> Device Manager).
2. Expand **Network Adapters**, right-click your Ethernet adapter -> **Properties**.
3. Go to **Power Management** tab:
   - Check `Allow this device to wake the computer`.
   - Check `Only allow a magic packet to wake the computer`.
4. Go to **Advanced** tab:
   - Find `Wake on Magic Packet` -> Set to **Enabled**.
   - Find `Shutdown Wake-On-LAN` -> Set to **Enabled**.
5. Disable Windows Fast Startup (Crucial):
   - Open **Control Panel** -> **Power Options**.
   - Click `Choose what the power buttons do`.
   - Click `Change settings that are currently unavailable`.
   - Uncheck `Turn on fast startup (recommended)`. Click **Save changes**.

---

## 3. Optional Hardware Power Switch Wiring (Relay / Optocoupler)
If your motherboard BIOS does not support Wake-on-LAN, you can connect a 5V relay module or 4N35 optocoupler in parallel with your PC's power button header (`PWR_BTN`):

- **ESP32 GPIO 18** -> Relay Module `IN` (or Optocoupler Pin 1 via 220Ω resistor).
- **ESP32 GND** -> Relay `GND`.
- **ESP32 5V (VIN)** -> Relay `VCC`.
- **Relay COM & NO Pins** -> Connected to Motherboard `POWER SW` pins.

Calling `POST http://<esp32-ip>/relay` will trigger a 500ms pulse to turn on/off the PC physically!

---

## 4. How to Flashing Firmware to ESP32
Using **Arduino IDE**:
1. Select board: `ESP32 Dev Module`.
2. Update `WIFI_SSID`, `WIFI_PASS`, and `TARGET_MAC` in `main.cpp`.
3. Connect ESP32 via USB and click **Upload**.

Using **PlatformIO**:
```bash
cd esp32_firmware
pio run --target upload
```

## or uplode ESP32_server.ino file from Arduino Id and insert wifi name  and password

const char* ssid = "";
const char* password = "";

