import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_executable():
    print("="*60)
    print(" J.A.R.V.I.S. STANDALONE .EXE BUILDER")
    print("="*60)
    
    root_dir = Path(__file__).resolve().parent
    
    # Check pyinstaller
    try:
        import PyInstaller
    except ImportError:
        print("[+] PyInstaller not found. Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    spec_path = root_dir / "jarvis_exe.spec"
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        str(spec_path),
    ]
    
    print("\n[+] Compiling standalone EXE package using PyInstaller...")
    result = subprocess.run(cmd, check=True)
    
    dist_dir = root_dir / "dist"
    exe_file = dist_dir / "JARVIS_AI_Agent.exe"
    release_dir = dist_dir / "JARVIS_Control_Center"
    release_dir.mkdir(parents=True, exist_ok=True)
    release_exe = release_dir / "JARVIS_Control_Center.exe"

    if exe_file.exists():
        shutil.copy2(exe_file, release_exe)
    else:
        print(f"[!] Warning: built executable not found at {exe_file}")

    # Ensure template .env exists in dist and release folder
    template_src = root_dir / ".env.template"
    if template_src.exists():
        shutil.copy2(template_src, dist_dir / ".env.template")
        if not (dist_dir / ".env").exists():
            shutil.copy2(template_src, dist_dir / ".env")
        shutil.copy2(template_src, release_dir / ".env.template")
        if not (release_dir / ".env").exists():
            shutil.copy2(template_src, release_dir / ".env")

    bat_path = release_dir / "START_JARVIS.bat"
    bat_path.write_text('@echo off\r\n"%~dp0JARVIS_Control_Center.exe"\r\npause\r\n', encoding="utf-8")

    print("\n" + "="*60)
    print(" BUILD COMPLETE SUCCESSFUL!")
    print(f" Executable: {release_exe}")
    print("="*60)
    print("\nYou can now double-click 'JARVIS_Control_Center.exe' from the dist/JARVIS_Control_Center folder to run JARVIS directly!")


if __name__ == "__main__":
    build_executable()
