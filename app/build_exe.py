<<<<<<< HEAD
import os
import sys
import subprocess
import shutil

def ensure_pyinstaller():
    try:
        import PyInstaller  # noqa
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_exe(target_file):
    app_root = os.path.dirname(os.path.abspath(__file__))

    # Clean old build folders
    for folder in ("build", "dist"):
        folder_path = os.path.join(app_root, folder)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

    exe_name = "NovaTurn"

    # Paths INSIDE app/
    branding_src = os.path.join(app_root, "assets", "branding")
    vlc_src = os.path.join(app_root, "vlc")
    icon_path = os.path.join(branding_src, "novaturn.ico")

    # Validate
    if not os.path.exists(icon_path):
        print(f"ERROR: Icon not found: {icon_path}")
        sys.exit(1)

    if not os.path.exists(vlc_src):
        print(f"ERROR: VLC folder not found: {vlc_src}")
        sys.exit(1)

    # Correct Windows add-data syntax (colon)
    add_data_args = [
        "--add-data", f"{branding_src}:assets/branding",
        "--add-data", f"{vlc_src}:vlc"
    ]

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onedir",
        "--noconfirm",
        "--clean",
        "--noconsole",
        "--name", exe_name,
        "--icon", icon_path,
    ] + add_data_args + [target_file]

    print("Running PyInstaller...")
    subprocess.check_call(cmd)

    print("\nBuild complete!")
    print(f"EXE created at: {os.path.join(app_root, 'dist', exe_name + '.exe')}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python build_exe.py main.py")
        sys.exit(1)

    ensure_pyinstaller()
    build_exe(sys.argv[1])


=======
import os
import sys
import subprocess
import shutil

def ensure_pyinstaller():
    try:
        import PyInstaller  # noqa
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_exe(target_file):
    app_root = os.path.dirname(os.path.abspath(__file__))

    # Clean old build folders
    for folder in ("build", "dist"):
        folder_path = os.path.join(app_root, folder)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

    exe_name = "NovaTurn"

    # Paths INSIDE app/
    branding_src = os.path.join(app_root, "assets", "branding")
    vlc_src = os.path.join(app_root, "vlc")
    icon_path = os.path.join(branding_src, "novaturn.ico")

    # Validate
    if not os.path.exists(icon_path):
        print(f"ERROR: Icon not found: {icon_path}")
        sys.exit(1)

    if not os.path.exists(vlc_src):
        print(f"ERROR: VLC folder not found: {vlc_src}")
        sys.exit(1)

    # Correct Windows add-data syntax (colon)
    add_data_args = [
        "--add-data", f"{branding_src}:assets/branding",
        "--add-data", f"{vlc_src}:vlc"
    ]

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onedir",
        "--noconfirm",
        "--clean",
        "--noconsole",
        "--name", exe_name,
        "--icon", icon_path,
    ] + add_data_args + [target_file]

    print("Running PyInstaller...")
    subprocess.check_call(cmd)

    print("\nBuild complete!")
    print(f"EXE created at: {os.path.join(app_root, 'dist', exe_name + '.exe')}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python build_exe.py main.py")
        sys.exit(1)

    ensure_pyinstaller()
    build_exe(sys.argv[1])


>>>>>>> be9547aaccb1857afa059ff99cc82f20dba6ff7b
