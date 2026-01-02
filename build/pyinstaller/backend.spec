# -*- mode: python ; coding: utf-8 -*-
# ETL Dashboard Backend - PyInstaller Spec

import sys
from pathlib import Path

block_cipher = None

# Paths
ROOT = Path(SPECPATH).parent.parent
BACKEND = ROOT / 'backend'
PYTHON = ROOT / 'python'

a = Analysis(
    [str(BACKEND / 'app.py')],
    pathex=[str(BACKEND), str(PYTHON)],
    binaries=[],
    datas=[
        (str(PYTHON / 'modules'), 'modules'),
    ],
    hiddenimports=[
        # Uvicorn
        'uvicorn.logging',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        # FastAPI
        'fastapi',
        'starlette',
        'pydantic',
        # Selenium
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        # Data processing
        'pandas',
        'openpyxl',
        'xlrd',
        # Database
        'sqlite3',
        # Others
        'json',
        'logging',
        'asyncio',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PIL',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
    ],
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
    name='etl_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=str(ROOT / 'scripts' / 'icon.ico') if (ROOT / 'scripts' / 'icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='backend',
)
