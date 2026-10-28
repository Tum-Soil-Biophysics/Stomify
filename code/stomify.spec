# -*- mode: python ; coding: utf-8 -*-
"""
Stomify PyInstaller spec file.
One-DIRECTORY build with bundled resources (QSS, logo).
The YOLO model is NOT bundled here — it ships via the Inno Setup installer.

NOTE: Switched from --onefile to --onedir to eliminate the 60-90 second
temp-extraction delay on every launch. The Inno Setup installer handles
distribution, so users still get a single-click install experience.
"""

import os

block_cipher = None

# Paths
APP_DIR = r'.'

a = Analysis(
    [os.path.join(APP_DIR, 'main.py')],
    pathex=[APP_DIR],
    binaries=[],
    datas=[
        # Bundle resource files (QSS themes + logo)
        (os.path.join(APP_DIR, 'resources', 'style.qss'), 'resources'),
        (os.path.join(APP_DIR, 'resources', 'style_dark.qss'), 'resources'),
        (os.path.join(APP_DIR, 'resources', 'logo.png'), 'resources'),
        (os.path.join(APP_DIR, 'resources', 'logo.ico'), 'resources'),
        (os.path.join(APP_DIR, 'resources', 'splash.png'), 'resources'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSvg',
        'cv2',
        'numpy',
        'pandas',
        'openpyxl',
        'PIL',
        'ultralytics',
        'ultralytics.nn',
        'ultralytics.nn.tasks',
        'ultralytics.utils',
        'ultralytics.engine',
        'ultralytics.engine.model',
        'ultralytics.engine.predictor',
        'ultralytics.engine.results',
        'ultralytics.models',
        'ultralytics.models.yolo',
        'ultralytics.models.yolo.detect',
        'ultralytics.models.yolo.detect.predict',
        'torch',
        'torch.nn',
        'torchvision',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'jupyter',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE — in onedir mode, this only contains the bootloader + scripts
exe = EXE(
    pyz,
    a.scripts,
    [],                          # binaries/datas go into COLLECT, not EXE
    exclude_binaries=True,       # key flag for onedir mode
    name='Stomify',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,               # No console window — pure GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(APP_DIR, 'resources', 'logo.ico'),
)

# COLLECT — gathers all binaries, data files, and dependencies into a directory
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Stomify',
)
