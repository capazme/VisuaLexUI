# updater.py

import requests
import sys
import os
import shutil
import tempfile
import zipfile
import platform
import subprocess
import logging

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QTextEdit, QMessageBox
)
from PyQt6.QtCore import QMetaObject, Qt
from .helpers import get_resource_path

class ProgressDialog(QDialog):
    update_status_signal = pyqtSignal(str)
    update_progress_signal = pyqtSignal(int)
    log_message_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aggiornamento in Corso")
        self.setModal(True)
        self.layout = QVBoxLayout(self)

        self.status_label = QLabel("Inizializzazione...")
        self.layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.layout.addWidget(self.log_output)

        self.cancel_button = QPushButton("Annulla")
        self.cancel_button.clicked.connect(self.cancel_update)
        self.layout.addWidget(self.cancel_button)

        self.canceled = False

        # Connetti i segnali ai rispettivi slot
        self.update_status_signal.connect(self.update_status)
        self.update_progress_signal.connect(self.update_progress)
        self.log_message_signal.connect(self.append_log_message)

    def cancel_update(self):
        self.canceled = True
        self.close()

    @pyqtSlot(str)
    def update_status(self, message):
        self.status_label.setText(message)

    @pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    @pyqtSlot(str)
    def append_log_message(self, message):
        """Aggiunge un nuovo log all'area di testo."""
        self.log_output.append(message)
        # Scorri automaticamente verso il basso
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())


class UpdateCheckWorker(QObject):
    update_checked = pyqtSignal(bool, str)  # is_newer, latest_version

    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version

    @pyqtSlot()
    def check_for_update(self):
        logging.debug(f"Avvio del controllo aggiornamenti. Versione attuale: {self.current_version}")
        try:
            # URL del tuo file version.txt su GitHub
            version_url = "https://raw.githubusercontent.com/capazme/VisuaLexUI/main/src/visualex_ui/resources/version.txt"
            logging.debug(f"Controllo della versione remota: {version_url}")

            response = requests.get(version_url, timeout=5)
            if response.status_code == 200:
                latest_version = response.text.strip()
                logging.debug(f"Versione remota ottenuta: {latest_version}")
                is_newer = self.is_newer_version(self.current_version, latest_version)
                self.update_checked.emit(is_newer, latest_version)
            else:
                logging.error(f"Errore nel recupero della versione dal server. Codice di stato: {response.status_code}")
                self.update_checked.emit(False, self.current_version)
        except Exception as e:
            logging.error(f"Errore durante il controllo degli aggiornamenti: {e}")
            self.update_checked.emit(False, self.current_version)

    def is_newer_version(self, current_version, latest_version):
        """Confronta le versioni."""
        try:
            logging.debug(f"Confronto delle versioni. Attuale: {current_version}, Remota: {latest_version}")
            def parse_version(v):
                return [int(x) for x in v.split('.')]
            return parse_version(latest_version) > parse_version(current_version)
        except ValueError as e:
            logging.error(f"Errore durante il parsing delle versioni: {e}")
            return False


class UpdateDownloadWorker(QObject):
    update_status_signal = pyqtSignal(str)
    update_progress_signal = pyqtSignal(int)
    log_message_signal = pyqtSignal(str)
    update_completed_signal = pyqtSignal(bool, str)  # Success, message

    def __init__(self, latest_version):
        super().__init__()
        self.latest_version = latest_version
        self.canceled = False

    @pyqtSlot()
    def download_and_update(self):
        try:
            self.update_status_signal.emit("Scaricamento della repository...")
            repo_zip_url = "https://github.com/capazme/VisuaLexUI/archive/refs/heads/main.zip"
            self.log_message_signal.emit(f"Scaricamento della repository da {repo_zip_url}...")

            response = requests.get(repo_zip_url, stream=True)
            total_length = response.headers.get('content-length')

            if response.status_code == 200:
                # Crea una cartella temporanea per scaricare ed estrarre l'archivio
                temp_dir = get_resource_path(tempfile.mkdtemp())
                zip_path = os.path.join(temp_dir, 'repo.zip')
                self.log_message_signal.emit(f"Salvataggio del file ZIP in {zip_path}...")

                with open(zip_path, 'wb') as f:
                    if total_length is None:
                        f.write(response.content)
                    else:
                        dl = 0
                        total_length = int(total_length)
                        for chunk in response.iter_content(chunk_size=8192):
                            if self.canceled:
                                self.log_message_signal.emit("Aggiornamento annullato dall'utente.")
                                self.update_completed_signal.emit(False, "Aggiornamento annullato dall'utente.")
                                return
                            if chunk:
                                f.write(chunk)
                                dl += len(chunk)
                                percent = int((dl / total_length) * 100)
                                self.update_progress_signal.emit(percent)
                                self.log_message_signal.emit(f"Scaricati {dl} di {total_length} byte.")

                self.update_status_signal.emit("Estrazione dei file...")
                self.log_message_signal.emit("Estrazione del file ZIP.")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Percorso della repository estratta
                extracted_repo_path = os.path.join(temp_dir, 'VisuaLexUI-main')
                self.log_message_signal.emit(f"Repository estratta in {extracted_repo_path}.")

                # Rileva il sistema operativo
                current_os = platform.system()
                if current_os == 'Darwin':
                    build_script = 'build_macos.sh'
                else:
                    self.log_message_signal.emit("Sistema operativo non supportato.")
                    self.update_completed_signal.emit(False, "Sistema operativo non supportato.")
                    return

                build_script_path = os.path.join(extracted_repo_path, build_script)
                self.log_message_signal.emit(f"Script di build trovato in {build_script_path}")

                # Assicurati che lo script di build sia eseguibile
                os.chmod(build_script_path, 0o755)

                # Crea una nuova cartella sul desktop dell'utente per l'applicazione aggiornata
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                new_app_folder_name = f"VisualexApp_Update_v{self.latest_version}"
                new_app_folder_path = os.path.join(desktop_path, new_app_folder_name)

                if not os.path.exists(new_app_folder_path):
                    os.makedirs(new_app_folder_path)
                    self.log_message_signal.emit(f"Creata nuova cartella per l'applicazione aggiornata in {new_app_folder_path}")
                else:
                    self.log_message_signal.emit(f"La cartella {new_app_folder_path} esiste già. Utilizzando la cartella esistente.")

                # Copia la repository estratta nella nuova cartella
                shutil.copytree(extracted_repo_path, new_app_folder_path, dirs_exist_ok=True)
                self.log_message_signal.emit(f"Repository copiata in {new_app_folder_path}")

                # Aggiorna lo stato
                self.update_status_signal.emit("Costruzione dell'applicazione...")
                self.log_message_signal.emit("Avvio della build dell'applicazione...")

                # Esegui lo script di build nella nuova cartella
                process = subprocess.Popen(
                    ['bash', build_script],
                    cwd=new_app_folder_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                while True:
                    if self.canceled:
                        process.terminate()
                        self.log_message_signal.emit("Aggiornamento annullato durante la build.")
                        self.update_completed_signal.emit(False, "Aggiornamento annullato dall'utente.")
                        return
                    retcode = process.poll()
                    line = process.stdout.readline()
                    if line:
                        self.log_message_signal.emit(line.strip())
                    if retcode is not None:
                        # Leggi le restanti linee
                        for line in process.stdout:
                            self.log_message_signal.emit(line.strip())
                        break

                stdout, stderr = process.communicate()
                if stderr:
                    self.log_message_signal.emit(f"Errori build: {stderr}")
                    logging.error(f"Errori build: {stderr}")

                if process.returncode != 0:
                    self.log_message_signal.emit(f"Lo script di build ha fallito con codice di ritorno {process.returncode}")
                    self.update_completed_signal.emit(False, f"Lo script di build ha fallito con codice di ritorno {process.returncode}")
                    return

                # Percorso della nuova applicazione costruita
                output_name = f"VisualexApp-v{self.latest_version}.app"
                new_app_path = os.path.join(new_app_folder_path, output_name)
                self.log_message_signal.emit(f"Nuova applicazione costruita in {new_app_path}")

                if os.path.exists(new_app_path):
                    self.update_completed_signal.emit(True, new_app_path)
                    self.log_message_signal.emit("Aggiornamento completato con successo.")
                else:
                    self.log_message_signal.emit("Errore: la nuova applicazione non è stata costruita correttamente.")
                    self.update_completed_signal.emit(False, "La nuova applicazione non è stata costruita correttamente.")

            else:
                self.log_message_signal.emit(f"Errore nel download della repository: {response.status_code}")
                self.update_completed_signal.emit(False, "Errore nel download della repository.")

        except Exception as e:
            logging.error(f"Errore durante l'aggiornamento: {e}", exc_info=True)
            self.log_message_signal.emit(f"Errore durante l'aggiornamento: {e}")
            self.update_completed_signal.emit(False, f"Errore durante l'aggiornamento: {e}")

    def cancel(self):
        self.canceled = True

class UpdateNotifier(QObject):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.latest_version = None
        self.update_thread = None  # Thread per il controllo degli aggiornamenti
        self.download_thread = None  # Thread per il download e l'aggiornamento

    def check_for_update(self, current_version):
        """Avvia un thread per controllare gli aggiornamenti."""
        if self.update_thread is not None and self.update_thread.isRunning():
            logging.warning("Controllo aggiornamenti già in esecuzione.")
            return

        self.update_worker = UpdateCheckWorker(current_version)
        self.update_worker.update_checked.connect(self.on_update_checked, Qt.ConnectionType.QueuedConnection)

        self.update_thread = QThread()
        self.update_worker.moveToThread(self.update_thread)

        self.update_thread.finished.connect(self.update_thread.deleteLater)
        self.update_thread.started.connect(self.update_worker.check_for_update)
        self.update_thread.start()





    @pyqtSlot(bool, str)
    def on_update_checked(self, is_newer, latest_version):
        self.latest_version = latest_version
        logging.debug(f"on_update_checked: self.latest_version impostato a {self.latest_version}")
        self.update_thread.quit()
        self.update_thread.wait()

        if is_newer:
            logging.info(f"Trovata nuova versione: {latest_version}. Avvio del processo di aggiornamento.")
            self.prompt_update()
        else:
            logging.info("L'applicazione è già aggiornata.")
            QMetaObject.invokeMethod(self.parent, "show_no_update_message", Qt.ConnectionType.QueuedConnection)


    @pyqtSlot()
    def prompt_update(self):
        logging.debug(f"prompt_update: self.latest_version è {self.latest_version}")

        reply = QMessageBox.question(
            self.parent,
            "Aggiornamento Disponibile",
            f"È disponibile una nuova versione ({self.latest_version}). Vuoi aggiornare?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            logging.info("L'utente ha accettato l'aggiornamento.")
            self.download_and_update()
        else:
            logging.info("L'utente ha rifiutato l'aggiornamento.")

    def download_and_update(self):
        self.progress_dialog = ProgressDialog(self.parent)
        self.progress_dialog.show()

        self.download_worker = UpdateDownloadWorker(self.latest_version)
        self.download_worker.update_status_signal.connect(self.progress_dialog.update_status_signal)
        self.download_worker.update_progress_signal.connect(self.progress_dialog.update_progress_signal)
        self.download_worker.log_message_signal.connect(self.progress_dialog.log_message_signal)
        self.download_worker.update_completed_signal.connect(self.on_update_completed)
        self.progress_dialog.cancel_button.clicked.connect(self.download_worker.cancel)

        self.download_thread = QThread()
        self.download_worker.moveToThread(self.download_thread)

        self.download_thread.started.connect(self.download_worker.download_and_update)
        self.download_thread.start()

    @pyqtSlot(bool, str)
    def on_update_completed(self, success, message):
        self.download_thread.quit()
        self.download_thread.wait()
        self.progress_dialog.close()
        if success:
            QMessageBox.information(
                self.parent,
                "Aggiornamento Completato",
                f"L'applicazione è stata aggiornata ed è disponibile in:\n{message}\n\n"
                "Per favore, sostituisci manualmente la tua applicazione esistente con la nuova versione."
            )
            logging.info("Aggiornamento completato con successo.")
            # Apri la cartella contenente la nuova applicazione
            subprocess.Popen(['open', os.path.dirname(message)])
        else:
            QMessageBox.warning(self.parent, "Aggiornamento Fallito", message)
            logging.error(f"Aggiornamento fallito: {message}")
