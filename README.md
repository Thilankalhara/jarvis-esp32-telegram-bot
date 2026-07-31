# 🤖 J.A.R.V.I.S. - AI Remote PC Assistant & ESP32 Automation

> Turn your PC into Tony Stark's J.A.R.V.I.S. Control, automate, wake up, and complete tasks on your home PC from anywhere in the world using AI voice & text commands over Telegram & Tailscale!

> GitHub: https://github.com/Thilankalhara/jarvis-esp32-telegram-bot

---


> **Pre-built standalone Windows executable** — no Python installation required!

| File | Description |
|------|-------------|
| `JARVIS_Control_Center.exe` | Main GUI application with mute/unmute voice feedback and system control buttons |
| `JARVIS_Setup_v2.1.exe` | Full Windows installer for the control center and bundled assets |
| `START_JARVIS.bat` | Recommended launcher (checks `.env` first) |
| `.env.template` | Copy to `.env` and fill in your credentials |

### 📥 Release Download
- GitHub release page: https://github.com/Thilankalhara/jarvis-esp32-telegram-bot/releases
- After publishing a release, download these assets from the release page:
  - `JARVIS_Control_Center.exe`
  - `JARVIS_Setup_v2.1.exe`
  - `START_JARVIS.bat`
  - `.env.template`

> Note: the direct asset URLs only work after a release is published with those files attached. If you haven’t created a release yet, use the release page link above and upload the assets there.

### 📦 How to Download the Installer
1. Open the GitHub release page above.
2. Select the latest release entry.
3. Download `JARVIS_Setup_v2.1.exe` from the list of attached assets.
4. Run the installer and follow the setup prompts.
5. Launch `JARVIS_Control_Center.exe` from the installed application folder or the Windows Start Menu.

### 🧩 If You Only Want the Standalone GUI
Download these instead:
- `JARVIS_Control_Center.exe`
- `START_JARVIS.bat`
- `.env.template`

Then:
1. Place them in the same folder.
2. Copy `.env.template` to `.env` and edit it.
3. Run `START_JARVIS.bat` or `JARVIS_Control_Center.exe` directly.

> If the release asset is not available, publish a new release and upload the built files as assets. For large files over 50 MB, GitHub may recommend Git LFS.

### 🔨 Build EXE from Source
```bash
# Install dependencies first
pip install -r pc_agent/requirements.txt

# Build the standalone EXE
python build_exe.py
```
Output will be in: `dist/JARVIS_Control_Center/`

After building, the release assets are:
- `dist/JARVIS_Control_Center/JARVIS_Control_Center.exe`
- `dist/JARVIS_Control_Center/START_JARVIS.bat`

> Note: PyInstaller also produces `dist/JARVIS_AI_Agent.exe` as the build output before packaging the release folder.

### ▶️ Run Directly (Python)
```bash
python jarvis_app.py
```

---

## 🌟 Features

- ⚡ **Wake-on-LAN via ESP32**: Turn on your PC remotely when you're away from home.
- 🎙️ **Voice & Text Automation**: Send voice notes or text messages from your phone via Telegram.
- 🧠 **OpenRouter AI Intelligence**: Uses models like **Claude 3.5 Sonnet**, **GPT-4o**, or **DeepSeek R1/V3** to understand your requests and execute multi-step tools.
- 🖥️ **Desktop App Execution**: Open VS Code, Chrome, Word, Excel, Spotify, Command Prompt, etc.
- 📁 **File & Code Management**: Search, read, edit files, clone/pull Git repos, run build scripts.
- 📄 **Assignment & Document Generator**: Automatically generate formatted Word `.docx` documents & reports on your PC while you travel back home.
- 🌐 **Web Browsing & Search**: Search latest news, summarize articles, download files.
- 📸 **Live Desktop Screenshot & Telemetry**: Monitor desktop live and check CPU/RAM/Battery status.
- 🔒 **Tailscale Mesh Security**: Zero open ports required; all PC-to-Mobile-to-ESP32 traffic is securely encrypted.
- 🔊 **Voice Feedback**: J.A.R.V.I.S. speaks confirmation when every task completes ("Welcome sir, I opened calculator").
- � **Mute / Unmute Voice Feedback**: Toggle spoken confirmations from the desktop control center or via the shared system tools.
- 🔉 **Windows Volume Control**: Set system/master volume and application volume with the new Windows audio integration (requires `pycaw` and `comtypes`).
- 🖱️ **Graphical Control Center**: Standalone Windows EXE with live ESP32 status, agent monitoring, emergency stop, and the new mute button.

---

## 🚀 Quickstart & Setup Guide

### 1️⃣ Clone & Configure Environment
1. Copy `.env.template` to `.env`:
    ```bash
    cp .env.template .env
    ```
2. Edit `.env` and fill in your credentials:
    - **`OPENROUTER_API_KEY`**: Get key from [OpenRouter.ai](https://openrouter.ai/keys).
    - **`TELEGRAM_BOT_TOKEN`**: Create a bot in Telegram by messaging `@BotFather`.
    - **`ALLOWED_TELEGRAM_USERS`**: Message `@userinfobot` on Telegram to get your numeric User ID.
    - **`BOT_PASSWORD`**: Set a password to secure your bot (default: `jarvis123`).
    - **`ESP32_IP`**: Your ESP32's local or Tailscale IP address.

> 🔐 Important: Do not commit `.env` or any file containing secret keys or passwords. Only `.env.template` should be stored in source control.

---

### 2️⃣ ESP32 Hardware Setup (Wake-on-LAN Node)
1. Open `esp32_firmware/ESP32_server.ino` in Arduino IDE.
2. Install the ESP32 board support package in Arduino IDE:
   - Open **Tools > Board > Boards Manager**
   - Search for `esp32` and install the package by Espressif Systems
3. Update your home Wi-Fi credentials in the sketch:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID"; // 2.4GHz only
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
4. Select the correct ESP32 board (for example `ESP32 Dev Module`) and COM port.
5. Upload `ESP32_server.ino` to the board.
6. Open the Serial Monitor at `115200` baud to confirm the ESP32 connects and prints its IP address.
7. Keep the ESP32 powered near your router.

If you prefer PlatformIO, you can upload the same sketch from `esp32_firmware/ESP32_server.ino` after installing ESP32 support.

---

### 3️⃣ PC Agent Setup (Python)
1. Install Python dependencies:
    ```bash
    pip install -r pc_agent/requirements.txt
    ```
2. Start the J.A.R.V.I.S PC Agent:
    ```bash
    python pc_agent/main.py
    ```

---

### 4️⃣ Autostart on Windows Boot (Optional)
To make your PC Agent start automatically whenever your PC wakes up or turns on:
1. Press `Win + R`, type `shell:startup`, and press Enter.
2. Create a shortcut to run:
    ```cmd
    pythonw.exe C:\Users\HP\OneDrive\Desktop\Esp32 automation\pc_agent\main.py
    ```

---

## 🖥️ Standalone EXE Build (Control Center)

Build a single-click Windows desktop application with live monitoring and emergency stop.

### Prerequisites
```bash
pip install pyinstaller
```

### Build the EXE
```bash
python build_exe.py
```

### 🚀 Launch the EXE
After building, open the folder and double-click the launcher:

**[📂 Open EXE Folder](dist/JARVIS_Control_Center/)**

> **Note**: If GitHub blocks folder links, navigate manually to `dist/JARVIS_Control_Center/` in this repo.

Inside that folder:
- **`START_JARVIS.bat`** — One-click launcher (recommended)
- **`JARVIS_Control_Center.exe`** — The standalone GUI

### First-Run Setup
1. Edit `.env` inside the EXE folder with your credentials:
   - `TELEGRAM_BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
   - `OPENROUTER_API_KEY` — from [OpenRouter.ai](https://openrouter.ai/keys)
   - `ESP32_IP` — your ESP32 local/Tailscale IP
   - `BOT_PASSWORD` — password to secure Telegram access (default: `jarvis123`)
   - `WINDOWS_PC_PASSWORD` — optional, for remote lockscreen unlock
   - `DEFAULT_WORKSPACE` — default folder for file operations (leave blank to auto-detect your Desktop folder, e.g. `C:\Users\HP\OneDrive\Desktop`)
   - `ALLOWED_TELEGRAM_USERS` — your numeric Telegram User ID
2. Run `START_JARVIS.bat` as Administrator.
3. In the GUI, click **▶ START AGENT**.

---

## 💬 Example Commands You Can Give J.A.R.V.I.S

| Command Type | Example Voice/Text Prompt |
|--------------|---------------------------|
| **Wake PC** | Send `/wake` to your Telegram Bot (ESP32 sends Magic Packet) |
| **Development** | *"Open VS Code and pull the latest code from my project repository."* |
| **Assignments** | *"Create a formatted Word document assignment about IoT and Cloud Automation."* |
| **Research** | *"Search the web for latest AI news today and save a summary on my Desktop."* |
| **Control** | *"Take a screenshot of my PC screen"* or *"Lock my PC."* |
| **Status** | Send `/status` to check CPU, RAM, and Disk space. |

---

## 🔐 Security Features

- **Bot Password**: All Telegram bot access is locked behind a password. Use `/login <password>` to authenticate.
- **Emergency Stop**: The EXE Control Center has a red **EMERGENCY STOP** button that instantly kills the agent and shuts down the Telegram bot.
- **PC Unlock**: After Wake-on-LAN, use `/unlock <windows_password>` to remotely unlock your PC lockscreen.
- **Allowed Users**: Restrict bot access to specific Telegram User IDs in `.env`.

## 🛡️ Security Contact

For security issues or responsible disclosure, contact:

- **Maintainer:** `Thilankalhara`
- **Email:** `thilankalhara8@gmail.com`
- **GitHub:** https://github.com/Thilankalhara

Please do not post secrets or passwords in issue threads. Use the above contact channels for vulnerability reports.

---

## 🎨 Web Command Center
Open `web_dashboard/index.html` in any browser (or host it over Tailscale) for a futuristic J.A.R.V.I.S HUD interface!

---

## 📁 Project Structure

```
Esp32 automation - Copy/
├── esp32_firmware/          # ESP32 Arduino/PlatformIO code
│   └── src/
│       └── main.cpp
├── pc_agent/                # Python backend agent
│   ├── main.py              # Entry point
│   ├── telegram_bot.py      # Telegram bot handlers
│   ├── agent.py             # OpenRouter AI agent
│   ├── config.py            # Environment config
│   ├── requirements.txt     # Python dependencies
│   ├── tools/               # Tool implementations
│   │   ├── system_tools.py
│   │   ├── file_tools.py
│   │   ├── web_tools.py
│   │   ├── dev_tools.py
│   │   └── doc_tools.py
│   ├── screenshots/         # Screenshot storage
│   └── documents/           # Generated documents
├── web_dashboard/           # Futuristic web HUD
│   ├── index.html
│   ├── style.css
│   └── app.js
├── jarvis_app.py            # Standalone GUI (tkinter)
├── jarvis_exe.spec          # PyInstaller spec for EXE build
├── build_exe.py             # EXE builder script
├── .env.template            # Configuration template
└── README.md
```

---

## 🛠️ Troubleshooting

- **EXE won't start**: Right-click and select "Run as Administrator". Some Windows security policies block unsigned executables.
- **Telegram bot not responding**: Verify your `TELEGRAM_BOT_TOKEN` in `.env` and check internet connectivity.
- **ESP32 not reachable**: Ensure ESP32 and PC are on the same network, and `ESP32_IP` in `.env` is correct.
- **Voice not working**: Ensure Windows Text-to-Speech voices are installed (Settings > Time & Language > Speech).
- **Volume commands fail**: Install the Windows audio dependencies with `pip install pycaw comtypes`.
- **Wake-on-LAN not working**: Enable Wake-on-LAN in BIOS/UEFI and ensure the PC's MAC address is correctly set in `esp32_firmware/src/main.cpp`.

---

## 📝 License
MIT License - Feel free to modify and use this project for personal automation!

---

<div align="center">

**Built with ❤️ | J.A.R.V.I.S. Control Center v2.1**

[📦 Run EXE](dist/JARVIS_Control_Center/JARVIS_Control_Center.exe) · [🚀 Quick Launcher](dist/JARVIS_Control_Center/START_JARVIS.bat) · [⚙️ Configure](.env.template)

</div>
