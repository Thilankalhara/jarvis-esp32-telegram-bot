import subprocess
import os
from pathlib import Path
from pc_agent.config import DEFAULT_WORKSPACE

def execute_terminal_command(command: str, working_dir: str = None) -> dict:
    """Execute a PowerShell / CMD / Bash command on the system and capture output."""
    cwd = Path(working_dir) if working_dir else Path(DEFAULT_WORKSPACE)
    if not cwd.exists():
        cwd = Path(DEFAULT_WORKSPACE)

    # Blacklist dangerous/destructive formatting commands for safety
    forbidden = ["format c:", "rmdir /s /q c:\\", "del /f /s /q c:\\", "mkfs"]
    if any(f in command.lower() for f in forbidden):
        return {"error": "Execution denied: Dangerous command detected."}

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120
        )
        return {
            "stdout": result.stdout[:2000] if result.stdout else "",
            "stderr": result.stderr[:1000] if result.stderr else "",
            "returncode": result.returncode,
            "cwd": str(cwd)
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out after 120 seconds."}
    except Exception as e:
        return {"error": f"Execution failed: {str(e)}"}

def git_operation(action: str, repo_path: str = None, repo_url: str = None, message: str = "Automated commit from JARVIS") -> str:
    """Perform Git operations: 'status', 'pull', 'clone', 'commit_push'."""
    cwd = Path(repo_path) if repo_path else Path(DEFAULT_WORKSPACE)
    action = action.lower().strip()
    
    try:
        if action == "status":
            res = subprocess.run("git status", shell=True, cwd=str(cwd), capture_output=True, text=True)
            return res.stdout or res.stderr
        elif action == "pull":
            res = subprocess.run("git pull", shell=True, cwd=str(cwd), capture_output=True, text=True)
            return res.stdout or res.stderr
        elif action == "clone":
            if not repo_url:
                return "Error: repo_url is required for git clone."
            res = subprocess.run(f"git clone {repo_url}", shell=True, cwd=str(cwd), capture_output=True, text=True)
            return res.stdout or res.stderr
        elif action == "commit_push":
            cmd = f'git add . && git commit -m "{message}" && git push'
            res = subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True, text=True)
            return res.stdout or res.stderr
        else:
            return f"Unknown Git action '{action}'. Supported: 'status', 'pull', 'clone', 'commit_push'."
    except Exception as e:
        return f"Error executing Git action '{action}': {str(e)}"
