import os
import sys
import time
import threading
from pathlib import Path

# Ensure pc_agent is on python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pc_agent.config as pcc
from pc_agent.telegram_bot import run_telegram_bot

import traceback

def _write_crash_log(exc: Exception):
    """Write a crash log next to the project root when startup fails."""
    try:
        project_root = pcc.project_root if hasattr(pcc, 'project_root') else Path(__file__).resolve().parent.parent
        log_path = Path(project_root) / "crash_log.txt"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"JARVIS Crash Log — {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=f)
    except Exception:
        pass

def print_banner():
    banner = r"""
    ===============================================================
               ____.  _____ .______  ____   ____.___ _____ 
              |    | /  _  \|   _  \ \   \ /   /|   |/ ____|
              |    |/  /_\  \|  |_)  | \   Y   / |   |  __   
          /\__|    /    |    \  | \  /  \     /  |   |\___ \  
          \________\____|__  /__|  \_\   \___/   |___|____  > 
                           \/                             \/  
                   REMOTE PC AUTOMATION AGENT (v1.0)
    ===============================================================
    """
    print(banner)
    pcc.reload_config()
    print(f"[*] OpenRouter Model Target : Configured", flush=True)
    print(f"[*] Telegram Bot Interface  : {'READY' if pcc.TELEGRAM_BOT_TOKEN else 'MISSING TOKEN'}", flush=True)
    print(f"[*] ESP32 Node Address     : http://{pcc.ESP32_IP}", flush=True)
    print("---------------------------------------------------------------", flush=True)

def main():
    print_banner()

    pcc.reload_config()
    if not pcc.get_openrouter_api_key():
        print("[!] WARNING: OPENROUTER_API_KEY is not set in `.env`!")
        print("[!] Please set your OpenRouter API key to enable AI automation features.")

    if not pcc.get_telegram_bot_token():
        print("[!] WARNING: TELEGRAM_BOT_TOKEN is not set in `.env`!")
        print("[!] Please create a Telegram bot via @BotFather and paste the token in `.env`.")

    print("\n[+] Starting J.A.R.V.I.S Agent Daemon...", flush=True)
    try:
        run_telegram_bot()
    except Exception as exc:
        # Save crash log and print helpful guidance
        _write_crash_log(exc)
        print('\n[!] Fatal error while starting the Telegram agent:')
        print(f'    {type(exc).__name__}: {exc}')
        print('\n[!] A crash_log.txt was written to the project root with the traceback.')
        print('[!] Common fixes:')
        print('    - Ensure python-telegram-bot and its dependencies are installed (pip install -r pc_agent/requirements.txt)')
        print('    - Remove any local files named telegram.py or folders named telegram that could shadow the library')
        print('    - Clear __pycache__ folders: find . -name "__pycache__" -type d -exec rm -r {} +')
        print('    - Reinstall python-telegram-bot: python -m pip install --upgrade --force-reinstall python-telegram-bot')
        sys.exit(1)

if __name__ == "__main__":
    main()
