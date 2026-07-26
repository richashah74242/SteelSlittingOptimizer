from PyInstaller.__main__ import run

run([
    "backend/main.py",
    "--name=steel-slitting-backend",
    "--onefile",
    "--clean",
    "--paths=.",
])