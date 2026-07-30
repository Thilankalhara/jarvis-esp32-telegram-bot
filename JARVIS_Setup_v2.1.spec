# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\HP\\OneDrive\\Desktop\\Esp32 automation\\installer_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\HP\\OneDrive\\Desktop\\Esp32 automation\\dist\\jarvis_app_payload.zip', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='JARVIS_Setup_v2.1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\HP\\OneDrive\\Desktop\\Esp32 automation\\jarvis_icon.ico'],
)
