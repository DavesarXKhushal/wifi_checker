from setuptools import setup

APP = ['WifiSpeedCheckerMac.py']
OPTIONS = {
    'argv_emulation': True,
    'packages': ['matplotlib', 'customtkinter', 'speedtest', 'plyer'],
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
