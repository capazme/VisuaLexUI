# updater.py

import requests
import threading
import sys
import os
import shutil
import tempfile
import zipfile
import platform
import subprocess
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal
import logging

class UpdateNotifier(QObject):
    update_available = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.latest_version = None

    def check_for_update(self, current_version):
        """Controlla se è disponibile un aggiornamento confrontando versioni locali e remote."""
        def _check():
            try:
                # URL del tuo file version.txt su GitHub (modifica con il tuo repository)
                version_url = "https://raw.githubusercontent.com/tuo_username/tuo_repository/main/src/visualex_ui/resources/version.txt"

                response = requests.get(version_url, timeout=5)
                if response.status_code == 200:
                    self.latest_version = response.text.strip()
                    if self.is_newer_version(current_version, self.latest_version):
                        self.update_available.emit(self.latest_version)
                else:
                    logging.error("Impossibile ottenere la versione dal server.")
            except Exception as e:
                logging.error(f"Errore durante il controllo degli aggiornamenti: {e}")

        threading.Thread(target=_check).start()

    def is_newer_version(self, current_version, latest_version):
        """Confronta le versioni."""
        def parse_version(v):
            return [int(x) for x in v.split('.')]
        try:
            return parse_version(latest_version) > parse_version(current_version)
        except ValueError:
            return False  # Se le versioni non possono essere analizzate, assume che non ci siano aggiornamenti

    def prompt_update(self):
        """Chiede all'utente se desidera aggiornare."""
        reply = QMessageBox.question(
            self.parent,
            "Aggiornamento Disponibile",
            f"È disponibile una nuova versione ({self.latest_version}). Vuoi aggiornare?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.download_and_update()

    def download_and_update(self):
        """Scarica la repository ed esegue lo script di build."""
        try:
            # URL per scaricare l'archivio ZIP della repository
            repo_zip_url = "https://github.com/tuo_username/tuo_repository/archive/refs/heads/main.zip"

            response = requests.get(repo_zip_url, stream=True)
            if response.status_code == 200:
                # Salva il file ZIP in una directory temporanea
                temp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(temp_dir, 'repo.zip')
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # Estrai il file ZIP
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Percorso della repository estratta
                extracted_repo_path = os.path.join(temp_dir, 'tuo_repository-main')  # Modifica se necessario

                # Rileva il sistema operativo
                current_os = platform.system()
                if current_os == 'Darwin':  # macOS
                    build_script = 'build_macos.sh'
                    shell = True
                elif current_os == 'Windows':
                    QMessageBox.warning(self.parent, "Sistema Operativo Non Supportato", "Il tuo sistema operativo non è supportato per gli aggiornamenti automatici.")
                    return
                else:
                    QMessageBox.warning(self.parent, "Sistema Operativo Non Supportato", "Il tuo sistema operativo non è supportato per gli aggiornamenti automatici.")
                    return

                # Percorso dello script di build
                build_script_path = os.path.join(extracted_repo_path, build_script)

                # Assicurati che lo script di build sia eseguibile
                os.chmod(build_script_path, 0o755)

                # Informa l'utente che l'aggiornamento sta per iniziare
                QMessageBox.information(self.parent, "Aggiornamento in Corso", "L'applicazione si aggiornerà ora. Attendi il completamento dell'operazione...")

                # Esegui lo script di build
                process = subprocess.Popen(['bash', build_script_path], cwd=extracted_repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Attendi il completamento della build
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    logging.error(f"Lo script di build ha fallito con errore: {stderr.decode()}")
                    QMessageBox.warning(self.parent, "Aggiornamento Fallito", "Il processo di aggiornamento è fallito. Per favore, riprova.")
                    return

                # Percorso della nuova applicazione costruita
                version = self.latest_version
                output_name = f"VisualexApp-v{version}.app"
                new_app_path = os.path.join(extracted_repo_path, output_name)

                # Verifica che la nuova app esista
                if not os.path.exists(new_app_path):
                    QMessageBox.warning(self.parent, "Aggiornamento Fallito", "La nuova applicazione non è stata costruita correttamente.")
                    return

                # Percorso dell'applicazione corrente
                current_app_path = os.path.abspath(sys.argv[0])
                current_app_dir = os.path.dirname(current_app_path)
                current_app_bundle = os.path.abspath(os.path.join(current_app_dir, '..', '..', '..'))

                # Sostituisci l'applicazione vecchia con la nuova
                try:
                    # Rinomina l'applicazione corrente per effettuare un backup
                    backup_app_bundle = current_app_bundle + "_backup"
                    if os.path.exists(backup_app_bundle):
                        shutil.rmtree(backup_app_bundle)
                    os.rename(current_app_bundle, backup_app_bundle)

                    # Sposta la nuova app nella posizione dell'app corrente
                    shutil.move(new_app_path, current_app_bundle)

                    # Rimuovi il backup
                    shutil.rmtree(backup_app_bundle)
                except Exception as e:
                    logging.error(f"Errore durante la sostituzione dell'applicazione: {e}")
                    QMessageBox.warning(self.parent, "Aggiornamento Fallito", "Non è stato possibile sostituire l'applicazione esistente.")
                    # Ripristina l'applicazione originale
                    if os.path.exists(backup_app_bundle):
                        os.rename(backup_app_bundle, current_app_bundle)
                    return

                # Informa l'utente e riavvia l'applicazione
                QMessageBox.information(self.parent, "Aggiornamento Completato", "L'applicazione è stata aggiornata e verrà riavviata.")
                self.restart_application(current_app_bundle)

            else:
                QMessageBox.warning(self.parent, "Errore di Download", "Impossibile scaricare l'aggiornamento.")
        except Exception as e:
            logging.error(f"Errore durante l'aggiornamento: {e}")
            QMessageBox.warning(self.parent, "Errore", "Si è verificato un errore durante l'aggiornamento.")

    def restart_application(self, app_bundle_path):
        """Riavvia l'applicazione aggiornata."""
        try:
            subprocess.Popen(['open', app_bundle_path])
            sys.exit()
        except Exception as e:
            logging.error(f"Errore durante il riavvio dell'applicazione: {e}")
            QMessageBox.warning(self.parent, "Errore", "Si è verificato un errore durante il riavvio dell'applicazione.")
