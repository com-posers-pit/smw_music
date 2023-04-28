# SPDX-FileCopyrightText: 2023 The SMW Music Python Project Authors
# <https://github.com/com-posers-pit/smw_music/blob/develop/AUTHORS.rst>
#
# SPDX-License-Identifier: CC0-1.0


block_cipher = None


a = Analysis(
    ['smw_music/scripts/dashboard.py'],
    pathex=[],
    binaries=[],
    datas=[('smw_music/data/mml.txt', 'smw_music/data'), ('smw_music/data/dashboard.ui', 'smw_music/data'), ('smw_music/data/ashtley.gif', 'smw_music/data'), ('smw_music/data/maestro.svg', 'smw_music/data'), ('smw_music/data/convert.bat', 'smw_music/data'), ('smw_music/data/convert.sh', 'smw_music/data'), ('smw_music/data/preferences.ui', 'smw_music/data')],
    hiddenimports=['music21.alpha', 'music21.audioSearch', 'music21.configure', 'qdarkstyle'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tk', 'matplotlib'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='dashboard',
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
    icon='resources/maestro.ico'
)
