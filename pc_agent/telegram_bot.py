import os
import re
import json
import asyncio
import logging
import threading
import requests
import subprocess
import time
from pathlib import Path
from weakref import WeakKeyDictionary
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import pc_agent.config as pcc
from pc_agent.agent import JarvisAgent
from pc_agent.tools import system_tools

project_root = pcc.project_root
_APP_STOP_EVENTS: WeakKeyDictionary = WeakKeyDictionary()

# Pending close choices per chat: { chat_id: { 'choices': [ {id,name,title,cmd}, ... ], 'expires': ts } }
PENDING_CLOSE = {}

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("JarvisTelegramBot")

jarvis = JarvisAgent()

# ── Persistent authentication ─────────────────────────────────────────────────
_AUTH_FILE = project_root / "authenticated_chats.json"

def _load_auth() -> set:
    """Load saved authenticated chat IDs from disk."""
    try:
        pcc.reload_config()
        current_hash = pcc.get_bot_password_hash()
        if _AUTH_FILE.exists():
            data = json.loads(_AUTH_FILE.read_text(encoding="utf-8"))
            saved_hash = data.get("password_hash", "")
            if not saved_hash or saved_hash != current_hash:
                logger.info("Bot password changed or auth metadata missing; clearing persisted Telegram auth sessions.")
                _save_auth(set(), password_hash=current_hash)
                return set()
            return set(data.get("chats", []))
    except Exception:
        pass
    return set()


def _refresh_auth_state() -> set:
    """Refresh in-memory auth state from disk and invalidate when the password hash changes."""
    global authenticated_chats
    authenticated_chats = _load_auth()
    return authenticated_chats


def _save_auth(chats: set, password_hash: str | None = None):
    """Persist authenticated chat IDs to disk."""
    try:
        if password_hash is None:
            password_hash = pcc.get_bot_password_hash()
        _AUTH_FILE.write_text(
            json.dumps({"password_hash": password_hash, "chats": list(chats)}, indent=2),
            encoding="utf-8"
        )
    except Exception as e:
        logger.warning(f"Could not save auth file: {e}")


def invalidate_auth_sessions() -> None:
    """Forcefully clear current authenticated chat sessions."""
    global authenticated_chats
    authenticated_chats = set()
    _save_auth(authenticated_chats, password_hash=pcc.get_bot_password_hash())

# Load on module startup
authenticated_chats: set = _load_auth()

def is_authenticated(chat_id: int) -> bool:
    """Check if the Telegram chat session is unlocked with password."""
    _refresh_auth_state()
    return chat_id in authenticated_chats

async def prompt_password(update: Update):
    """Ask user to enter the security password."""
    msg = (
        "🔒 *J.A.R.V.I.S PC Control Locked*\n\n"
        "Please enter your security password to access and control your PC from this account:\n"
        "• Reply directly with your password\n"
        "• Or use `/login <password>`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /login <password> command."""
    chat_id = update.effective_chat.id
    
    # Reload environment variable dynamically
    pcc.reload_config()
    current_password = pcc.BOT_PASSWORD

    # Check if password passed in args or text
    input_pass = ""
    if context.args:
        input_pass = " ".join(context.args).strip()
    elif update.message.text:
        input_pass = update.message.text.strip()
        
    user_name = pcc.get_user_name()
    if input_pass == current_password or input_pass == f"/login {current_password}":
        authenticated_chats.add(chat_id)
        _save_auth(authenticated_chats, password_hash=pcc.get_bot_password_hash())
        msg = (
            "🔓 *ACCESS GRANTED!*\n\n"
            f"Welcome back, {user_name}. Your account is now authenticated.\n"
            "You have full AI remote control over your PC.\n\n"
            "Try sending voice messages, `/status`, `/screenshot`, or text commands like *'Open VS Code'*!"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ *Incorrect Password!* Please try again.", parse_mode="Markdown")

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lock session for current chat."""
    chat_id = update.effective_chat.id
    if chat_id in authenticated_chats:
        authenticated_chats.remove(chat_id)
        _save_auth(authenticated_chats)
    await update.message.reply_text("🔒 *Session Locked.* Use `/login <password>` or send your password to regain access.", parse_mode="Markdown")


async def reload_config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reload .env configuration and invalidate stale auth if needed."""
    chat_id = update.effective_chat.id
    if not is_authenticated(chat_id):
        await prompt_password(update)
        return

    old_api_key = pcc.OPENROUTER_API_KEY
    old_token = pcc.TELEGRAM_BOT_TOKEN
    old_password_hash = pcc.get_bot_password_hash()

    pcc.reload_config()

    new_api_key = pcc.get_openrouter_api_key()
    new_token = pcc.get_telegram_bot_token()
    new_password_hash = pcc.get_bot_password_hash()

    messages = []
    if old_password_hash != new_password_hash:
        invalidate_auth_sessions()
        messages.append("🔐 Bot password changed. All authenticated sessions were invalidated. Please `/login <new_password>`.")
    else:
        messages.append("✅ Bot password is unchanged.")

    if old_api_key != new_api_key:
        messages.append("🔑 OpenRouter API key updated and will be used for new AI requests.")
    else:
        messages.append("✅ OpenRouter API key is unchanged.")

    if old_token != new_token:
        messages.append(
            "🚨 Telegram token changed. This bot process must be restarted to use the new token. "
            "If you are using the GUI, reopen the agent or restart the application."
        )
    else:
        messages.append("✅ Telegram bot token is unchanged.")

    await update.message.reply_text("\n".join(messages), parse_mode="Markdown")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not is_authenticated(chat_id):
        await prompt_password(update)
        return
        
    user_name = pcc.get_user_name()
    msg = (
        "🤖 *J.A.R.V.I.S Remote PC Assistant Online*\n\n"
        f"Welcome back, {user_name}. I am listening for text and voice commands.\n\n"
        "*Quick Commands:*\n"
        "• `/status` - Check PC & ESP32 Health\n"
        "• `/screenshot` - Capture current PC desktop\n"
        "• `/wake` - Trigger ESP32 Wake-on-LAN\n"
        "• `/logout` - Lock session\n\n"
        "_Example Prompts:_\n"
        "• \"Open VS Code and pull my latest project\"\n"
        "• \"Create a Word document assignment on Quantum Computing\"\n"
        "• \"Search the web for latest AI news and summarize it\""
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def open_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /open <app> confirm command for explicit app launches."""
    if not is_authenticated(update.effective_chat.id):
        await prompt_password(update)
        return

    args = context.args or []
    if not args:
        await update.message.reply_text(
            "⚠️ Please specify the app name and confirm with `/open <app> confirm`, for example `/open calculator confirm`.",
            parse_mode="Markdown"
        )
        return

    confirm = False
    if args[-1].lower() == "confirm":
        confirm = True
        app_name = " ".join(args[:-1]).strip()
    else:
        app_name = " ".join(args).strip()

    if not app_name:
        await update.message.reply_text(
            "⚠️ Please specify the app name before confirming, for example `/open calculator confirm`.",
            parse_mode="Markdown"
        )
        return

    if not confirm:
        await update.message.reply_text(
            "⚠️ I will not open or launch applications automatically.\n"
            "If you really want to open an app, use `/open <app> confirm` to confirm the action.",
            parse_mode="Markdown"
        )
        return

    # Normalize common typos for calculator, calendar, and similar app names
    alias_map = {
        'calculater': 'calculator',
        'calulator': 'calculator',
        'calclater': 'calculator',
        'calclatr': 'calculator',
        'claculator': 'calculator',
        'calander': 'calendar',
        'calender': 'calendar',
    }
    normalized_app = alias_map.get(app_name.lower(), app_name)
    result = system_tools.open_application(normalized_app)
    await update.message.reply_text(result)


def _normalize_open_target(target: str) -> str:
    """Normalize common app name typos parsed from open/launch commands."""
    target_clean = target.strip().lower()
    target_clean = target_clean.replace(' please', '').replace(' the ', ' ').strip()
    alias_map = {
        'calculater': 'calculator',
        'calulator': 'calculator',
        'calclater': 'calculator',
        'calclatr': 'calculator',
        'claculator': 'calculator',
        'calander': 'calendar',
        'calender': 'calendar',
    }
    return alias_map.get(target_clean, target_clean)


def _extract_open_target(user_text: str) -> str | None:
    """Extract the app name from a natural open/launch/start/run command."""
    import re
    text = user_text.strip().lower()
    # Remove polite prefixes so the open verb can be matched anywhere
    text = re.sub(r"^(?:please|kindly|hey|hi|hi jarvis|jarvis|could you|can you|would you|please could you|please can you)\s+", "", text)

    # Find the first explicit open/launch/start/run request
    m = re.search(r"\b(?:open|launch|start|run)\b\s+(.+?)(?:\s+(?:please|now|thanks|thank you|for me|if possible))?$", text)
    if not m:
        m = re.search(r"\b(?:open|launch|start|run)\b\s+(.+?)(?:[?.!]|$)", text)
        if not m:
            return None

    target = m.group(1).strip()
    target = re.sub(r"\b(?:please|now|thanks|thank you|for me|if possible)\b.*$", "", target).strip()
    target = re.split(r"\s+(?:and|then|with|to|for)\s+", target)[0].strip()
    if target.startswith('the '):
        target = target[4:]
    return target

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authenticated(update.effective_chat.id):
        await prompt_password(update)
        return
        
    sys_info = system_tools.get_system_info()
    text = (
        "📊 *PC System Status*\n"
        f"• *CPU Usage:* {sys_info.get('cpu_usage_percent', 'N/A')}%\n"
        f"• *RAM Used:* {sys_info.get('ram_used_gb', 'N/A')} / {sys_info.get('ram_total_gb', 'N/A')} GB ({sys_info.get('ram_usage_percent', 'N/A')}%)\n"
        f"• *Disk Free:* {sys_info.get('disk_free_gb', 'N/A')} / {sys_info.get('disk_total_gb', 'N/A')} GB\n"
        f"• *Power/Battery:* {sys_info.get('battery_percent', 'AC Power')}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List interactive GUI processes (PID, ProcessName, MainWindowTitle)."""
    if not is_authenticated(update.effective_chat.id):
        await prompt_password(update)
        return

    await update.message.reply_text("🔎 Gathering interactive processes...")
    try:
        ps_cmd = (
            "Get-Process | Where-Object { $_.MainWindowTitle } | Select-Object Id,ProcessName,MainWindowTitle | ConvertTo-Json -Compress"
        )
        p = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=6)
        out = p.stdout.strip()
        if not out:
            await update.message.reply_text("No interactive GUI processes found.")
            return
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        lines = ["Interactive processes (PID — Name — Title):"]
        for item in data[:20]:
            pid = item.get('Id')
            name = item.get('ProcessName') or item.get('Process') or ''
            title = item.get('MainWindowTitle') or ''
            lines.append(f"• PID `{pid}` — {name} — {title}")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except Exception as e:
        logger.exception('Error listing interactive processes')
        await update.message.reply_text(f"❌ Error listing processes: {type(e).__name__}")


async def close_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Close multiple GUI applications.

    Usage:
    - `/closeall` -> lists interactive GUI apps and instructs how to confirm
    - `/closeall confirm` -> force-close all listed GUI apps (EXCLUDES core system processes)
    - `/closeall <pattern>` -> close GUI apps whose name/title matches `<pattern>`
    """
    if not is_authenticated(update.effective_chat.id):
        await prompt_password(update)
        return

    args = context.args or []
    # Exclude dangerous/system-critical processes by image name
    exclude_images = {"explorer", "winlogon", "csrss", "svchost", "dwm", "shellexperiencehost", "searchui", "sihost", "taskhostw"}

    # Gather interactive GUI processes
    try:
        ps_cmd = (
            "Get-Process | Where-Object { $_.MainWindowTitle } | Select-Object Id,ProcessName,MainWindowTitle,Path | ConvertTo-Json -Compress"
        )
        p = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=8)
        out = p.stdout.strip()
        procs = []
        if out:
            data = json.loads(out)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                pid = int(item.get('Id') or 0)
                name = (item.get('ProcessName') or '').lower()
                title = item.get('MainWindowTitle') or ''
                procs.append({'id': pid, 'name': name, 'title': title})
    except Exception:
        await update.message.reply_text("❌ Failed to enumerate GUI processes.")
        return

    if not args:
        lines = ["Interactive GUI processes (safe listing):"]
        for pinfo in procs[:50]:
            lines.append(f"• PID `{pinfo['id']}` — {pinfo['name']} — {pinfo['title'] or '<no title>'}")
        lines.append("\nTo force-close all listed GUI apps, send `/closeall confirm`. To close only matching apps: `/closeall <pattern>`.")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return

    # If user asked to confirm, close all (except excluded images)
    param = args[0].strip().lower()
    if param == 'confirm':
        killed = []
        failed = []
        for pinfo in procs:
            if pinfo['name'] in exclude_images:
                continue
            pid = pinfo['id']
            try:
                r = subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, text=True)
                if r.returncode == 0:
                    killed.append(pid)
                else:
                    failed.append((pid, r.stderr.strip()))
            except Exception as e:
                failed.append((pid, str(type(e).__name__)))
        msg = ''
        if killed:
            # Build friendly info for killed processes
            killed_info = []
            for pinfo in procs:
                if pinfo['id'] in killed:
                    name = pinfo.get('name') or '<unknown>'
                    title = pinfo.get('title') or ''
                    killed_info.append(f"{pinfo['id']} ({name}{': ' + title if title else ''})")
            msg += f"✅ Closed: {', '.join(killed_info)}.\n"
            try:
                spoken = ', '.join([p.get('name') or 'unknown' for p in procs if p.get('id') in killed])
                if spoken:
                    system_tools.speak_voice_feedback(f"Closed {spoken} successfully.")
            except Exception:
                pass
        if failed:
            msg += f"⚠️ Failed to close: {failed}.\n"
        await update.message.reply_text(msg or "⚠️ No GUI apps were closed.")
        return

    # Otherwise treat param as pattern and close matching GUI processes
    pattern = param
    matches = [pinfo for pinfo in procs if pattern in (pinfo['name'] or '') or pattern in (pinfo['title'] or '').lower()]
    if not matches:
        await update.message.reply_text(f"⚠️ No GUI processes matched `{pattern}`.", parse_mode="Markdown")
        return

    killed = []
    failed = []
    for pinfo in matches:
        if pinfo['name'] in exclude_images:
            continue
        pid = pinfo['id']
        try:
            r = subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, text=True)
            if r.returncode == 0:
                killed.append(pid)
            else:
                failed.append((pid, r.stderr.strip()))
        except Exception as e:
            failed.append((pid, str(type(e).__name__)))

    msg = ''
    if killed:
        killed_info = []
        for p in matches:
            if p['id'] in killed:
                name = p.get('name') or '<unknown>'
                title = p.get('title') or ''
                killed_info.append(f"{p['id']} ({name}{': ' + title if title else ''})")
        msg += f"✅ Closed: {', '.join(killed_info)}.\n"
        try:
            spoken = ', '.join([p.get('name') or 'unknown' for p in matches if p.get('id') in killed])
            if spoken:
                system_tools.speak_voice_feedback(f"Closed {spoken} successfully.")
        except Exception:
            pass
    if failed:
        msg += f"⚠️ Failed to close: {failed}.\n"
    await update.message.reply_text(msg or f"⚠️ No processes were closed for pattern `{pattern}`.", parse_mode="Markdown")

async def screenshot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authenticated(update.effective_chat.id):
        await prompt_password(update)
        return
        
    user_name = pcc.get_user_name()
    await update.message.reply_text("📸 Capturing screenshot...")
    path = system_tools.take_screenshot()
    if os.path.exists(path):
        with open(path, "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=f"Here is your live PC desktop view, {user_name}.")
    else:
        await update.message.reply_text(f"❌ Failed to take screenshot: {path}")

async def wake_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authenticated(update.effective_chat.id):
        await prompt_password(update)
        return

    esp_ip = getattr(pcc, "ESP32_IP", "") or "192.168.43.13"
    await update.message.reply_text(f"📡 Contacting ESP32 hardware node at `{esp_ip}`...", parse_mode="Markdown")

    try:
        url = f"http://{esp_ip}/wake"
        res = requests.get(url, timeout=4)
        if res.status_code == 200:
            msg = (
                "⚡ *Wake-on-LAN Magic Packet broadcasted via ESP32 successfully!*\n\n"
                "Your PC should now be powering on. If it has a Windows login password, "
                "send `/unlock <pc_password>` to automatically type the password and unlock your lockscreen."
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
            # Speak greeting on wake so the user hears the PC is awake
            try:
                user_name = pcc.get_user_name()
                system_tools.speak_voice_feedback(f"Hello {user_name}, I am awake.")
                # Also schedule a delayed retry in case audio subsystem isn't ready yet
                def _delayed_speak(name=user_name):
                    try:
                        time.sleep(12)
                        system_tools.speak_voice_feedback(f"Hello {name}, I am awake.")
                    except Exception:
                        pass
                t = threading.Thread(target=_delayed_speak, daemon=True)
                t.start()
            except Exception:
                pass
            return
    except Exception:
        pass

    # Fallback: probe root http://{esp_ip}/
    try:
        url = f"http://{esp_ip}/"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            msg = (
                "⚡ *Connected to ESP32 Hardware Node!*\n"
                f"Status: Online (`{esp_ip}`)"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
            return
    except Exception:
        pass

    # Auto-scan local network
    await update.message.reply_text("🔍 Searching local Wi-Fi network for ESP32...")
    found_ip = system_tools.auto_discover_esp32_ip()
    if found_ip:
        pcc.ESP32_IP = found_ip
        # Update .env
        env_file = project_root / ".env"
        if env_file.exists():
            content = env_file.read_text(encoding="utf-8")
            import re
            content = re.sub(r"^ESP32_IP=.*$", f"ESP32_IP={found_ip}", content, flags=re.MULTILINE)
            env_file.write_text(content, encoding="utf-8")

        await update.message.reply_text(f"✅ *ESP32 Auto-Detected at `{found_ip}`!*", parse_mode="Markdown")
    else:
        await update.message.reply_text(
            f"❌ Could not reach ESP32 at `{esp_ip}` and auto-scan did not find it.\n"
            "Ensure ESP32 is powered on and connected to the same Wi-Fi network.",
            parse_mode="Markdown"
        )


async def set_volume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set per-application volume: /set_volume <app_name|process> <percent>"""
    if not is_authenticated(update.effective_chat.id):
        await prompt_password(update)
        return

    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("Usage: /set_volume <app_name_or_process> <0-100>")
        return

    app_ident = args[0]
    try:
        percent = int(args[1])
    except Exception:
        await update.message.reply_text("Volume percent must be an integer between 0 and 100.")
        return

    await update.message.reply_text(f"🔉 Setting volume for '{app_ident}' to {percent}%...")
    try:
        res = system_tools.set_application_volume(app_ident, percent)
        if "Missing dependency" in res:
            res += "\nInstall: `pip install pycaw comtypes`"
        await update.message.reply_text(res)
        if res.startswith("Set volume for"):
            system_tools.speak_voice_feedback(f"Volume for {app_ident} set to {percent} percent.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {type(e).__name__}")


async def set_master_volume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set system master volume: /set_master_volume <percent>"""
    if not is_authenticated(update.effective_chat.id):
        await prompt_password(update)
        return

    args = context.args or []
    if len(args) < 1:
        await update.message.reply_text("Usage: /set_master_volume <0-100>")
        return

    try:
        percent = int(args[0])
    except Exception:
        await update.message.reply_text("Volume percent must be an integer between 0 and 100.")
        return

    await update.message.reply_text(f"🔊 Setting system volume to {percent}%...")
    try:
        res = system_tools.set_system_volume(percent)
        if "Missing dependency" in res:
            res += "\nInstall: `pip install pycaw comtypes`"
        await update.message.reply_text(res)
        if res.startswith("System volume set"):
            system_tools.speak_voice_feedback(f"System volume set to {percent} percent.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {type(e).__name__}")


async def set_brightness_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set display brightness: /set_brightness <percent>"""
    if not is_authenticated(update.effective_chat.id):
        await prompt_password(update)
        return

    args = context.args or []
    if len(args) < 1:
        await update.message.reply_text("Usage: /set_brightness <0-100>")
        return

    try:
        percent = int(args[0])
    except Exception:
        await update.message.reply_text("Brightness percent must be an integer between 0 and 100.")
        return

    await update.message.reply_text(f"☀️ Setting brightness to {percent}%...")
    try:
        res = system_tools.set_brightness(percent)
        await update.message.reply_text(res)
        if res.startswith("Brightness set to"):
            system_tools.speak_voice_feedback(f"Brightness set to {percent} percent.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {type(e).__name__}")


async def hibernate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hibernate the PC. Usage: /hibernate confirm"""
    chat_id = update.effective_chat.id
    if not is_authenticated(chat_id):
        await prompt_password(update)
        return

    args = context.args or []
    if not args or args[0].strip().lower() != 'confirm':
        await update.message.reply_text("⚠️ This will hibernate the PC. To proceed, send `/hibernate confirm`.", parse_mode="Markdown")
        return

    await update.message.reply_text("✅ Hibernating PC.")
    try:
        # Speak the same text so auditory and chat outputs match
        system_tools.speak_voice_feedback("Hibernating PC")
    except Exception:
        pass
    # Execute the hibernate action (non-blocking)
    try:
        system_tools.power_control('hibernate')
    except Exception as e:
        logger.exception('Failed to hibernate')
        await update.message.reply_text(f"❌ Failed to hibernate: {type(e).__name__}")

async def unlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remotely type Windows login password to unlock lockscreen after Wake-on-LAN."""
    if not is_authenticated(update.effective_chat.id):
        await prompt_password(update)
        return
    # Diagnostics + safer logging around automated keypresses
    pcc.reload_config()
    pc_pass = ""
    if context.args:
        pc_pass = " ".join(context.args).strip()
    else:
        pc_pass = getattr(pcc, "WINDOWS_PC_PASSWORD", "").strip()

    if not pc_pass:
        await update.message.reply_text(
            "⚠️ Please specify password: `/unlock <your_windows_password>` or set `WINDOWS_PC_PASSWORD` in `.env`.",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text("🔑 Attempting to wake screen and type Windows password...", parse_mode="Markdown")

    # Check pyautogui availability
    try:
        import pyautogui
    except Exception as e:
        await update.message.reply_text(
            "❌ `pyautogui` is not available in this Python environment. Install it (pip install pyautogui) and restart the agent.")
        return

    # Important note: Windows prevents synthetic input from reaching the secure logon desktop
    # in many configurations. If this fails, the most likely causes are:
    # - The agent is running in a different session (not the interactive user session)
    # - Windows blocks synthetic input on the secure desktop for security reasons
    # - The process lacks the required desktop/session context

    try:
        # Try a simple sequence: press Enter to open password field, type password, press Enter
        pyautogui.press('enter')
        pyautogui.sleep(0.8)
        pyautogui.press('enter')
        pyautogui.sleep(0.4)
        pyautogui.typewrite(pc_pass, interval=0.05)
        pyautogui.press('enter')

        user_name = pcc.get_user_name()
        system_tools.speak_voice_feedback(f"Welcome back {user_name}, PC unlock attempted.")
        await update.message.reply_text(f"🔓 Unlock sequence sent. If the desktop did not unlock, see diagnostics below.")
        await update.message.reply_text(
            "If unlock failed: ensure the agent is running as the interactive user (not a service), `pyautogui` is installed, and `WINDOWS_PC_PASSWORD` is correct.")
    except Exception as e:
        # Provide full diagnostic feedback to the user (no secrets)
        await update.message.reply_text(
            f"❌ Failed to send keypresses (exception: {type(e).__name__}).\n"
            "Common causes: running in non-interactive session, Windows secure desktop blocking synthetic input, or missing permissions."
        )
        try:
            import traceback
            tb = traceback.format_exc()
            logger.error("Unlock command failed: %s", tb)
        except Exception:
            pass


async def close_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Close an application by process name or PID. Usage: /close <process_name|pid>"""
    chat_id = update.effective_chat.id
    if not is_authenticated(chat_id):
        await prompt_password(update)
        return

    if not context.args:
        await update.message.reply_text("Usage: /close <process_name|pid> (e.g. /close notepad or /close 1234)")
        return

    raw_target = " ".join(context.args).strip()
    # Normalize target: remove angle brackets, surrounding punctuation, and collapse whitespace
    import re
    target = re.sub(r"^[<\[\(\s]+|[>\]\)\s]+$", "", raw_target)
    # Remove any non-alphanumeric (keep spaces) for matching convenience
    target = re.sub(r"[^0-9A-Za-z \-_.]", "", target).strip()
    logger.info("close_command invoked by chat %s with args=%s", update.effective_chat.id, context.args)
    try:
        # If numeric, treat as PID
        if target.isdigit():
            pid = int(target)
            # Try to get process name/title before killing so we can report a friendly name
            proc_name = None
            proc_title = None
            try:
                ps_cmd = f"Get-Process -Id {pid} | Select-Object ProcessName,MainWindowTitle | ConvertTo-Json -Compress"
                pinfo = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, timeout=5)
                if pinfo.stdout:
                    try:
                        infoj = json.loads(pinfo.stdout)
                        if isinstance(infoj, dict):
                            proc_name = infoj.get('ProcessName')
                            proc_title = infoj.get('MainWindowTitle')
                    except Exception:
                        pass
            except Exception:
                proc_name = None
                proc_title = None

            res = subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, text=True)
            if res.returncode == 0:
                display = proc_name or str(pid)
                title_part = f": {proc_title}" if proc_title else ""
                await update.message.reply_text(f"✅ Closed PID `{pid}` ({display}{title_part}) successfully.", parse_mode="Markdown")
                try:
                    system_tools.speak_voice_feedback(f"Closed {display} successfully.")
                except Exception:
                    pass
                return

        # Try image-name kill first (add .exe if missing)
        proc_name = target
        if not proc_name.lower().endswith('.exe'):
            proc_name_exe = proc_name + '.exe'
        else:
            proc_name_exe = proc_name

        res = subprocess.run(["taskkill", "/IM", proc_name_exe, "/F"], capture_output=True, text=True)
        if res.returncode == 0:
            await update.message.reply_text(f"✅ Closed `{proc_name_exe}` successfully.", parse_mode="Markdown")
            system_tools.speak_voice_feedback(f"Closed {proc_name_exe} successfully.")
            return

        # Collect running processes (Name, Id, MainWindowTitle, CommandLine) via PowerShell
        try:
            ps_procs_cmd = (
                "$p = Get-Process | Select-Object Id,ProcessName,MainWindowTitle;"
                "$c = Get-CimInstance Win32_Process | Select-Object ProcessId,Name,CommandLine;"
                "$out = foreach($proc in $p){$cmd = ($c | Where-Object { $_.ProcessId -eq $proc.Id }).CommandLine; [PSCustomObject]@{Id=$proc.Id;Name=$proc.ProcessName;MainWindowTitle=$proc.MainWindowTitle;CommandLine=$cmd}};"
                "$out | ConvertTo-Json -Compress"
            )
            try:
                p = subprocess.run(["powershell", "-NoProfile", "-Command", ps_procs_cmd], capture_output=True, text=True, timeout=20)
            except subprocess.TimeoutExpired:
                logger.warning("Process search timed out, retrying with a smaller Get-Process query")
                ps_procs_cmd = (
                    "Get-Process | Select-Object Id,ProcessName,MainWindowTitle | ConvertTo-Json -Compress"
                )
                p = subprocess.run(["powershell", "-NoProfile", "-Command", ps_procs_cmd], capture_output=True, text=True, timeout=10)

            procs_json = p.stdout.strip()
            import json, difflib
            candidates = []
            if procs_json:
                data = json.loads(procs_json)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = (item.get('Name') or '')
                    mid = int(item.get('Id') or 0)
                    title = item.get('MainWindowTitle') or ''
                    cmdline = item.get('CommandLine') or ''
                    candidates.append({'id': mid, 'name': name, 'title': title, 'cmd': cmdline})

            # Lightweight alias/misspelling map for common apps (helps when user types e.g. 'calander')
            alias_map = {
                'calculater': 'calculator',
                'calulator': 'calculator',
                'calander': 'calendar',
                'calender': 'calendar',
                'calendar': 'calendar',
                'calclater': 'calculator',
                'calclatr': 'calculator',
                'claculator': 'calculator',
                'calclater': 'calculator',
                'notepad++': 'notepad++',
                'chrome': 'chrome',
                'msedge': 'msedge',
                'edge': 'msedge',
                'spotify': 'spotify',
            }
            target_lower = (target or '').lower()
            mapped = alias_map.get(target_lower)
            if mapped:
                logger.info("Mapping alias '%s' -> '%s'", target_lower, mapped)
                target_lower = mapped
            matches = []
            for c in candidates:
                if target_lower in (c['name'] or '').lower() or target_lower in (c['title'] or '').lower() or target_lower in (c['cmd'] or '').lower():
                    matches.append(c)

            # If any direct substring match appears in a window title, try to close those PIDs immediately
            title_matches = [c for c in matches if (c.get('title') or '').strip() and target_lower in (c.get('title') or '').lower()]
            if title_matches:
                killed = []
                killed_info = []
                failed = []
                for c in title_matches:
                    pid = c.get('id')
                    try:
                        r = subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, text=True)
                        name = c.get('name') or '<unknown>'
                        title = c.get('title') or ''
                        if r.returncode == 0:
                            killed.append(pid)
                            killed_info.append(f"{pid} ({name}{': ' + title if title else ''})")
                        else:
                            failed.append((pid, r.stderr.strip()))
                    except Exception as e:
                        failed.append((pid, str(type(e).__name__)))
                msg = ''
                if killed_info:
                    # Report friendly names instead of raw PID list
                    msg += f"✅ Closed by window-title match: {', '.join(killed_info)}.\n"
                    try:
                        spoken = ', '.join([f"{c.get('name') or 'unknown'}" for c in title_matches if c.get('id') in killed])
                        if spoken:
                            system_tools.speak_voice_feedback(f"Closed {spoken} successfully.")
                        else:
                            system_tools.speak_voice_feedback(f"Closed {len(killed)} processes successfully.")
                    except Exception:
                        system_tools.speak_voice_feedback(f"Closed {len(killed)} processes successfully.")
                if failed:
                    msg += f"⚠️ Failed to close: {failed}.\n"
                await update.message.reply_text(msg or f"⚠️ Could not close processes matching window title '{target}'.")
                return

            # Aggressive fallback for UWP-hosted apps: ApplicationFrameHost hosts many UWP apps (Calendar, Calculator)
            try:
                # Search for ApplicationFrameHost instances whose window title matches
                ps_appfh = (
                    "Get-Process ApplicationFrameHost | Where-Object { $_.MainWindowTitle -and $_.MainWindowTitle -match '" + target + "' } | Select-Object Id,ProcessName,MainWindowTitle | ConvertTo-Json -Compress"
                )
                pf = subprocess.run(["powershell", "-NoProfile", "-Command", ps_appfh], capture_output=True, text=True, timeout=5)
                out = pf.stdout.strip()
                if out:
                    try:
                        j = json.loads(out)
                        if isinstance(j, dict):
                            j = [j]
                        killed = []
                        failed = []
                        for item in j:
                            pid = int(item.get('Id') or 0)
                            try:
                                r = subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, text=True)
                                if r.returncode == 0:
                                    killed.append(pid)
                                else:
                                    failed.append((pid, r.stderr.strip()))
                            except Exception as e:
                                failed.append((pid, str(type(e).__name__)))
                        if killed:
                            await update.message.reply_text(f"✅ Closed UWP host ApplicationFrameHost PIDs: {killed}.")
                            system_tools.speak_voice_feedback(f"Closed UWP host processes successfully.")
                            return
                        if failed:
                            await update.message.reply_text(f"⚠️ Attempted ApplicationFrameHost close but failed: {failed}.")
                            return
                    except Exception:
                        pass
            except Exception:
                pass

                # If no direct substring matches, compute fuzzy suggestions to present to user
                scores = []
                for c in candidates:
                    combined = ' '.join([c['name'] or '', c['title'] or '', c['cmd'] or ''])
                    score = difflib.SequenceMatcher(None, target_lower, combined.lower()).ratio()
                    scores.append((score, c))
                scores.sort(key=lambda x: x[0], reverse=True)

                # If top fuzzy match is very confident, attempt to auto-close it (convenience for UWP-hosted apps)
                if scores and scores[0][0] >= 0.65:
                    best_score, best_candidate = scores[0]
                    pid = best_candidate.get('id')
                    try:
                        r = subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, text=True)
                        if r.returncode == 0:
                            name = best_candidate.get('name') or str(pid)
                            await update.message.reply_text(f"✅ Closed PID `{pid}` (`{best_candidate.get('name')}`) — fuzzy score {best_score:.2f}", parse_mode="Markdown")
                            try:
                                system_tools.speak_voice_feedback(f"Closed {name} successfully.")
                            except Exception:
                                pass
                            return
                        else:
                            await update.message.reply_text(f"⚠️ Attempted to close PID `{pid}` but failed: {r.stderr.strip()}", parse_mode="Markdown")
                            return
                    except Exception as e:
                        logger.exception('Auto-kill of best fuzzy candidate failed')
                        await update.message.reply_text(f"❌ Error while attempting to close PID `{pid}`: {type(e).__name__}")
                        return

                # Otherwise present up to 6 suggestions and require explicit PID confirmation for safety
                suggestions = [(s[0], s[1]) for s in scores if s[0] >= 0.35][:6]
                if not suggestions:
                    await update.message.reply_text(f"⚠️ No running process matched `{target}`. Try `/list` to see running apps or use the exact process name/PID.", parse_mode="Markdown")
                    return

                # Present numbered candidates and store them for selection via a single number
                msg_lines = [f"Found candidate processes matching '{target}':\nReply with the number to select, or `/close <PID>` to terminate directly."]
                numbered = []
                for i, (score, c) in enumerate(suggestions, start=1):
                    msg_lines.append(f"{i}. PID `{c['id']}` — {c['name']} — Title: {c['title'] or '<no title>'} — score {score:.2f}")
                    numbered.append(c)

                # store pending choices for this chat for 60 seconds
                try:
                    PENDING_CLOSE[update.effective_chat.id] = {'choices': numbered, 'expires': time.time() + 60}
                except Exception:
                    pass

                await update.message.reply_text("\n".join(msg_lines), parse_mode="Markdown")
                return
        except Exception as e:
            logger.exception('Error while attempting to list candidates for close')
            await update.message.reply_text(f"❌ Error while searching for processes: {type(e).__name__}")
            return
    except Exception as e:
        await update.message.reply_text(f"❌ Error closing `{target}`: {type(e).__name__}", parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_text = (update.message.text or "").strip()
    
    # Reload environment variable dynamically
    pcc.reload_config()
    current_password = pcc.BOT_PASSWORD

    # If not authenticated, check if message is the password
    if not is_authenticated(chat_id):
        if user_text == current_password:
            await login_command(update, context)
        else:
            await prompt_password(update)
        return

    # If user has pending numbered choices, accept a single-number reply to select
    try:
        if user_text.strip().isdigit():
            idx = int(user_text.strip())
            pending = PENDING_CLOSE.get(chat_id)
            if pending:
                if time.time() > pending.get('expires', 0):
                    PENDING_CLOSE.pop(chat_id, None)
                    await update.message.reply_text("⏳ Selection expired. Please run the close command again.")
                    return
                choices = pending.get('choices', [])
                if 1 <= idx <= len(choices):
                    sel = choices[idx-1]
                    context.args = [str(sel.get('id'))]
                    PENDING_CLOSE.pop(chat_id, None)
                    await close_command(update, context)
                    return
    except Exception:
        pass

    # Intercept close/kill/terminate intents anywhere in the sentence to avoid Jarvis opening apps
    import re
    # Match phrases like: "close calendar", "please close the calendar", "can you kill spotify"
    m = re.search(r"\b(?:close|kill|terminate)\b\s+(.*)", user_text, re.IGNORECASE)
    if m:
        target = (m.group(1) or "").strip()
        if target:
            logger.info("Intercepted close intent: %s", user_text)
            context.args = [target]
            await close_command(update, context)
            return
        else:
            await update.message.reply_text("⚠️ Which application would you like to close? Reply with the app name or PID.")
            return

    # Intercept volume and brightness text commands
    # Support natural phrases like "please set volume to 30", "adjust brightness 50", "volume 30" and "set the screen brightness to 70"
    master_vol_match = re.search(r"\b(?:set|change|adjust)?\s*(?:the\s+)?(?:master\s+)?(?:volume|vol)\s*(?:to|at|=)?\s*(\d{1,3})\b", user_text, re.IGNORECASE)
    brightness_match = re.search(r"\b(?:set|change|adjust)?\s*(?:the\s+)?(?:screen\s+|display\s+)?(?:brightness|bright|bridgeness)\s*(?:to|at|=)?\s*(\d{1,3})\b", user_text, re.IGNORECASE)
    app_vol_match = re.search(r"\b(?:set|change|adjust)?\s*volume\s+for\s+(.+?)\s*(?:to|at|=)?\s*(\d{1,3})\b", user_text, re.IGNORECASE)
    app_vol_match2 = re.search(r"\b(?:set|change|adjust)?\s*(.+?)\s+volume\s*(?:to|at|=)?\s*(\d{1,3})\b", user_text, re.IGNORECASE)
    if master_vol_match:
        context.args = [master_vol_match.group(1)]
        await set_master_volume_command(update, context)
        return

    # Intercept wake phrases: allow natural-language like "wake up", "get alive", "turn on the pc"
    wake_match = re.search(r"\b(?:wake(?:\s*up)?|get\s+alive|bring\s+me\s+alive|turn\s+on\b)\b", user_text, re.IGNORECASE)
    if wake_match:
        logger.info("Intercepted wake intent: %s", user_text)
        context.args = []
        await wake_command(update, context)
        return
    if brightness_match:
        context.args = [brightness_match.group(1)]
        await set_brightness_command(update, context)
        return
    if app_vol_match:
        context.args = [app_vol_match.group(1).strip(), app_vol_match.group(2)]
        await set_volume_command(update, context)
        return
    if app_vol_match2 and not re.search(r"\b(?:set|change|adjust)?\s*(?:the\s+)?(?:master\s+)?(?:volume|vol)\b", user_text, re.IGNORECASE):
        context.args = [app_vol_match2.group(1).strip(), app_vol_match2.group(2)]
        await set_volume_command(update, context)
        return

    # Guard: process explicit open/launch commands from authenticated users
    open_target = _extract_open_target(user_text)
    if open_target:
        if not is_authenticated(chat_id):
            await update.message.reply_text(
                "⚠️ I will not open or launch applications automatically unless you are authenticated. "
                "Please login first with `/login <password>`."
            )
            return

        target_norm = _normalize_open_target(open_target)
        result = system_tools.open_application(target_norm)
        await update.message.reply_text(result)
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Process through Jarvis OpenRouter AI Agent
    result = jarvis.process_command(user_text, allow_open=False)

    # Send Text Response
    if result.get("text"):
        await update.message.reply_text(result["text"])
        
    # Send Media Attachment (Photo or Document) if tool generated one
    media = result.get("media")
    if media and os.path.exists(media["path"]):
        if media["type"] == "photo":
            with open(media["path"], "rb") as f:
                await update.message.reply_photo(photo=f)
        elif media["type"] == "document":
            with open(media["path"], "rb") as f:
                await update.message.reply_document(document=f, caption="📄 Generated Document")

def _convert_audio_to_wav(audio_path: Path) -> Path | None:
    """Convert Telegram-style audio to WAV so SpeechRecognition can process it."""
    if audio_path.suffix.lower() == ".wav":
        return audio_path

    try:
        from imageio_ffmpeg import get_ffmpeg_exe

        ffmpeg_path = get_ffmpeg_exe()
        if not ffmpeg_path:
            return None

        wav_path = audio_path.with_suffix(".wav")
        subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-i",
                str(audio_path),
                "-vn",
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                str(wav_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return wav_path
    except Exception as exc:
        logger.warning("Could not convert audio to WAV: %s", exc)
        return None


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authenticated(update.effective_chat.id):
        await prompt_password(update)
        return
    await update.message.reply_text("🎙️ Voice command received! Processing audio...")
    voice_file = await update.message.voice.get_file()
    # Download to temp path
    tmp_dir = project_root / "tmp_audio"
    try:
        tmp_dir.mkdir(exist_ok=True)
    except Exception:
        pass
    tmp_path = tmp_dir / f"voice_{int(time.time())}.ogg"
    try:
        await voice_file.download_to_drive(custom_path=str(tmp_path))
    except Exception:
        await update.message.reply_text("❌ Failed to download audio file.")
        return

    transcribed = None
    try:
        import speech_recognition as sr
        wav_path = _convert_audio_to_wav(tmp_path)
        if not wav_path or not wav_path.exists():
            raise RuntimeError("Could not create a WAV file for transcription")

        r = sr.Recognizer()
        with sr.AudioFile(str(wav_path)) as source:
            audio = r.record(source)

        try:
            transcribed = r.recognize_google(audio)
        except Exception:
            try:
                transcribed = r.recognize_sphinx(audio)
            except Exception as exc:
                logger.warning("SpeechRecognition transcription failed: %s", exc)
                transcribed = None

        if wav_path != tmp_path:
            try:
                wav_path.unlink(missing_ok=True)
            except Exception:
                pass
    except Exception as exc:
        logger.warning("SpeechRecognition path failed: %s", exc)
        transcribed = None

    # Clean up file
    try:
        tmp_path.unlink()
    except Exception:
        pass

    if not transcribed:
        await update.message.reply_text(
            "⚠️ Could not transcribe voice message. Please send text or enable a transcription library (whisper or SpeechRecognition)."
        )
        return

    await update.message.reply_text(f"📝 Transcribed: {transcribed}")

    # Reuse text handling: set user_text and follow same interception rules
    user_text = transcribed.strip()
    # If user replied with a single number and a pending close exists, handle it
    try:
        if user_text.isdigit():
            idx = int(user_text)
            pending = PENDING_CLOSE.get(update.effective_chat.id)
            if pending and time.time() <= pending.get('expires', 0):
                choices = pending.get('choices', [])
                if 1 <= idx <= len(choices):
                    sel = choices[idx-1]
                    context.args = [str(sel.get('id'))]
                    PENDING_CLOSE.pop(update.effective_chat.id, None)
                    await close_command(update, context)
                    return
    except Exception:
        pass

    # Intercept close intent in transcribed text (match anywhere in sentence)
    import re
    m = re.search(r"\b(?:close|kill|terminate)\b\s+(.*)", user_text, re.IGNORECASE)
    if m:
        target = (m.group(1) or "").strip()
        if target:
            context.args = [target]
            await close_command(update, context)
            return
        else:
            await update.message.reply_text("⚠️ Which application would you like to close? Reply with the app name or PID.")
            return

    # Intercept volume and brightness voice commands via transcribed text
    master_vol_match = re.search(r"\b(?:set|change|adjust)?\s*(?:the\s+)?(?:master\s+)?(?:volume|vol)\s*(?:to|at|=)?\s*(\d{1,3})\b", user_text, re.IGNORECASE)
    brightness_match = re.search(r"\b(?:set|change|adjust)?\s*(?:the\s+)?(?:screen\s+|display\s+)?(?:brightness|bright|bridgeness)\s*(?:to|at|=)?\s*(\d{1,3})\b", user_text, re.IGNORECASE)
    app_vol_match = re.search(r"\b(?:set|change|adjust)?\s*volume\s+for\s+(.+?)\s*(?:to|at|=)?\s*(\d{1,3})\b", user_text, re.IGNORECASE)
    app_vol_match2 = re.search(r"\b(?:set|change|adjust)?\s*(.+?)\s+volume\s*(?:to|at|=)?\s*(\d{1,3})\b", user_text, re.IGNORECASE)
    if master_vol_match:
        context.args = [master_vol_match.group(1)]
        await set_master_volume_command(update, context)
        return

    # Intercept wake phrases in transcribed voice
    wake_match = re.search(r"\b(?:wake(?:\s*up)?|get\s+alive|bring\s+me\s+alive|turn\s+on)\b", user_text, re.IGNORECASE)
    if wake_match:
        context.args = []
        await wake_command(update, context)
        return
    if brightness_match:
        context.args = [brightness_match.group(1)]
        await set_brightness_command(update, context)
        return
    if app_vol_match:
        context.args = [app_vol_match.group(1).strip(), app_vol_match.group(2)]
        await set_volume_command(update, context)
        return
    if app_vol_match2 and not re.search(r"\b(?:set|change|adjust)?\s*(?:the\s+)?(?:master\s+)?(?:volume|vol)\b", user_text, re.IGNORECASE):
        context.args = [app_vol_match2.group(1).strip(), app_vol_match2.group(2)]
        await set_volume_command(update, context)
        return

    # Guard: process explicit open/launch commands from authenticated users if possible
    open_target = _extract_open_target(user_text)
    if open_target:
        if not is_authenticated(update.effective_chat.id):
            await update.message.reply_text(
                "⚠️ I will not open or launch applications automatically unless you are authenticated. "
                "Please login first with `/login <password>`."
            )
            return

        open_target = _normalize_open_target(open_target)
        result = system_tools.open_application(open_target)
        await update.message.reply_text(result)
        return

    # Fallback: process via Jarvis
    await update.message.reply_text("🗣️ Processing intent via J.A.R.V.I.S...")
    result = jarvis.process_command(user_text, allow_open=False)
    await update.message.reply_text(result.get("text", "(no response)"))

def run_telegram_bot():
    token = pcc.get_telegram_bot_token()
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("⚠️ Telegram Bot Token is missing! Please set TELEGRAM_BOT_TOKEN in .env file.")
        return

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CommandHandler("logout", logout_command))
    app.add_handler(CommandHandler("reloadconfig", reload_config_command))
    app.add_handler(CommandHandler("reload_config", reload_config_command))
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("open", open_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("screenshot", screenshot_command))
    app.add_handler(CommandHandler("closeall", close_all_command))
    app.add_handler(CommandHandler("wake", wake_command))
    app.add_handler(CommandHandler("unlock", unlock_command))
    app.add_handler(CommandHandler("close", close_command))
    app.add_handler(CommandHandler("hibernate", hibernate_command))
    app.add_handler(CommandHandler("set_volume", set_volume_command))
    app.add_handler(CommandHandler("set_master_volume", set_master_volume_command))
    app.add_handler(CommandHandler("set_brightness", set_brightness_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("[J.A.R.V.I.S Telegram Bot] Listening for remote commands (Password Auth Enabled)...", flush=True)
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_bot_async(app))
    except Exception as e:
        print(f"[J.A.R.V.I.S Telegram Bot] Error: {e}", flush=True)
    finally:
        clear_stop_event(app)
        try:
            loop.close()
        except Exception:
            pass


def get_application():
    """Create and return the Telegram bot application instance (for GUI integration)."""
    token = pcc.get_telegram_bot_token()
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        return None
    return Application.builder().token(token).build()


def setup_bot_handlers(app):
    """Register all command and message handlers on the application."""
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CommandHandler("logout", logout_command))
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("open", open_command))
    app.add_handler(CommandHandler("screenshot", screenshot_command))
    app.add_handler(CommandHandler("wake", wake_command))
    app.add_handler(CommandHandler("unlock", unlock_command))
    app.add_handler(CommandHandler("close", close_command))
    app.add_handler(CommandHandler("hibernate", hibernate_command))
    app.add_handler(CommandHandler("set_volume", set_volume_command))
    app.add_handler(CommandHandler("set_master_volume", set_master_volume_command))
    app.add_handler(CommandHandler("set_brightness", set_brightness_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))


def run_telegram_bot_threaded(app, stop_event: threading.Event = None):
    """Run the Telegram bot in a thread (used by GUI).
    
    python-telegram-bot v20+ is fully async; a fresh event loop must be
    created in the thread because tkinter daemon threads have none.
    """
    import asyncio
    print("[J.A.R.V.I.S Telegram Bot] Listening for remote commands in background thread...", flush=True)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_run_bot_async(app))
    except Exception as e:
        print(f"[J.A.R.V.I.S Telegram Bot] Error: {e}", flush=True)
    finally:
        try:
            loop.close()
        except Exception:
            pass


async def _run_bot_async(app):
    """Initialise, start polling, then cleanly shut down."""
    import asyncio
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    print("[J.A.R.V.I.S Telegram Bot] Polling started — bot is online.", flush=True)
    stop_event = asyncio.Event()
    try:
        _APP_STOP_EVENTS[app] = stop_event
    except Exception:
        pass
    try:
        await stop_event.wait()
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        try:
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
        except Exception:
            pass


def get_stop_event(app):
    return _APP_STOP_EVENTS.get(app)


def clear_stop_event(app):
    try:
        _APP_STOP_EVENTS.pop(app, None)
    except Exception:
        pass
