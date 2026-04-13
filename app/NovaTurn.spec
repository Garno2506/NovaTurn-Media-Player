# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# PyInstaller-safe project root
project_root = os.path.abspath(os.getcwd())


# Helper to include entire folders cleanly
def collect_folder(src_folder, dest_folder):
    return [
        (os.path.join(src_folder, f), os.path.join(dest_folder, f))
        for f in os.listdir(src_folder)
    ]


# Paths inside your project
assets_path   = os.path.join(project_root, "app", "assets", "branding")
vlc_path      = os.path.join(project_root, "app", "vlc")
banners_path  = os.path.join(project_root, "app", "banners")

a = Analysis(
    ['main.py'],          # You run Run.py, but PyInstaller builds from main.py
    pathex=[project_root],
    binaries=[],

    datas=[
        # Branding assets
        (assets_path, 'assets/branding'),

        # VLC folder (DLLs + plugins)
        (vlc_path, 'vlc'),

        # OSK PNG + splash screen + any future banners
        (banners_path, 'banners'),
    ],

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
    [],
    exclude_binaries=True,
    name='NovaTurn',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,

    # App icon
    icon=os.path.join(assets_path, "novaturn.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NovaTurn',
)
