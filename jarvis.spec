# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os

block_cipher = None

# Packages known to need explicit full collection with PyInstaller — they
# either load models/config dynamically or bundle non-Python data files that
# static analysis misses.
packages_to_collect = [
    "TTS",
    "faster_whisper",
    "chromadb",
    "openwakeword",
    "onnxruntime",
    "torch",
    "torchaudio",
    "torchcodec",
    "ollama",
]

datas = []
binaries = []
hiddenimports = []

for pkg in packages_to_collect:
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

# Our own data files: dashboard UI + boot sound assets
datas += [
    ("ui/dashboard.html", "ui"),
    ("ui/assets/boot_intro.wav", "ui/assets"),
    ("ui/assets/boot_loop.wav", "ui/assets"),
    ("ui/assets/boot_ready.wav", "ui/assets"),
]

# Extra hidden imports PyInstaller's static analysis commonly misses
hiddenimports += [
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebChannel",
    "keyboard",
    "sounddevice",
    "soundfile",
    "pyautogui",
    "pygetwindow",
    "pystray",
    "ddgs",
]

a = Analysis(
    ["run_app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="JARVIS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # keep console visible for now, to see errors during first builds
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="ui/assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="JARVIS",
)
