# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect all complex packages
tg_datas, tg_binaries, tg_hiddenimports = collect_all('telegram')
httpx_datas, httpx_binaries, httpx_hiddenimports = collect_all('httpx')
openai_datas, openai_binaries, openai_hiddenimports = collect_all('openai')

a = Analysis(
    ['jarvis_app.py'],
    pathex=['.'],
    binaries=tg_binaries + httpx_binaries + openai_binaries,
    datas=[
        ('jarvis_icon.ico', '.'),
        ('.env.template', '.'),
        ('pc_agent', 'pc_agent'),
    ] + tg_datas + httpx_datas + openai_datas,
    hiddenimports=[
        'pc_agent',
        'pc_agent.config',
        'pc_agent.tools',
        'pc_agent.tools.system_tools',
        'pc_agent.tools.file_tools',
        'pc_agent.tools.web_tools',
        'pc_agent.tools.doc_tools',
        'pc_agent.tools.dev_tools',
        'pc_agent.telegram_bot',
        'pc_agent.agent',
        'pyautogui',
        'psutil',
        'mss',
        'PIL',
        'PIL._tkinter_finder',
        'docx',
        'requests',
        'dotenv',
        'asyncio',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'duckduckgo_search',
        'openai',
    ] + tg_hiddenimports + httpx_hiddenimports + openai_hiddenimports
    + collect_submodules('telegram')
    + collect_submodules('httpx')
    + collect_submodules('openai'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'pandas', 'IPython', 'jupyter'],
    noarchive=False,
)

pyz = PYZ(a.pure)

# Single standalone double-clickable executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='JARVIS_AI_Agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Run directly as GUI app on double click
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='jarvis_icon.ico',
)
