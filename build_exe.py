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
    
    # Ensure template .env exists in dist
    template_src = root_dir / ".env.template"
    if template_src.exists():
        shutil.copy(template_src, dist_dir / ".env.template")
        if not (dist_dir / ".env").exists():
            shutil.copy(template_src, dist_dir / ".env")
            
    print("\n" + "="*60)
    print(" BUILD COMPLETE SUCCESSFUL!")
    print(f" Executable: {exe_file}")
    print("="*60)
    print("\nYou can now double-click 'JARVIS_AI_Agent.exe' to run JARVIS directly!")


if __name__ == "__main__":
    build_executable()
