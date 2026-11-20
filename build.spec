# -*- mode: python ; coding: utf-8 -*-
import os
import customtkinter
from PyInstaller.utils.hooks import collect_submodules

ctk_dir = os.path.dirname(customtkinter.__file__)

datas = [
    ("assets/golden_cookie.png", "assets"),
    (os.path.join(ctk_dir, "assets"), "customtkinter/assets"),
]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=collect_submodules("customtkinter"),
    hookspath=[],
    runtime_hooks=[],
    excludes=["matplotlib", "scipy", "pandas", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name="GoldenCookieCatcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="icon.ico",
    version="version_info.txt",
    manifest="app.manifest",
)