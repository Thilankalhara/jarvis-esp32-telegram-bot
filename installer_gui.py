import os
import sys
import time
import shutil
import zipfile
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

APP_NAME = "J.A.R.V.I.S. Control Center"
APP_DIR_NAME = "JARVIS_Control_Center"

def get_bundle_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _is_file_locked(path: Path) -> bool:
    try:
        if not path.exists():
            return False
        with open(path, 'a+b'):
            pass
        return False
    except PermissionError:
        return True
    except OSError:
        return True


def _terminate_running_process(exe_name: str) -> bool:
    try:
        subprocess.run(
            ["taskkill", "/IM", exe_name, "/F"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


class SetupWizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - Setup Wizard")
        self.geometry("580x420")
        self.minsize(500, 380)
        self.configure(bg="#070b12")
        self.resizable(False, False)

        default_install = Path.home() / "AppData" / "Local" / APP_DIR_NAME
        self.install_path_var = tk.StringVar(value=str(default_install))
        self.desktop_shortcut_var = tk.BooleanVar(value=True)
        self.startmenu_shortcut_var = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg="#0d1525", height=70, highlightbackground="#00f3ff", highlightthickness=1)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="⚡ J.A.R.V.I.S. CONTROL CENTER SETUP", bg="#0d1525", fg="#00f3ff",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=20, pady=18)

        # Body
        body = tk.Frame(self, bg="#070b12")
        body.pack(fill="both", expand=True, padx=20, pady=15)

        tk.Label(body, text="Select Installation Folder:", bg="#070b12", fg="#8ab4cc",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 5))

        path_frame = tk.Frame(body, bg="#0e1726")
        path_frame.pack(fill="x", pady=(0, 15))

        path_ent = tk.Entry(path_frame, textvariable=self.install_path_var, bg="#05101e", fg="#00ff88",
                            font=("Consolas", 9), relief="flat", bd=0)
        path_ent.pack(side="left", fill="x", expand=True, padx=8, pady=8, ipady=4)

        browse_btn = tk.Button(path_frame, text="Browse...", bg="#1a2a40", fg="#00f3ff",
                               font=("Segoe UI", 9, "bold"), relief="flat", command=self._browse)
        browse_btn.pack(side="right", padx=8, pady=8)

        # Options
        opt_frame = tk.Frame(body, bg="#0e1726", highlightbackground="#1a2a40", highlightthickness=1)
        opt_frame.pack(fill="x", pady=(0, 15), ipady=8)

        tk.Label(opt_frame, text="Shortcut Options:", bg="#0e1726", fg="#00f3ff",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(6, 4))

        cb1 = tk.Checkbutton(opt_frame, text="Create Desktop Shortcut", variable=self.desktop_shortcut_var,
                             bg="#0e1726", fg="#e2f1f8", selectcolor="#05101e", activebackground="#0e1726",
                             activeforeground="#00f3ff", font=("Segoe UI", 9))
        cb1.pack(anchor="w", padx=15, pady=2)

        cb2 = tk.Checkbutton(opt_frame, text="Create Start Menu Shortcut", variable=self.startmenu_shortcut_var,
                             bg="#0e1726", fg="#e2f1f8", selectcolor="#05101e", activebackground="#0e1726",
                             activeforeground="#00f3ff", font=("Segoe UI", 9))
        cb2.pack(anchor="w", padx=15, pady=2)

        # Status & Progress
        self.lbl_status = tk.Label(body, text="Ready to install.", bg="#070b12", fg="#ffaa00",
                                   font=("Segoe UI", 9, "italic"))
        self.lbl_status.pack(anchor="w", pady=(5, 5))

        self.progress = ttk.Progressbar(body, orient="horizontal", mode="indeterminate")
        self.progress.pack(fill="x", pady=(0, 10))

        # Bottom Bar
        btn_bar = tk.Frame(self, bg="#0d1525", height=50)
        btn_bar.pack(fill="x", side="bottom")

        self.btn_install = tk.Button(btn_bar, text="🚀 INSTALL NOW", bg="#00ff88", fg="#000",
                                    font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                                    padx=15, pady=6, command=self._start_install)
        self.btn_install.pack(side="right", padx=15, pady=8)

        tk.Button(btn_bar, text="Cancel", bg="#ff3366", fg="#fff",
                  font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                  padx=10, pady=6, command=self.destroy).pack(side="right", padx=5, pady=8)

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.install_path_var.get())
        if d:
            self.install_path_var.set(str(Path(d) / APP_DIR_NAME))

    def _start_install(self):
        target_dir = Path(self.install_path_var.get())
        self.btn_install.config(state="disabled")
        self.progress.start(10)
        self.lbl_status.config(text="Extracting application files...")

        def _do_install():
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                payload_zip = get_bundle_dir() / "jarvis_app_payload.zip"

                exe_path = target_dir / "JARVIS_Control_Center.exe"
                if exe_path.exists() and _is_file_locked(exe_path):
                    user_choice = messagebox.askyesno(
                        "J.A.R.V.I.S. Is Running",
                        "A running J.A.R.V.I.S. executable was detected. Close it now and retry the install?",
                    )
                    if user_choice:
                        if _terminate_running_process(exe_path.name):
                            time.sleep(1)
                            if exe_path.exists() and _is_file_locked(exe_path):
                                self.after(0, self._on_error, "J.A.R.V.I.S. is still locked after closing. Please close it manually and retry.")
                                return
                        else:
                            self.after(0, self._on_error, "Unable to terminate the running J.A.R.V.I.S. process. Close it manually and retry the install.")
                            return
                    else:
                        self.after(0, self._on_error, "Target executable is locked by a running process. Close J.A.R.V.I.S. and retry the install.")
                        return

                # If the folder exists, remove stale files before extracting
                if target_dir.exists() and any(target_dir.iterdir()):
                    try:
                        for item in target_dir.iterdir():
                            if item.is_file():
                                item.unlink()
                            else:
                                shutil.rmtree(item)
                    except Exception:
                        pass

                with zipfile.ZipFile(payload_zip, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)

                # Ensure default blank .env exists
                env_file = target_dir / ".env"
                env_tmpl = target_dir / ".env.template"
                if not env_file.exists() and env_tmpl.exists():
                    shutil.copy(env_tmpl, env_file)

                # Shortcuts creation
                ico_path = target_dir / "jarvis_icon.ico"

                if self.desktop_shortcut_var.get():
                    desktop = Path.home() / "Desktop"
                    self._create_shortcut(exe_path, desktop / "J.A.R.V.I.S. Control Center.lnk", target_dir, ico_path)

                if self.startmenu_shortcut_var.get():
                    start_menu = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
                    self._create_shortcut(exe_path, start_menu / "J.A.R.V.I.S. Control Center.lnk", target_dir, ico_path)

                self.after(0, self._on_success, target_dir, exe_path)
            except Exception as e:
                self.after(0, self._on_error, str(e))

        import threading
        threading.Thread(target=_do_install, daemon=True).start()

    def _create_shortcut(self, target, shortcut_path, working_dir, icon_path):
        try:
            ps_script = f"""
            $WshShell = New-Object -comObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
            $Shortcut.TargetPath = '{target}'
            $Shortcut.WorkingDirectory = '{working_dir}'
            if (Test-Path '{icon_path}') {{ $Shortcut.IconLocation = '{icon_path}' }}
            $Shortcut.Save()
            """
            subprocess.run(["powershell", "-Command", ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

    def _on_success(self, target_dir, exe_path):
        self.progress.stop()
        self.lbl_status.config(text="Installation Complete! ✔", fg="#00ff88")
        msg = f"{APP_NAME} installed successfully to:\n" + str(target_dir) + "\n\nWould you like to launch J.A.R.V.I.S. now?"
        res = messagebox.askyesno("Installation Successful", msg)
        if res:
            subprocess.Popen([str(exe_path)], cwd=str(target_dir))
        self.destroy()

    def _on_error(self, err_msg):
        self.progress.stop()
        self.btn_install.config(state="normal")
        self.lbl_status.config(text="Installation failed! ❌", fg="#ff3366")
        messagebox.showerror("Installation Error", f"Failed to install {APP_NAME}:\n" + str(err_msg))

if __name__ == "__main__":
    app = SetupWizard()
    app.mainloop()
