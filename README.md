NovaTurn — Premium Media Player for Windows
NovaTurn is a modern, cinematic media player built with Python, PyQt5, and VLC, designed to deliver a polished, re
sponsive, and visually rich experience. It features a custom on-screen keyboard, dynamic UI elements, a powerful me
dia database, and a fully self-contained Windows installer.
NovaTurn is engineered with a professional build pipeline, PyInstaller-safe asset loading, and a frozen folder struc
ture to ensure stability across development, EXE builds, and clean-machine installations.
Features
Code
Audio & Video Playback powered by VLC
Modern UI built with PyQt5
Cinematic design with custom banners, icons, and animations
Mini On-Screen Keyboard (OSK) for touch-friendly input
Media Library with metadata extraction (Mutagen)
Plugin-ready architecture
Password-protected sections
Fully self-contained Windows installer (no Python required)
Project Structure
MicksMediaPlayer/
│
├── Run.py
├── NovaTurn.spec
├── NovaTurnInstaller.iss
│
├── app/
│   ├── main.py
│   ├── ui/
│   ├── banners/
│   ├── assets/
│   │   └── branding/
│   ├── vlc/
│   └── db/
│
├── dist/
├── build/
└── Output/
Rules
All runtime assets live inside app/
All build artifacts (dist/, build/, Output/) live outside app/
Folder names and locations are frozen and must not be changed
    Universal Asset Loader
NovaTurn uses a PyInstaller-safe loader that works in:
Dev mode
EXE mode
Installer mode
Clean machines
python
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), relat
ive_path)
Example usage:
python
resource_path("banners/NovaTurn_OSK.png")
resource_path("assets/branding/novaturn.ico")
resource_path("vlc")
  VLC Integration
NovaTurn bundles a full VLC runtime inside:
Code
app/vlc/
The VLC bootstrap:
Sets PYTHON_VLC_LIB_PATH
Sets VLC_PLUGIN_PATH
Ensures DLLs load correctly on Windows
Works in both dev and EXE mode
This section of the codebase is protected and must not be modified.
  Build Pipeline
1. Clean (optional but recommended)
Delete:
build/
dist/
2. Build the EXE
From the project root:
Code
& "C:\Program Files\Python314\python.exe" -m PyInstaller app\NovaTurn.spec
Output:
Code
dist/NovaTurn/
3. Build the Installer
Open Inno Setup and compile:
Code
NovaTurnInstaller.iss
Output:
Code
Output/NovaTurnSetup.exe
This installer is fully self-contained and works on clean Windows machines.
    Testing Workflow
Test NovaTurn in all environments:
  Dev mode
Code
python Run.py
  EXE mode
Code
dist/NovaTurn/NovaTurn.exe
  Installer mode
Code
Output/NovaTurnSetup.exe
  Clean machine
A Windows machine with:
no Python
no VLC
no dev tools
This confirms the build is fully self-contained.
欄 Contributor Guidelines
Anyone contributing to NovaTurn must follow these rules:
Do not move or rename folders
Do not modify the VLC bootstrap
Do not bypass resource_path()
Do not modify the .spec file
Do not modify installer paths
Do not introduce absolute paths
Do not add assets outside app/
Breaking these rules risks breaking:
EXE builds
installer builds
clean-machine compatibility
  Release Workflow
1st
2ndUpdate version in .iss
3rd
4thClean build
5th
6thBuild EXE
7th
8thBuild installer
9th
10thTest on clean machine
11th
12thArchive installer
13th
14thTag release in GitHub
15th
License
(Add your license here — MIT, GPL, proprietary, etc.)
Credits
NovaTurn is built with:
Python
PyQt5
VLC
Mutagen
Inno Setup
PyInstaller
And a lot of craftsmanship, iteration, and attention to detail
