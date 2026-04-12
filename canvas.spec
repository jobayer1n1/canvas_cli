# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['canvas.py'],
    pathex=[],
    binaries=[],
    datas=[('commands', 'commands'), ('api', 'api'), ('utils', 'utils')],
    hiddenimports=['requests', 'tkinter', 'tkinter.filedialog', 'canvasapi', 'canvasapi.exceptions'],
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
    name='canvas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
