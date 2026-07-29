import os
import sys
import subprocess
import webbrowser
import urllib.parse
import requests
from pathlib import Path
from pc_agent.config import DEFAULT_WORKSPACE


def _open_in_default_browser(url: str) -> bool:
    """Open URL natively in default web browser as a new tab on Windows."""
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    if sys.platform == "win32":
        try:
            os.startfile(url)
            return True
        except Exception:
            pass

    try:
        webbrowser.open_new_tab(url)
        return True
    except Exception:
        try:
            webbrowser.open(url)
            return True
        except Exception:
            try:
                subprocess.Popen(f'start "" "{url}"', shell=True)
                return True
            except Exception:
                return False


def open_browser_url(url: str) -> str:
    """Open any web URL in the default desktop web browser in a NEW TAB."""
    target_url = url.strip()
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = "https://" + target_url

    if _open_in_default_browser(target_url):
        return f"Successfully opened browser tab to: {target_url}"
    else:
        return f"Error opening URL '{target_url}'"


def search_web(query: str, max_results: int = 5) -> str:
    """Search the web and open Google results in a NEW BROWSER TAB on the PC."""
    clean_query = query.strip()
    search_url = f"https://www.google.com/search?q={urllib.parse.quote(clean_query)}"

    # Force open Google search in a NEW TAB in the default browser
    _open_in_default_browser(search_url)

    # ── Method 1: duckduckgo-search library (best) ─────────────────────────
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(clean_query, max_results=max_results):
                results.append(f"• *{r.get('title', '')}*\n  {r.get('body', '')}\n  🔗 {r.get('href', '')}")
        if results:
            return (
                f"🔍 *Web Search: {clean_query}*\n"
                f"_(Browser opened on your PC screen with Google results)_\n\n"
                + "\n\n".join(results)
            )
    except ImportError:
        pass
    except Exception:
        pass

    # ── Method 2: DuckDuckGo HTML scrape fallback ───────────────────────────
    try:
        import re
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0.0.0 Safari/537.36"
        }
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": clean_query},
            headers=headers,
            timeout=12
        )
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
        titles   = re.findall(r'class="result__a"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
        urls     = re.findall(r'uddg=(https?[^&"]+)', resp.text)

        def _clean(s):
            return re.sub(r"<[^>]+>", "", s).strip()

        results = []
        for i in range(min(max_results, len(snippets))):
            title   = _clean(titles[i])   if i < len(titles)   else ""
            snippet = _clean(snippets[i]) if i < len(snippets) else ""
            url     = requests.utils.unquote(urls[i]) if i < len(urls) else ""
            results.append(f"• *{title}*\n  {snippet}\n  🔗 {url}")

        if results:
            return (
                f"🔍 *Web Search: {clean_query}*\n"
                f"_(Browser opened on your PC screen)_\n\n"
                + "\n\n".join(results)
            )
    except Exception:
        pass

    return (
        f"🔍 *Google Search opened on your PC screen for:* `{clean_query}`"
    )


def fetch_url_text(url: str) -> str:
    """Fetch and return cleaned text content of a web page."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        import re
        clean = re.sub(r"<[^>]+>", " ", res.text)
        clean = " ".join(clean.split())
        return clean[:4000]
    except Exception as e:
        return f"Error fetching URL '{url}': {str(e)}"


def download_file(url: str, filename: str = None) -> str:
    """Download a file from a URL to the PC workspace."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, stream=True, timeout=30)
        res.raise_for_status()

        if not filename:
            filename = url.split("/")[-1].split("?")[0] or "downloaded_file.bin"

        save_path = Path(DEFAULT_WORKSPACE) / filename
        with open(save_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)

        return f"✅ Downloaded to: '{save_path}'"
    except Exception as e:
        return f"Error downloading from '{url}': {str(e)}"
