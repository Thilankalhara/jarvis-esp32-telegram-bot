import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_installer_package():
    print("=" * 60)
    print(" CREATING J.A.R.V.I.S. STANDALONE SETUP INSTALLER")
    print("=" * 60)

    project_dir = Path(__file__).resolve().parent
    dist_app_dir = project_dir / "dist" / "JARVIS_Control_Center"

    if not dist_app_dir.exists():
        print("[!] App distribution missing. Running build_exe.py first...")
        from build_exe import build_executable
        build_executable()

    zip_path = project_dir / "dist" / "jarvis_app_payload.zip"
    print(f"\n[+] Compressing app payload into {zip_path.name}...")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(project_dir / "dist" / "jarvis_app_payload"), 'zip', str(dist_app_dir))

    installer_script = project_dir / "installer_gui.py"
    if not installer_script.exists():
        raise FileNotFoundError(f"Installer script missing: {installer_script}")

    installer_exe_name = "JARVIS_Setup_v2.1"
    print("\n[+] Compiling installer executable with PyInstaller...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--name={installer_exe_name}",
        f"--icon={project_dir / 'jarvis_icon.ico'}",
        f"--add-data={zip_path};.",
        str(installer_script),
    ]
    subprocess.run(cmd, check=True)

    final_installer_path = project_dir / "dist" / f"{installer_exe_name}.exe"
    print("\n" + "=" * 60)
    print(" INSTALLER BUILD COMPLETE!")
    print(f" Installer Package: {final_installer_path}")
    print("=" * 60)


if __name__ == "__main__":
    create_installer_package()
