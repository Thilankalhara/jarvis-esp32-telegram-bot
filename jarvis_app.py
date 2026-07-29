import os
import sys
import time
import subprocess
import threading
import asyncio
import traceback
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

def _get_app_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

# ── Crash logger (writes traceback next to EXE if startup fails) ─────────────
def _write_crash_log(exc: Exception):
    try:
        log_path = _get_app_dir() / "crash_log.txt"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"JARVIS Crash Log — {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=f)
        try:
            import tkinter.messagebox as mb
            mb.showerror("J.A.R.V.I.S. Startup Error",
                         f"Fatal error on startup:\n\n{exc}\n\nSee crash_log.txt for details.")
        except Exception:
            pass
    except Exception:
        pass


# Ensure project dir is in path
sys.path.insert(0, str(_get_app_dir()))

# Ensure user site-packages are available when running from source
if not getattr(sys, 'frozen', False):
    import site as _site
    _user_site = _site.getusersitepackages()
    if _user_site not in sys.path:
        sys.path.insert(1, _user_site)

# Guard imports that may fail at startup (write crash log & show messagebox)
try:
    from pc_agent.config import ESP32_IP, OPENROUTER_API_KEY, TELEGRAM_BOT_TOKEN, BOT_PASSWORD, project_root
    from pc_agent.tools import system_tools
except Exception as exc:
    try:
        _write_crash_log(exc)
    except Exception:
        pass
    try:
        import tkinter.messagebox as _mb
        _mb.showerror("J.A.R.V.I.S. Startup Error",
                      f"Fatal error while importing project modules:\n\n{type(exc).__name__}: {exc}\n\nA crash_log.txt has been written to the application folder.")
    except Exception:
        # If GUI not available, print to stderr
        print(f"FATAL: {type(exc).__name__}: {exc}", file=sys.stderr)
    raise

APP_VERSION = "v2.1"


# ---------------------------------------------------------------------------
# Settings Dialog
# ---------------------------------------------------------------------------

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("⚙️  J.A.R.V.I.S.  –  Settings")
        self.geometry("600x760")
        self.minsize(500, 550)
        self.configure(bg="#070b12")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        # Load icon
        icon_path = _get_app_dir() / "jarvis_icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self._build_form()

    def _build_form(self):
        env_path = project_root / ".env"
        curr_env = {}
        if env_path.exists():
            from dotenv import dotenv_values
            curr_env = dotenv_values(env_path)

        OPENROUTER_MODELS = [
            "google/gemini-2.0-flash-001",
            "google/gemini-2.5-flash",
            "google/gemini-2.5-pro",
            "google/gemini-flash-1.5",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/o3-mini",
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-haiku",
            "anthropic/claude-sonnet-4-5",
            "meta-llama/llama-3.3-70b-instruct",
            "meta-llama/llama-3.1-8b-instruct",
            "deepseek/deepseek-r1",
            "deepseek/deepseek-chat-v3-0324",
            "mistralai/mistral-nemo",
            "qwen/qwen-2.5-72b-instruct",
        ]
        current_model = curr_env.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")

        fields = [
            ("OPENROUTER_API_KEY",     "OpenRouter API Key",                    curr_env.get("OPENROUTER_API_KEY", ""), True),
            ("TELEGRAM_BOT_TOKEN",     "Telegram Bot Token",                    curr_env.get("TELEGRAM_BOT_TOKEN", ""), True),
            ("BOT_PASSWORD",           "Bot Password (for /login)",             curr_env.get("BOT_PASSWORD", ""), True),
            ("ESP32_IP",               "ESP32 IP Address",                     curr_env.get("ESP32_IP", ""), False),
            ("WINDOWS_PC_PASSWORD",    "Windows PC Password (for /unlock)",     curr_env.get("WINDOWS_PC_PASSWORD", ""), True),
            ("DEFAULT_WORKSPACE",      "Default Workspace (leave empty for auto)", curr_env.get("DEFAULT_WORKSPACE", ""), False),
            ("ALLOWED_TELEGRAM_USERS", "Allowed Telegram User IDs (comma-separated)", curr_env.get("ALLOWED_TELEGRAM_USERS", ""), False),
        ]
        # Memory field — separate (shown with special styling)
        memory_name = curr_env.get("USER_NAME", "Sir")

        # ── Scrollable content area ──────────────────────────────────────
        content_frame = tk.Frame(self, bg="#070b12")
        content_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(content_frame, bg="#070b12", highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#070b12")

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def _resize_inner(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", _resize_inner)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>",  lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>",  lambda e: canvas.unbind_all("<MouseWheel>"))

        # Section header
        hdr = tk.Label(
            scroll_frame,
            text="⚙️  CONFIGURATION SETTINGS",
            bg="#070b12", fg="#00f3ff",
            font=("Segoe UI", 13, "bold"),
            anchor="w"
        )
        hdr.pack(fill="x", padx=16, pady=(16, 4))

        sub_hdr = tk.Label(
            scroll_frame,
            text="Enter your credentials below. Values are saved securely in your local .env file.",
            bg="#070b12", fg="#8ab4cc",
            font=("Segoe UI", 9),
            anchor="w"
        )
        sub_hdr.pack(fill="x", padx=16, pady=(0, 8))

        tk.Frame(scroll_frame, bg="#00f3ff", height=1).pack(fill="x", padx=16, pady=(0, 12))

        self.entries = {}

        # ── Memory Section ───────────────────────────────────────────────────
        mem_hdr = tk.Label(
            scroll_frame,
            text="🧠  MEMORY  &  PERSONALIZATION",
            bg="#070b12", fg="#00ff88",
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        )
        mem_hdr.pack(fill="x", padx=16, pady=(8, 2))
        mem_sub = tk.Label(
            scroll_frame,
            text="JARVIS will address you by this name in Telegram and voice responses.",
            bg="#070b12", fg="#8ab4cc",
            font=("Segoe UI", 9),
            anchor="w"
        )
        mem_sub.pack(fill="x", padx=16, pady=(0, 6))

        mem_row = tk.Frame(scroll_frame, bg="#0e1726", bd=0, highlightthickness=2,
                           highlightbackground="#00ff88")
        mem_row.pack(fill="x", padx=16, pady=5, ipady=4)

        tk.Label(
            mem_row, text="🏷️  Your Name  (JARVIS calls you by this)",
            fg="#00ff88", bg="#0e1726",
            font=("Segoe UI", 9, "bold"), anchor="w"
        ).pack(fill="x", padx=10, pady=(6, 2))

        mem_input = tk.Frame(mem_row, bg="#0e1726")
        mem_input.pack(fill="x", padx=10, pady=(0, 6))

        mem_entry = tk.Entry(
            mem_input,
            bg="#05101e", fg="#00ff88",
            insertbackground="#00ff88",
            font=("Consolas", 12, "bold"),
            relief="flat", bd=0
        )
        mem_entry.insert(0, memory_name or "Sir")
        mem_entry.pack(side="left", fill="x", expand=True, ipady=6)

        class _MemWrapper:
            def get(self_inner): return mem_entry.get().strip() or "Sir"  # noqa: E301
        self.entries["USER_NAME"] = _MemWrapper()

        tk.Frame(scroll_frame, bg="#00f3ff", height=1).pack(fill="x", padx=16, pady=(8, 12))

        # ── API & Config Section ─────────────────────────────────────────────
        api_hdr = tk.Label(
            scroll_frame,
            text="🔑  API  KEYS  &  CONFIGURATION",
            bg="#070b12", fg="#00f3ff",
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        )
        api_hdr.pack(fill="x", padx=16, pady=(0, 4))

        # ── OPENROUTER_MODEL — special Combobox row ────────────────────────
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Model.TCombobox",
            fieldbackground="#05101e",
            background="#1a2a40",
            foreground="#00ff88",
            selectbackground="#1a2a40",
            selectforeground="#00ff88",
            arrowcolor="#00f3ff",
            borderwidth=0,
        )
        style.map(
            "Model.TCombobox",
            fieldbackground=[("readonly", "#05101e")],
            foreground=[("readonly", "#00ff88")],
            selectbackground=[("readonly", "#1a2a40")],
        )

        model_row = tk.Frame(scroll_frame, bg="#0e1726", bd=0, highlightthickness=1,
                             highlightbackground="#1a2a40")
        model_row.pack(fill="x", padx=16, pady=5, ipady=4)

        tk.Label(
            model_row, text="🤖  OpenRouter Model",
            fg="#8ab4cc", bg="#0e1726",
            font=("Segoe UI", 9, "bold"), anchor="w"
        ).pack(fill="x", padx=10, pady=(6, 2))

        model_hint = tk.Label(
            model_row,
            text="Choose a preset or type any OpenRouter model ID manually",
            fg="#4a6a80", bg="#0e1726",
            font=("Segoe UI", 8), anchor="w"
        )
        model_hint.pack(fill="x", padx=10, pady=(0, 2))

        model_input_frame = tk.Frame(model_row, bg="#0e1726")
        model_input_frame.pack(fill="x", padx=10, pady=(0, 6))

        model_var = tk.StringVar(value=current_model)
        model_cb = ttk.Combobox(
            model_input_frame,
            textvariable=model_var,
            values=OPENROUTER_MODELS,
            style="Model.TCombobox",
            font=("Consolas", 10),
            state="normal",
        )
        model_cb.pack(side="left", fill="x", expand=True, ipady=4)

        # Make dropdown list dark-styled via option_add
        self.option_add("*TCombobox*Listbox.background", "#05101e")
        self.option_add("*TCombobox*Listbox.foreground", "#00ff88")
        self.option_add("*TCombobox*Listbox.selectBackground", "#1a2a40")
        self.option_add("*TCombobox*Listbox.selectForeground", "#00f3ff")
        self.option_add("*TCombobox*Listbox.font", "Consolas 10")

        # Expose as a pseudo-entry with .get() so save() works uniformly
        class _ComboWrapper:
            def get(self_inner): return model_var.get().strip()
        self.entries["OPENROUTER_MODEL"] = _ComboWrapper()

        # ── Remaining fields ────────────────────────────────────────────────
        for key, label, val, is_secret in fields:
            row = tk.Frame(scroll_frame, bg="#0e1726", bd=0, highlightthickness=1,
                           highlightbackground="#1a2a40")
            row.pack(fill="x", padx=16, pady=5, ipady=4)

            tk.Label(
                row, text=label,
                fg="#8ab4cc", bg="#0e1726",
                font=("Segoe UI", 9, "bold"), anchor="w"
            ).pack(fill="x", padx=10, pady=(6, 2))

            input_frame = tk.Frame(row, bg="#0e1726")
            input_frame.pack(fill="x", padx=10, pady=(0, 6))

            ent = tk.Entry(
                input_frame,
                bg="#05101e", fg="#00ff88",
                insertbackground="#00ff88",
                font=("Consolas", 10),
                relief="flat",
                bd=0,
                show="●" if is_secret else ""
            )
            ent.insert(0, val or "")
            ent.pack(side="left", fill="x", expand=True, ipady=4)

            if key == "ESP32_IP":
                def _do_auto_detect(entry_field, scan_btn):
                    scan_btn.config(text="⏳ Scanning...", state="disabled")
                    def _thread():
                        found = system_tools.auto_discover_esp32_ip()
                        if found:
                            self.after(0, lambda: entry_field.delete(0, tk.END))
                            self.after(0, lambda: entry_field.insert(0, found))
                            self.after(0, lambda: scan_btn.config(text="✅ Found!", bg="#00ff88", fg="#000", state="normal"))
                            self.after(2000, lambda: scan_btn.config(text="🔍 Auto-Detect", bg="#1a2a40", fg="#00f3ff", state="normal"))
                        else:
                            self.after(0, lambda: scan_btn.config(text="❌ Not Found", bg="#ff3366", fg="#fff", state="normal"))
                            self.after(2500, lambda: scan_btn.config(text="🔍 Auto-Detect", bg="#1a2a40", fg="#00f3ff", state="normal"))
                    threading.Thread(target=_thread, daemon=True).start()

                scan_b = tk.Button(
                    input_frame, text="🔍 Auto-Detect", bg="#1a2a40", fg="#00f3ff",
                    font=("Segoe UI", 8, "bold"), relief="flat", activebackground="#2a3a50",
                    cursor="hand2"
                )
                scan_b.config(command=lambda e=ent, b=scan_b: _do_auto_detect(e, b))
                scan_b.pack(side="right", padx=(4, 0))

                # Auto-run discovery in background if field is empty or points to unreachable IP
                if not val or val == "192.168.1.150":
                    _do_auto_detect(ent, scan_b)

            self.entries[key] = ent

        tk.Frame(scroll_frame, bg="#070b12", height=12).pack()

        # ── Fixed button bar ─────────────────────────────────────────────
        btn_bar = tk.Frame(self, bg="#0d1525", height=58,
                           highlightbackground="#00f3ff", highlightthickness=1)
        btn_bar.pack(fill="x", side="bottom")
        btn_bar.pack_propagate(False)

        tk.Button(
            btn_bar,
            text="💾  SAVE SETTINGS",
            bg="#00ff88", fg="#000",
            font=("Segoe UI", 11, "bold"),
            activebackground="#00cc66",
            relief="flat", cursor="hand2",
            padx=14, pady=8,
            command=self.save
        ).pack(side="right", padx=10, pady=8)

        tk.Button(
            btn_bar,
            text="✕  CANCEL",
            bg="#ff3366", fg="#fff",
            font=("Segoe UI", 11, "bold"),
            activebackground="#cc0033",
            relief="flat", cursor="hand2",
            padx=14, pady=8,
            command=self.destroy
        ).pack(side="right", padx=4, pady=8)

        note = tk.Label(
            btn_bar,
            text="✔ Settings saved to .env",
            bg="#0d1525", fg="#00ff88",
            font=("Segoe UI", 9)
        )
        note.pack(side="left", padx=12)

        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def save(self):
        env_path = project_root / ".env"
        env_dict = {}
        for key, entry in self.entries.items():
            val = entry.get().strip()
            # Auto-clean: if user pastes "KEY=value" or "KEY = value", strip the prefix
            if "=" in val:
                prefix = val.split("=", 1)[0].strip().upper()
                if prefix == key.upper():
                    val = val.split("=", 1)[1].strip()
            # Strip surrounding quotes if present
            if len(val) >= 2 and val[0] in ('"', "'") and val[-1] == val[0]:
                val = val[1:-1]
            env_dict[key] = val

        try:
            with open(env_path, "w", encoding="utf-8") as f:
                f.write("# J.A.R.V.I.S. Environment Configuration\n")
                for k, v in env_dict.items():
                    f.write(f"{k}={v}\n")

            # Reload environment in memory & pc_agent.config
            import pc_agent.config as pcc
            pcc.reload_config()

            # Refresh parent UI labels
            if hasattr(self.parent, "_refresh_config_labels"):
                self.parent._refresh_config_labels()

            messagebox.showinfo(
                "Settings Saved",
                "Configuration saved successfully!\nSettings have been updated."
            )
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

class JarvisApp(tk.Tk):
    def __init__(self):
        # Ensure Windows taskbar uses the correct app icon
        if sys.platform == "win32":
            try:
                import ctypes
                appid = "JarvisAI.Agent"
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
            except Exception:
                pass

        super().__init__()

        self.title(f"J.A.R.V.I.S.  Control Center  {APP_VERSION}")
        self.geometry("960x720")
        self.minsize(820, 600)
        self.configure(bg="#070b12")
        self.resizable(True, True)

        # ── Icon ──────────────────────────────────────────────────────────
        icon_path = _get_app_dir() / "jarvis_icon.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass
            try:
                img = tk.PhotoImage(file=str(icon_path))
                self.iconphoto(True, img)
            except Exception:
                try:
                    img = tk.PhotoImage(width=1, height=1)
                    self.iconphoto(True, img)
                except Exception:
                    pass

        # Bring window to front
        try:
            self.deiconify()
            self.lift()
            self.attributes("-topmost", True)
            self.after_idle(self.attributes, "-topmost", False)
            self.focus_force()
        except Exception:
            pass

        self.bot_thread = None
        self.bot_app = None
        self.is_monitoring = True

        self._apply_styles()
        self._build_ui()

        self._schedule_health_check()
        self._refresh_config_labels()

    def _refresh_config_labels(self):
        try:
            import pc_agent.config as pcc
            pcc.reload_config()
            esp_ip = getattr(pcc, "ESP32_IP", "")
            bot_tok = getattr(pcc, "TELEGRAM_BOT_TOKEN", "")
            if hasattr(self, "lbl_esp_ip"):
                self.lbl_esp_ip.config(text=f"IP Address:  {esp_ip if esp_ip else 'Not Set'}")
            if hasattr(self, "lbl_bot_name"):
                self.lbl_bot_name.config(
                    text=f"Telegram Bot:  {'Configured ✓' if bot_tok else 'No Token ✗'}"
                )
        except Exception:
            pass


    # ── Styles ──────────────────────────────────────────────────────────

    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TLabel",       background="#070b12", foreground="#e2f1f8", font=("Consolas", 10))
        style.configure("Header.TLabel",    font=("Segoe UI", 17, "bold"), foreground="#00f3ff", background="#0d1525")
        style.configure("SubHeader.TLabel", font=("Segoe UI", 9, "bold"),  foreground="#00ff88", background="#0d1525")
        style.configure("TFrame",       background="#070b12")
        style.configure("TScrollbar",   background="#0e1726", troughcolor="#050a14",
                        arrowcolor="#00f3ff", bordercolor="#0e1726")

    # ── UI Build ────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────
        header_frame = tk.Frame(self, bg="#0d1525", height=72,
                                highlightbackground="#00f3ff", highlightthickness=1)
        header_frame.pack(fill="x", padx=14, pady=(14, 0))
        header_frame.pack_propagate(False)

        ttk.Label(
            header_frame,
            text="⚡  J.A.R.V.I.S.  REMOTE SYSTEM CONTROL",
            style="Header.TLabel"
        ).pack(side="left", padx=18, pady=16)

        right_info = tk.Frame(header_frame, bg="#0d1525")
        right_info.pack(side="right", padx=18, pady=8)

        ttk.Label(right_info, text="TAILSCALE MESH ACTIVE", style="SubHeader.TLabel").pack(anchor="e")
        tk.Label(right_info, text=APP_VERSION, bg="#0d1525", fg="#334455",
                 font=("Consolas", 8)).pack(anchor="e")

        # ── Developer credit bar (below header) ──────────────────────────
        dev_bar = tk.Frame(self, bg="#050a14", height=22)
        dev_bar.pack(fill="x", padx=14, pady=(0, 0))
        dev_bar.pack_propagate(False)

        dev_left = tk.Label(
            dev_bar,
            text="  👨‍💻 Developed by  Thilan Kalhara",
            bg="#050a14", fg="#334d6e",
            font=("Segoe UI", 8)
        )
        dev_left.pack(side="left", padx=4)

        git_lnk = tk.Label(
            dev_bar,
            text="✨ github.com/Thilankalhara",
            bg="#050a14", fg="#00f3ff",
            font=("Segoe UI", 8, "underline"),
            cursor="hand2"
        )
        git_lnk.pack(side="left", padx=2)
        git_lnk.bind("<Button-1>", lambda e: __import__("webbrowser").open("https://github.com/Thilankalhara"))

        # ── Status Cards ────────────────────────────────────────────────
        cards_frame = tk.Frame(self, bg="#070b12")
        cards_frame.pack(fill="x", padx=14, pady=12)
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)

        # ESP32 card
        esp_card = tk.Frame(cards_frame, bg="#0e1726",
                            highlightbackground="#1e3050", highlightthickness=1)
        esp_card.grid(row=0, column=0, padx=(0, 6), pady=0, sticky="ew")

        tk.Label(esp_card, text=" ESP32  WOL  HARDWARE  NODE",
                 bg="#0d1f36", fg="#00f3ff",
                 font=("Segoe UI", 9, "bold"), anchor="w"
                 ).pack(fill="x", padx=0, pady=0)

        inner_esp = tk.Frame(esp_card, bg="#0e1726")
        inner_esp.pack(fill="x", padx=14, pady=10)

        self.lbl_esp_ip = tk.Label(
            inner_esp, text=f"IP Address:  {ESP32_IP}",
            bg="#0e1726", fg="#8ab4cc", font=("Consolas", 9), anchor="w"
        )
        self.lbl_esp_ip.pack(anchor="w")

        self.lbl_esp_status = tk.Label(
            inner_esp, text="●  CHECKING…",
            bg="#0e1726", fg="#ffaa00", font=("Consolas", 11, "bold"), anchor="w"
        )
        self.lbl_esp_status.pack(anchor="w", pady=(4, 0))

        self.lbl_esp_hint = tk.Label(
            inner_esp, text="",
            bg="#0e1726", fg="#556677", font=("Consolas", 8), anchor="w",
            wraplength=300, justify="left"
        )
        self.lbl_esp_hint.pack(anchor="w", pady=(2, 0))

        tk.Button(
            inner_esp, text="🔍 Scan / Reconnect",
            bg="#0e1726", fg="#00f3ff",
            font=("Segoe UI", 8), relief="flat",
            activebackground="#1a2a40", activeforeground="#00f3ff",
            cursor="hand2",
            command=lambda: threading.Thread(target=self._run_health_check, daemon=True).start()
        ).pack(anchor="w", pady=(4, 0))

        # Agent Daemon card
        agent_card = tk.Frame(cards_frame, bg="#0e1726",
                              highlightbackground="#1e3050", highlightthickness=1)
        agent_card.grid(row=0, column=1, padx=(6, 0), pady=0, sticky="ew")

        tk.Label(agent_card, text=" PYTHON  AGENT  DAEMON",
                 bg="#0d1f36", fg="#00f3ff",
                 font=("Segoe UI", 9, "bold"), anchor="w"
                 ).pack(fill="x", padx=0, pady=0)

        inner_agent = tk.Frame(agent_card, bg="#0e1726")
        inner_agent.pack(fill="x", padx=14, pady=10)

        self.lbl_bot_name = tk.Label(
            inner_agent,
            text=f"Telegram Bot:  {'Configured ✓' if TELEGRAM_BOT_TOKEN else 'No Token ✗'}",
            bg="#0e1726", fg="#8ab4cc", font=("Consolas", 9), anchor="w"
        )
        self.lbl_bot_name.pack(anchor="w")

        self.lbl_agent_status = tk.Label(
            inner_agent, text="●  STOPPED",
            bg="#0e1726", fg="#ff3366", font=("Consolas", 11, "bold"), anchor="w"
        )
        self.lbl_agent_status.pack(anchor="w", pady=(4, 0))

        # ── Action Buttons ──────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg="#070b12")
        btn_frame.pack(fill="x", padx=14, pady=10)

        buttons = [
            ("btn_start",    "▶  START AGENT",      "#00ff88", "#000", "#00cc66",  self.start_agent),
            ("btn_stop",     "⛔  EMERGENCY STOP",  "#ff3366", "#fff", "#cc0033",  self.emergency_stop),
            ("btn_wake",     "⚡  WAKE PC  (WoL)",   "#00f3ff", "#000", "#00c4cc",  self.trigger_wake),
            ("btn_voice",    "🔊  TEST VOICE",        "#7c3aed", "#fff", "#5b21b6",  self.test_voice),
            ("btn_settings", "⚙️  SETTINGS",          "#ffaa00", "#000", "#cc8800",  self.open_settings),
        ]

        for col, (attr, text, bg, fg, abg, cmd) in enumerate(buttons):
            b = tk.Button(
                btn_frame,
                text=text,
                bg=bg, fg=fg,
                activebackground=abg,
                activeforeground=fg,
                font=("Segoe UI", 10, "bold"),
                relief="flat",
                cursor="hand2",
                padx=10, pady=10,
                command=cmd
            )
            b.grid(row=0, column=col, padx=5, pady=0, sticky="ew")
            setattr(self, attr, b)
            btn_frame.grid_columnconfigure(col, weight=1)

        # ── Live Log Console ─────────────────────────────────────────────
        log_outer = tk.Frame(self, bg="#050a14",
                             highlightbackground="#00f3ff", highlightthickness=1)
        log_outer.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        log_header = tk.Frame(log_outer, bg="#0a1525")
        log_header.pack(fill="x")

        tk.Label(log_header, text="  LIVE  AGENT  SYSTEM  LOGS",
                 bg="#0a1525", fg="#00f3ff",
                 font=("Segoe UI", 9, "bold"), anchor="w"
                 ).pack(side="left", padx=6, pady=4)

        self.btn_clear_log = tk.Button(
            log_header, text="⌫ Clear",
            bg="#0a1525", fg="#556677",
            font=("Segoe UI", 8), relief="flat",
            activebackground="#0d1f36", activeforeground="#00f3ff",
            cursor="hand2",
            command=self._clear_log
        )
        self.btn_clear_log.pack(side="right", padx=6, pady=4)

        log_inner = tk.Frame(log_outer, bg="#02050b")
        log_inner.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_inner,
            bg="#02050b", fg="#00ff88",
            font=("Consolas", 9),
            insertbackground="#00f3ff",
            selectbackground="#1a3a5c",
            relief="flat",
            wrap="word",
            state="normal"
        )
        log_scroll = ttk.Scrollbar(log_inner, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        log_scroll.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True, padx=6, pady=6)

        self._log("System Control Center initialized. Ready for operations.")

    # ── Logging helpers ──────────────────────────────────────────────────

    def _log(self, text):
        timestamp = time.strftime("[%H:%M:%S]")
        self.log_text.insert(tk.END, f"{timestamp} {text}\n")
        self.log_text.see(tk.END)

    def _clear_log(self):
        self.log_text.delete("1.0", tk.END)

    # ── Settings ─────────────────────────────────────────────────────────

    def open_settings(self):
        SettingsDialog(self)

    # ── Agent control ────────────────────────────────────────────────────

    def start_agent(self):
        if self.bot_thread and self.bot_thread.is_alive():
            messagebox.showinfo("Status", "J.A.R.V.I.S. Agent is already running!")
            return

        import pc_agent.config as pcc
        pcc.reload_config()
        bot_token = getattr(pcc, "TELEGRAM_BOT_TOKEN", "")
        if not bot_token or bot_token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            messagebox.showerror(
                "Error",
                "TELEGRAM_BOT_TOKEN is not configured!\n"
                "Go to ⚙️ Settings and enter your Telegram Bot Token."
            )
            return

        self._log("Starting J.A.R.V.I.S. Telegram Bot Agent…")
        try:
            from pc_agent.telegram_bot import get_application, setup_bot_handlers, run_telegram_bot_threaded

            self.bot_app = get_application()
            if self.bot_app is None:
                messagebox.showerror("Error", "Failed to create Telegram bot application.\nCheck your token in Settings.")
                return

            setup_bot_handlers(self.bot_app)

            self.bot_thread = threading.Thread(
                target=run_telegram_bot_threaded, args=(self.bot_app,), daemon=True
            )
            self.bot_thread.start()

            self.lbl_agent_status.config(text="●  RUNNING", fg="#00ff88")
            self._log("Agent daemon launched. Telegram bot is now listening.")
            system_tools.speak_voice_feedback("JARVIS agent online and listening.")
        except Exception as e:
            self._log(f"Failed to start agent: {e}")
            messagebox.showerror("Error", f"Failed to start agent:\n{e}")

    def emergency_stop(self):
        """Immediately kill agent process for emergency security lockdown."""
        self._log("⚠️  EMERGENCY STOP TRIGGERED! Shutting down agent immediately…")

        if self.bot_app is not None:
            try:
                from pc_agent.telegram_bot import get_stop_event, clear_stop_event

                stop_evt = get_stop_event(self.bot_app)
                if stop_evt:
                    try:
                        stop_evt.set()
                    except Exception:
                        pass
                clear_stop_event(self.bot_app)
            except Exception:
                pass
            self.bot_app = None

        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=5)
            self.bot_thread = None

        self.lbl_agent_status.config(text="●  KILLED  (SECURITY LOCK)", fg="#ff3366")
        self._log("Agent process terminated. Security lockdown active.")
        system_tools.speak_voice_feedback("Emergency stop executed. System locked.")

    # ── Wake-on-LAN ──────────────────────────────────────────────────────

    def trigger_wake(self):
        """Send WoL magic packet via ESP32 HTTP endpoint."""
        self._log(f"Sending Wake-on-LAN request to ESP32 at http://{ESP32_IP}/wake …")
        self.btn_wake.config(text="⏳  SENDING…", state="disabled", bg="#334455", fg="#fff")

        def _wake():
            try:
                res = requests.get(f"http://{ESP32_IP}/wake", timeout=5)
                if res.status_code == 200:
                    self._log("✅  ESP32: WoL Magic Packet sent successfully!")
                    system_tools.speak_voice_feedback("Wake on LAN packet sent.")
                    self.after(0, lambda: self.btn_wake.config(
                        text="⚡  WAKE PC  (WoL)", state="normal", bg="#00f3ff", fg="#000"
                    ))
                else:
                    self._log(f"⚠️  ESP32 returned unexpected status: {res.status_code}")
                    self.after(0, lambda: self.btn_wake.config(
                        text="⚡  WAKE PC  (WoL)", state="normal", bg="#00f3ff", fg="#000"
                    ))

            except requests.exceptions.ConnectTimeout:
                self._log(
                    f"⚠️  ESP32 at {ESP32_IP} is UNREACHABLE — connection timed out.\n"
                    f"           Is the ESP32 powered on and on the same network?"
                )
                self.after(0, lambda: self.btn_wake.config(
                    text="❌  ESP32 TIMEOUT", state="normal", bg="#ff3366", fg="#fff"
                ))
                self.after(4000, lambda: self.btn_wake.config(
                    text="⚡  WAKE PC  (WoL)", bg="#00f3ff", fg="#000"
                ))

            except requests.exceptions.ConnectionError as e:
                self._log(f"❌  ESP32 connection error: {e}")
                self.after(0, lambda: self.btn_wake.config(
                    text="❌  CONNECTION ERROR", state="normal", bg="#ff3366", fg="#fff"
                ))
                self.after(4000, lambda: self.btn_wake.config(
                    text="⚡  WAKE PC  (WoL)", bg="#00f3ff", fg="#000"
                ))

            except Exception as e:
                self._log(f"❌  ESP32 WoL request failed: {e}")
                self.after(0, lambda: self.btn_wake.config(
                    text="⚡  WAKE PC  (WoL)", state="normal", bg="#00f3ff", fg="#000"
                ))

        threading.Thread(target=_wake, daemon=True).start()

    # ── Voice test ───────────────────────────────────────────────────────

    def test_voice(self):
        self._log("Testing Text-to-Speech voice synthesis…")
        system_tools.speak_voice_feedback(
            "Welcome sir, I am JARVIS. All PC automation tools are operational."
        )

    # ── Health Monitor (Tkinter-safe via after()) ─────────────────────────

    def _schedule_health_check(self):
        """Schedule the next health check using Tk's after() — thread-safe."""
        self._run_health_check()
        self.after(5000, self._schedule_health_check)

    def _run_health_check(self):
        """Run ESP32 and agent health check in a background thread."""
        def _check():
            # Read IP dynamically (may have changed in Settings)
            import pc_agent.config as pcc
            esp_ip = getattr(pcc, "ESP32_IP", "") or ESP32_IP

            # Update IP label
            self.after(0, lambda: self.lbl_esp_ip.config(
                text=f"IP Address:  {esp_ip if esp_ip else 'Not configured'}"
            ))

            # ESP32 ping
            if not esp_ip:
                self.after(0, lambda: self.lbl_esp_status.config(
                    text="●  NOT CONFIGURED", fg="#ff3366"
                ))
                self.after(0, lambda: self.lbl_esp_hint.config(
                    text="Set ESP32_IP in ⚙️ Settings"
                ))
            else:
                try:
                    res = requests.get(f"http://{esp_ip}/", timeout=3)
                    if res.status_code == 200:
                        self.after(0, lambda: self.lbl_esp_status.config(
                            text="●  ONLINE", fg="#00ff88"
                        ))
                        self.after(0, lambda: self.lbl_esp_hint.config(text=""))
                    else:
                        self.after(0, lambda: self.lbl_esp_status.config(
                            text=f"●  HTTP {res.status_code}", fg="#ff3366"
                        ))
                        self.after(0, lambda: self.lbl_esp_hint.config(
                            text=f"ESP32 at {esp_ip} returned error"
                        ))
                except requests.exceptions.ConnectionError:
                    # Connection failed — attempt quick subnet auto-scan
                    self.after(0, lambda: self.lbl_esp_status.config(
                        text="●  SCANNING NETWORK…", fg="#ffaa00"
                    ))
                    found_ip = system_tools.auto_discover_esp32_ip()
                    if found_ip:
                        pcc.ESP32_IP = found_ip
                        env_file = project_root / ".env"
                        if env_file.exists():
                            import re
                            content = env_file.read_text(encoding="utf-8")
                            content = re.sub(r"^ESP32_IP=.*$", f"ESP32_IP={found_ip}", content, flags=re.MULTILINE)
                            env_file.write_text(content, encoding="utf-8")

                        self.after(0, lambda: self.lbl_esp_ip.config(
                            text=f"IP Address:  {found_ip}"
                        ))
                        self.after(0, lambda: self.lbl_esp_status.config(
                            text="●  ONLINE (AUTO-FOUND)", fg="#00ff88"
                        ))
                        self.after(0, lambda: self.lbl_esp_hint.config(
                            text=f"Auto-detected ESP32 at {found_ip}"
                        ))
                    else:
                        self.after(0, lambda: self.lbl_esp_status.config(
                            text="●  OFFLINE / UNREACHABLE", fg="#ff3366"
                        ))
                        self.after(0, lambda: self.lbl_esp_hint.config(
                            text=f"Cannot reach {esp_ip}. Ensure ESP32 is powered on Wi-Fi."
                        ))
                except requests.exceptions.Timeout:
                    self.after(0, lambda: self.lbl_esp_status.config(
                        text="●  TIMEOUT", fg="#ffaa00"
                    ))
                    self.after(0, lambda: self.lbl_esp_hint.config(
                        text=f"No response from {esp_ip} (timeout)."
                    ))
                except Exception as ex:
                    err_msg = str(ex)[:80]
                    self.after(0, lambda: self.lbl_esp_status.config(
                        text="●  STANDBY / OFFLINE", fg="#ffaa00"
                    ))
                    self.after(0, lambda m=err_msg: self.lbl_esp_hint.config(
                        text=m
                    ))

            # Agent thread
            if self.bot_thread and self.bot_thread.is_alive():
                self.after(0, lambda: self.lbl_agent_status.config(
                    text="●  RUNNING", fg="#00ff88"
                ))
            else:
                if self.bot_app is not None:
                    pass  # don't overwrite KILLED status
                else:
                    self.after(0, lambda: self.lbl_agent_status.config(
                        text="●  STOPPED", fg="#ff3366"
                    ))

        threading.Thread(target=_check, daemon=True).start()

    # ── Window close ────────────────────────────────────────────────────

    def on_close(self):
        self.is_monitoring = False
        self.emergency_stop()
        self.destroy()


if __name__ == "__main__":
    try:
        app = JarvisApp()
        app.protocol("WM_DELETE_WINDOW", app.on_close)
        app.mainloop()
    except Exception as e:
        _write_crash_log(e)
        raise e

