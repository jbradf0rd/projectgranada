# -*- mode: python ; coding: utf-8 -*-
"""
Granada - Offline Arabic Book Search Engine
PyInstaller Specification File

Build command:
    pyinstaller granada.spec

Output will be in dist/granada/
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Get the directory containing this spec file
spec_dir = os.path.dirname(os.path.abspath(SPEC))

# Collect all data files
datas = [
    # Templates
    (os.path.join(spec_dir, 'templates'), 'templates'),
    # Static files (CSS, JS, fonts)
    (os.path.join(spec_dir, 'static'), 'static'),
    # README for users
    (os.path.join(spec_dir, 'README.md'), '.'),
    # Note: Do NOT bundle the data directory - it contains user data
    # The app will create it on first run
]

# Include bundled books (Quran + Riyadh al-Salihin)
bundled_books_dir = os.path.join(spec_dir, 'bundled_books')
if os.path.exists(bundled_books_dir) and os.listdir(bundled_books_dir):
    datas.append((bundled_books_dir, 'bundled_books'))

# Hidden imports that PyInstaller might miss
hidden_imports = [
    'flask',
    'flask.json',
    'jinja2',
    'markupsafe',
    'werkzeug',
    'werkzeug.routing',
    'werkzeug.utils',
    'sqlite3',
    'json',
    'urllib.request',
    'urllib.parse',
    'http.client',
    'ssl',
    'certifi',
    'requests',
    'pyarabic',
    'pyarabic.araby',
    'pyarabic.normalize',
    'unicodedata',
    're',
    'datetime',
    'pathlib',
    'threading',
    'queue',
    'logging',
    'logging.handlers',
    'webbrowser',
    'tkinter',
    'tkinter.filedialog',
]

a = Analysis(
    ['app.py'],
    pathex=[spec_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        # Note: tkinter is REQUIRED for file dialogs - do not exclude
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'test',
        'tests',
        'unittest',
        'pytest',
        'setuptools',
        'pip',
        'wheel',
        'distutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='granada',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Use UPX compression if available
    console=False,  # Windowed app (no console)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(spec_dir, 'static', 'icons', 'granada.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='granada',
)
