import subprocess
import sys
from pathlib import Path

RELEASE_TAG = "v2.1"
REPO = "Thilankalhara/jarvis-esp32-telegram-bot"
DEFAULT_ASSETS = [
    Path("dist") / "JARVIS_Control_Center" / "JARVIS_Control_Center.exe",
    Path("dist") / "JARVIS_Control_Center" / "START_JARVIS.bat",
]


def find_gh_executable() -> str:
    local = Path(__file__).resolve().parent / "gh.exe"
    if local.exists():
        return str(local)
    return "gh"


def run_command(cmd, capture_output=True, check=False):
    return subprocess.run(
        cmd,
        text=True,
        capture_output=capture_output,
        check=check,
    )


def ensure_assets_exist(files):
    missing = [str(path) for path in files if not path.exists()]
    if missing:
        print("[!] Missing required release assets:")
        for path in missing:
            print(f"  - {path}")
        return False
    return True


def check_auth(gh_cmd):
    result = run_command([gh_cmd, "auth", "status"])
    if result.returncode != 0:
        print("[!] GitHub CLI is not authenticated.")
        print(result.stdout.strip())
        print(result.stderr.strip())
        print("\nRun 'gh auth login' and complete the browser/device login flow before retrying.")
        return False
    return True


def upload_release(gh_cmd, tag, assets, repo):
    print(f"Uploading release assets to {repo}, tag {tag}...")
    cmd = [gh_cmd, "release", "upload", tag] + [str(asset) for asset in assets] + ["--clobber", "--repo", repo]
    result = run_command(cmd, capture_output=False)
    if result.returncode == 0:
        print("[+] Upload complete.")
        return True
    print("[!] Upload failed.")
    return False


def create_release(gh_cmd, tag, assets, repo):
    print(f"Creating release {tag} and uploading assets...")
    cmd = [
        gh_cmd,
        "release",
        "create",
        tag,
        *[str(asset) for asset in assets],
        "--repo",
        repo,
        "--title",
        tag,
        "--notes",
        "Release build assets for JARVIS Control Center.",
    ]
    result = run_command(cmd, capture_output=False)
    if result.returncode == 0:
        print("[+] Release created and assets uploaded.")
        return True
    print("[!] Release creation failed.")
    return False


def release_exists(gh_cmd, tag, repo):
    result = run_command([gh_cmd, "release", "view", tag, "--repo", repo])
    return result.returncode == 0


def parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Upload J.A.R.V.I.S. release assets to GitHub using gh CLI."
    )
    parser.add_argument("tag", nargs="?", default=RELEASE_TAG, help="Release tag name")
    parser.add_argument(
        "assets",
        nargs="*",
        default=[str(p) for p in DEFAULT_ASSETS],
        help="List of asset file paths to upload",
    )
    parser.add_argument("--repo", default=REPO, help="GitHub repository owner/name")
    return parser.parse_args()


def main():
    args = parse_args()
    assets = [Path(asset) for asset in args.assets]
    if not ensure_assets_exist(assets):
        return 1

    gh_cmd = find_gh_executable()
    if not check_auth(gh_cmd):
        return 2

    if release_exists(gh_cmd, args.tag, args.repo):
        return 0 if upload_release(gh_cmd, args.tag, assets, args.repo) else 3
    return 0 if create_release(gh_cmd, args.tag, assets, args.repo) else 4


if __name__ == "__main__":
    sys.exit(main())
