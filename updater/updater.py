import os
import subprocess
import shutil
import sys
import tempfile
import zipfile
import requests
import platform

GITHUB_REPO = "https://github.com/username/repo"
ZIP_URL = f"{GITHUB_REPO}/archive/refs/heads/main.zip"
BUILD_MAC_SCRIPT = os.path.join('..', 'build_macos.sh')
BUILD_WIN_SCRIPT = os.path.join('..', 'build_win.bat')

def download_latest_version():
    temp_dir = tempfile.mkdtemp()

    try:
        print("Scaricando l'aggiornamento...")
        response = requests.get(ZIP_URL, stream=True)
        zip_path = os.path.join(temp_dir, "update.zip")
        with open(zip_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)

        print("Estraendo l'aggiornamento...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        return os.path.join(temp_dir, os.listdir(temp_dir)[0])
    except Exception as e:
        print(f"Errore durante l'aggiornamento: {e}")
        return None
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def run_build_script():
    if platform.system() == "Darwin":  # macOS
        command = ["bash", BUILD_MAC_SCRIPT]
    elif platform.system() == "Windows":
        command = ["cmd.exe", "/c", BUILD_WIN_SCRIPT]
    else:
        print(f"Sistema operativo {platform.system()} non supportato.")
        return False

    result = subprocess.run(command)
    return result.returncode == 0

def replace_old_app():
    old_app_path = os.path.join('..', 'VisualexApp.app')
    new_app_path = os.path.join('dist', 'VisualexApp')

    if os.path.exists(old_app_path):
        print("Rimuovendo la vecchia versione dell'app...")
        shutil.rmtree(old_app_path)

    print("Spostando la nuova versione...")
    shutil.move(new_app_path, old_app_path)
    print(f"Aggiornamento completato: {old_app_path}")

def main():
    latest_version_path = download_latest_version()
    if not latest_version_path:
        print("Errore durante il download dell'aggiornamento.")
        return

    print("Eseguendo la build...")
    if run_build_script():
        replace_old_app()
    else:
        print("Errore durante la build.")

if __name__ == "__main__":
    main()
