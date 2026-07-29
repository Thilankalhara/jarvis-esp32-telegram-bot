import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def _find_project_root() -> Path:
    """Find project root: prefer executable folder, then current working dir, then source tree."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

project_root = _find_project_root()
env_path = project_root / ".env"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def _auto_detect_workspace() -> str:
    desktop_paths = [
        project_root / ".." / "Desktop",
        Path.home() / "OneDrive" / "Desktop",
        Path.home() / "Desktop",
    ]
    for path in desktop_paths:
        resolved = path.expanduser().resolve()
        if resolved.exists() and resolved.is_dir():
            return str(resolved)
    return str(project_root)


def reload_config():
    """Reload all environment variables dynamically from .env file."""
    global OPENROUTER_API_KEY, OPENROUTER_MODEL, TELEGRAM_BOT_TOKEN, OPENROUTER_BASE_URL
    global ALLOWED_TELEGRAM_USERS, ESP32_IP, BOT_PASSWORD, USER_NAME
    global WINDOWS_PC_PASSWORD, DEFAULT_WORKSPACE
    
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001").strip()
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    
    raw_users = os.getenv("ALLOWED_TELEGRAM_USERS", "").strip()
    ALLOWED_TELEGRAM_USERS = [
        int(uid.strip()) for uid in raw_users.split(",") if uid.strip().isdigit()
    ]
    
    ESP32_IP = os.getenv("ESP32_IP", "192.168.1.150").strip()
    BOT_PASSWORD = os.getenv("BOT_PASSWORD", "jarvis123").strip()
    USER_NAME = os.getenv("USER_NAME", "Sir").strip()
    WINDOWS_PC_PASSWORD = os.getenv("WINDOWS_PC_PASSWORD", "").strip()
    
    _env_workspace = os.getenv("DEFAULT_WORKSPACE", "").strip()
    DEFAULT_WORKSPACE = _env_workspace if _env_workspace else _auto_detect_workspace()

# Initial load
reload_config()

def get_user_name() -> str:
    reload_config()
    return USER_NAME if USER_NAME and USER_NAME.strip() else "Sir"

# Screenshots directory
SCREENSHOTS_DIR = project_root / "pc_agent" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

DOCUMENTS_DIR = project_root / "pc_agent" / "documents"
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
