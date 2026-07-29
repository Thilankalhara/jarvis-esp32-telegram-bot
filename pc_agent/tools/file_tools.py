import os
import shutil
import zipfile
from pathlib import Path
from pc_agent.config import DEFAULT_WORKSPACE

def resolve_path(path_str: str) -> Path:
    """Resolve relative or absolute path safely."""
    path = Path(path_str)
    if not path.is_absolute():
        path = Path(DEFAULT_WORKSPACE) / path
    return path.resolve()

def list_directory(directory_path: str = None) -> list:
    """List contents of a directory."""
    target = resolve_path(directory_path) if directory_path else Path(DEFAULT_WORKSPACE)
    if not target.exists() or not target.is_dir():
        return [f"Error: Directory '{target}' does not exist or is not a folder."]
    
    items = []
    for entry in target.iterdir():
        info = {
            "name": entry.name,
            "type": "folder" if entry.is_dir() else "file",
            "size_kb": round(entry.stat().st_size / 1024, 2) if entry.is_file() else 0
        }
        items.append(info)
    return items

def read_file_content(file_path: str, max_lines: int = 200) -> str:
    """Read contents of a text file."""
    path = resolve_path(file_path)
    if not path.exists() or not path.is_file():
        return f"Error: File '{path}' does not exist."
    
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = [f.readline() for _ in range(max_lines)]
        content = "".join(lines)
        return content if content else "(File is empty)"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file_content(file_path: str, content: str, append: bool = False) -> str:
    """Create or write content to a file."""
    path = resolve_path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    mode = "a" if append else "w"
    try:
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)
        return f"Successfully written to '{path}' (Size: {len(content)} chars)."
    except Exception as e:
        return f"Error writing to file: {str(e)}"

def search_files(query: str, search_dir: str = None) -> list:
    """Search for files matching a keyword in name or extension."""
    target = resolve_path(search_dir) if search_dir else Path(DEFAULT_WORKSPACE)
    matches = []
    
    if not target.exists():
        return [f"Search directory '{target}' does not exist."]

    for root, dirs, files in os.walk(target):
        for f in files:
            if query.lower() in f.lower():
                full_path = Path(root) / f
                matches.append(str(full_path))
                if len(matches) >= 30: # Limit results
                    break
        if len(matches) >= 30:
            break
            
    return matches if matches else [f"No files matching '{query}' found in {target}."]

def compress_folder(folder_path: str, zip_name: str = None) -> str:
    """Compress a folder into a ZIP archive."""
    target = resolve_path(folder_path)
    if not target.exists() or not target.is_dir():
        return f"Error: Folder '{target}' does not exist."
    
    zip_path = target.with_suffix(".zip") if not zip_name else resolve_path(zip_name)
    try:
        shutil.make_archive(str(zip_path.with_suffix("")), 'zip', target)
        return f"Successfully created zip archive at: {zip_path}"
    except Exception as e:
        return f"Error compressing folder: {str(e)}"
