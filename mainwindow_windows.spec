# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['mainwindow.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('loading-snake-io.gif', '.'),
        ('form_pl.qm', '.'),
        ('form_en.qm', '.'),
        ('windrivers\\slabvcp.inf', '.'),
        ('windrivers\\slabvcp.cat', '.'),
        ('windrivers\\dpinst.xml', '.'),
        ('windrivers\\CP210xVCPInstaller_x64.exe', '.'),
        ('windrivers\\silabser.sys', '.'),
        ('windrivers\\WdfCoInstaller01009.dll', '.'),
        ('windrivers\\WdfCoInstaller01011.dll', '.'),
        ('windrivers\\SLAB_License_Agreement_VCP_Windows.txt', '.'),
    ],
    hiddenimports=[
        'serial',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'winrt.windows.foundation',
        'winrt.windows.foundation.collections',
    ],
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
    name='StiCAN_Configurator',
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
    icon=['icon.ico'],
)