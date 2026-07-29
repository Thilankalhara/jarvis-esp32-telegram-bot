import os
import sys
import subprocess
import time
import json
import socket
import concurrent.futures
import psutil
import pyautogui
from pathlib import Path
from pc_agent.config import SCREENSHOTS_DIR


def speak_voice_feedback(text: str):
    """Use Windows Text-to-Speech engine to speak feedback out loud on PC speakers."""
    if not text:
        return
    try:
        clean_text = text.replace('"', '').replace("'", '').replace('`', '')
        if sys.platform == "win32":
            ps_cmd = f'Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak("{clean_text}");'
            subprocess.Popen(["powershell", "-Command", ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        print(f"[TTS Error] {str(e)}")


def _get_name():
    try:
        from pc_agent.config import get_user_name
        return get_user_name()
    except Exception:
        return "Sir"

_feedback_map = {
    "open_application": lambda app_name, **__ : f"Opened {app_name} for you, {_get_name()}.",
    "take_screenshot": lambda **__ : f"Screenshot captured successfully, {_get_name()}.",
    "get_system_info": lambda **__ : f"System status report ready, {_get_name()}.",
    "power_control": lambda action, **__ : f"Power command executed: {action}, {_get_name()}.",
    "list_directory": lambda **__ : f"Directory listing completed, {_get_name()}.",
    "read_file_content": lambda **__ : f"File read completed, {_get_name()}.",
    "write_file_content": lambda file_path, **__ : f"File written to {file_path} successfully, {_get_name()}.",
    "search_files": lambda query, **__ : f"Search for {query} completed, {_get_name()}.",
    "execute_terminal_command": lambda command, **__ : f"Terminal command executed: {command}, {_get_name()}.",
    "git_operation": lambda action, **__ : f"Git {action} completed, {_get_name()}.",
    "search_web": lambda query, **__ : f"Web search for {query} completed, {_get_name()}.",
    "download_file": lambda url, **__ : f"File downloaded from {url} successfully, {_get_name()}.",
    "create_word_document": lambda title, **__ : f"Document {title} created successfully, {_get_name()}.",
}


def announce_tool_completion(tool_name: str, *args, **kwargs):
    """Trigger voice feedback for a completed tool action."""
    announcer = _feedback_map.get(tool_name)
    if announcer:
        try:
            msg = announcer(*args, **kwargs)
            speak_voice_feedback(msg)
        except Exception:
            pass


def auto_discover_esp32_ip() -> str:
    """Scan local network subnets to auto-detect ESP32 device IP address."""
    subnets = set()
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                parts = ip.split(".")
                if len(parts) == 4:
                    subnets.add(f"{parts[0]}.{parts[1]}.{parts[2]}")
    except Exception:
        pass

    if not subnets:
        subnets.add("192.168.43")
        subnets.add("192.168.1")

    def _check(ip):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.25)
            res = s.connect_ex((ip, 80))
            s.close()
            if res == 0:
                import requests
                r = requests.get(f"http://{ip}/", timeout=1.0)
                if "ESP32" in r.text or r.status_code == 200:
                    return ip
        except Exception:
            pass
        return None

    candidates = []
    for sub in subnets:
        candidates.extend([f"{sub}.{i}" for i in range(1, 255)])

    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
        found_ips = [ip for ip in executor.map(_check, candidates) if ip]

    if found_ips:
        return found_ips[0]
    return ""


def open_application(app_name: str) -> str:
    """Launch ANY desktop application by name or executable path on Windows."""
    app_clean = app_name.strip()
    app_lower = app_clean.lower()

    if not app_clean:
        return "Please specify an application name."

    if sys.platform == "win32":
        # Normalize some common typos before trying launchers
        alias_map = {
            'calculater': 'calculator',
            'calulator': 'calculator',
            'calclater': 'calculator',
            'calclatr': 'calculator',
            'claculator': 'calculator',
            'calander': 'calendar',
            'calender': 'calendar',
        }
        app_lower = alias_map.get(app_lower, app_lower)

        # 1. Direct Windows protocol / standard executable handlers
        direct_launchers = {
            "calculator": lambda: os.startfile("calculator:"),
            "calc": lambda: os.startfile("calculator:"),
            "notepad": lambda: os.startfile("notepad.exe"),
            "settings": lambda: os.startfile("ms-settings:"),
            "camera": lambda: os.startfile("microsoft.windows.camera:"),
            "snipping tool": lambda: os.startfile("snippingtool.exe"),
            "snippingtool": lambda: os.startfile("snippingtool.exe"),
            "paint": lambda: os.startfile("mspaint.exe"),
            "cmd": lambda: subprocess.Popen(["cmd.exe", "/c", "start", "cmd.exe"]),
            "command prompt": lambda: subprocess.Popen(["cmd.exe", "/c", "start", "cmd.exe"]),
            "powershell": lambda: subprocess.Popen(["powershell.exe"]),
            "explorer": lambda: subprocess.Popen(["explorer.exe"]),
            "file explorer": lambda: subprocess.Popen(["explorer.exe"]),
            "task manager": lambda: os.startfile("taskmgr.exe"),
            "taskmgr": lambda: os.startfile("taskmgr.exe"),
            "chrome": lambda: _launch_exe("chrome.exe", "chrome"),
            "google chrome": lambda: _launch_exe("chrome.exe", "chrome"),
            "edge": lambda: os.startfile("msedge:"),
            "msedge": lambda: os.startfile("msedge:"),
            "spotify": lambda: _launch_spotify(),
            "vscode": lambda: _launch_exe("code.cmd", "code"),
            "vs code": lambda: _launch_exe("code.cmd", "code"),
            "visual studio code": lambda: _launch_exe("code.cmd", "code"),
            "word": lambda: _launch_exe("winword.exe", "winword"),
            "excel": lambda: _launch_exe("excel.exe", "excel"),
            "powerpoint": lambda: _launch_exe("powerpnt.exe", "powerpnt"),
        }

        def _launch_exe(exe_name, shell_cmd):
            try:
                os.startfile(exe_name)
            except Exception:
                subprocess.Popen(f'start "" "{shell_cmd}"', shell=True)

        def _launch_spotify():
            try:
                os.startfile("spotify:")
            except Exception:
                _launch_exe("spotify.exe", "spotify")

        for key, launcher in direct_launchers.items():
            if key == app_lower or (len(key) > 3 and key in app_lower):
                try:
                    launcher()
                    announce_tool_completion("open_application", app_clean)
                    return f"Successfully opened '{app_clean}'!"
                except Exception:
                    pass

        # 2. Direct os.startfile attempt for target name or name.exe
        for candidate in [app_clean, f"{app_clean}.exe"]:
            try:
                os.startfile(candidate)
                announce_tool_completion("open_application", app_clean)
                return f"Successfully launched '{app_clean}'!"
            except Exception:
                pass

        # 3. Search ALL installed apps via PowerShell Get-StartApps
        try:
            ps_cmd = "Get-StartApps | ConvertTo-Json"
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=6,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    data = [data]

                matched_app = None
                for a in data:
                    name = a.get("Name", "")
                    if name.lower() == app_lower:
                        matched_app = a
                        break

                if not matched_app:
                    for a in data:
                        name = a.get("Name", "")
                        if app_lower in name.lower() or name.lower() in app_lower:
                            matched_app = a
                            break

                if matched_app:
                    app_id = matched_app.get("AppID", "")
                    try:
                        os.startfile(f"shell:AppsFolder\\{app_id}")
                        announce_tool_completion("open_application", app_clean)
                        return f"Successfully opened '{matched_app.get('Name')}'!"
                    except Exception:
                        pass
        except Exception:
            pass

        # 4. Search Windows Registry App Paths
        try:
            import winreg
            reg_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths",
            ]
            for hkey in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                for reg_path in reg_paths:
                    try:
                        key = winreg.OpenKey(hkey, reg_path)
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            sub = winreg.EnumKey(key, i)
                            if app_lower in sub.lower():
                                sub_key = winreg.OpenKey(key, sub)
                                exe_path = winreg.QueryValue(sub_key, None)
                                if exe_path and os.path.exists(exe_path):
                                    os.startfile(exe_path)
                                    announce_tool_completion("open_application", app_clean)
                                    return f"Successfully opened '{app_clean}' from registry!"
                    except Exception:
                        pass
        except Exception:
            pass

        # 5. Search Start Menu shortcut (.lnk) files
        start_menu_paths = [
            Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        ]
        for base_path in start_menu_paths:
            if base_path.exists():
                for lnk in base_path.glob("**/*.lnk"):
                    if app_lower in lnk.stem.lower():
                        try:
                            os.startfile(str(lnk))
                            announce_tool_completion("open_application", app_clean)
                            return f"Successfully opened shortcut '{lnk.name}'!"
                        except Exception:
                            pass

        # 6. Shell start command fallback
        try:
            subprocess.Popen(f'start "" "{app_clean}"', shell=True)
            announce_tool_completion("open_application", app_clean)
            return f"Launched '{app_clean}' via shell!"
        except Exception as e:
            return f"Could not open application '{app_clean}': {str(e)}"
    else:
        try:
            subprocess.Popen([app_clean])
            announce_tool_completion("open_application", app_clean)
            return f"Successfully opened application '{app_clean}'"
        except Exception as e:
            return f"Error opening application '{app_clean}': {str(e)}"


def take_screenshot() -> str:
    """Take a screenshot of the current desktop and save it to disk."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    file_path = SCREENSHOTS_DIR / f"screenshot_{timestamp}.png"

    try:
        import mss
        with mss.mss() as sct:
            sct.shot(output=str(file_path))
        if file_path.exists() and file_path.stat().st_size > 0:
            announce_tool_completion("take_screenshot")
            return str(file_path)
    except Exception:
        pass

    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(all_screens=True)
        img.save(file_path)
        if file_path.exists() and file_path.stat().st_size > 0:
            announce_tool_completion("take_screenshot")
            return str(file_path)
    except Exception:
        pass

    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(file_path)
        if file_path.exists() and file_path.stat().st_size > 0:
            announce_tool_completion("take_screenshot")
            return str(file_path)
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"

    return "Error: Failed to capture screenshot with all engines."


def get_system_info() -> dict:
    """Get system health metrics (CPU, RAM, Disk, Battery)."""
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('C:\\' if sys.platform == 'win32' else '/')
        battery = psutil.sensors_battery()

        info = {
            "cpu_usage_percent": cpu_usage,
            "ram_total_gb": round(memory.total / (1024**3), 2),
            "ram_used_gb": round(memory.used / (1024**3), 2),
            "ram_usage_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_usage_percent": disk.percent,
            "battery_percent": battery.percent if battery else "N/A (Desktop/AC)",
            "power_plugged": battery.power_plugged if battery else True
        }
        announce_tool_completion("get_system_info")
        return info
    except Exception as e:
        return {"error": str(e)}


def power_control(action: str) -> str:
    """Perform system power actions: 'lock', 'sleep', 'shutdown', 'restart'."""
    action = action.lower().strip()
    try:
        if sys.platform == "win32":
            if action == "lock":
                subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
                announce_tool_completion("power_control", action)
                return "PC has been locked."
            elif action == "sleep":
                subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
                announce_tool_completion("power_control", action)
                return "PC put to sleep."
            elif action == "shutdown":
                subprocess.run("shutdown /s /t 10", shell=True)
                announce_tool_completion("power_control", action)
                return "PC is shutting down in 10 seconds."
            elif action == "restart":
                subprocess.run("shutdown /r /t 10", shell=True)
                announce_tool_completion("power_control", action)
                return "PC is restarting in 10 seconds."
            else:
                return f"Unknown power action: {action}. Use 'lock', 'sleep', 'shutdown', or 'restart'."
        else:
            return "Power control supported on Windows."
    except Exception as e:
        return f"Error executing power action '{action}': {str(e)}"


def set_application_volume(app_identifier: str, percent: int) -> str:
    """Set volume for an application by process name or partial display name (Windows).

    Requires `pycaw` package. `app_identifier` may be a process name like 'msedge.exe'
    or a substring of the session display name (e.g., 'Edge', 'Spotify').
    Percent is 0-100.
    """
    try:
        if sys.platform != 'win32':
            return "Per-application volume control is supported only on Windows."

        try:
            from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
            import comtypes
        except Exception:
            return "Missing dependency: install 'pycaw' (pip install pycaw comtypes) to control app volumes."

        try:
            percent = int(percent)
            if percent < 0 or percent > 100:
                return "Volume percent must be between 0 and 100."
        except Exception:
            return "Invalid percent value. Provide an integer 0-100."

        sessions = AudioUtilities.GetAllSessions()
        lowered = app_identifier.lower()
        matched = []
        for session in sessions:
            proc = session.Process
            name = ''
            try:
                if proc:
                    name = proc.name()
            except Exception:
                name = ''
            display = (session.DisplayName or '')
            if (proc and lowered in name.lower()) or (display and lowered in display.lower()):
                matched.append((session, proc, name, display))

        if not matched:
            return f"No audio session matched '{app_identifier}'. Try process name (e.g. msedge.exe) or a distinct app title."

        for session, proc, name, display in matched:
            try:
                volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                volume.SetMasterVolume(percent / 100.0, None)
            except Exception:
                return f"Failed to set volume for session '{name or display}'. Ensure pycaw is usable."

        return f"Set volume for {len(matched)} session(s) matching '{app_identifier}' to {percent}%"
    except Exception as e:
        return f"Error setting application volume: {str(e)}"


def set_system_volume(percent: int) -> str:
    """Set the system (master) volume to a percent (0-100) on Windows using pycaw."""
    try:
        if sys.platform != 'win32':
            return "System volume control is supported only on Windows."

        try:
            from ctypes import POINTER, cast
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        except Exception:
            return "Missing dependency: install 'pycaw' and 'comtypes' (pip install pycaw comtypes)."

        try:
            devices = AudioUtilities.GetSpeakers()
            volume = devices.EndpointVolume
            val = float(percent) / 100.0
            if val < 0.0 or val > 1.0:
                return "Volume percent must be between 0 and 100."
            volume.SetMasterVolumeLevelScalar(val, None)
            return f"System volume set to {percent}%"
        except Exception as e:
            return f"Failed to set system volume: {str(e)}"
    except Exception as e:
        return f"Error setting system volume: {str(e)}"


def set_brightness(percent: int) -> str:
    """Set display brightness to percent (0-100) on Windows via WMI/PowerShell."""
    try:
        if sys.platform != 'win32':
            return "Brightness control is supported only on Windows."

        try:
            p = int(percent)
            if p < 0 or p > 100:
                return "Brightness percent must be between 0 and 100."
        except Exception:
            return "Invalid percent value. Provide an integer 0-100."

        # Use PowerShell WMI call to set brightness
        ps_cmd = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{p})"
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        if r.returncode == 0:
            return f"Brightness set to {p}%"
        else:
            return f"Failed to set brightness (PowerShell error): {r.stderr.strip() or r.stdout.strip()}"
    except Exception as e:
        return f"Error setting brightness: {str(e)}"
