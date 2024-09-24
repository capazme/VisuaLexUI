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
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
import logging

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton

class ProgressDialog(QDialog):
    update_status_signal = pyqtSignal(str)
    update_progress_signal = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aggiornamento in Corso")
        self.setModal(True)
        self.layout = QVBoxLayout()

        self.status_label = QLabel("Inizializzazione...")
        self.layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.layout.addWidget(self.progress_bar)

        self.cancel_button = QPushButton("Annulla")
        self.cancel_button.clicked.connect(self.cancel_update)
        self.layout.addWidget(self.cancel_button)

        self.setLayout(self.layout)
        self.canceled = False

        # Connetti i segnali ai rispettivi slot
        self.update_status_signal.connect(self.update_status)
        self.update_progress_signal.connect(self.update_progress)

    def cancel_update(self):
        self.canceled = True
        self.close()

    @pyqtSlot(str)
    def update_status(self, message):
        self.status_label.setText(message)

    @pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)

class UpdateNotifier(QObject):
    update_available = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.latest_version = None

    def check_for_update(self, current_version):
        """Controlla se è disponibile un aggiornamento confrontando versioni locali e remote."""
        logging.debug(f"Avvio del controllo aggiornamenti. Versione attuale: {current_version}")
        
        def _check():
            try:
                # URL del tuo file version.txt su GitHub (modifica con il tuo repository)
                version_url = "https://raw.githubusercontent.com/capazme/VisuaLexUI/main/src/visualex_ui/resources/version.txt"
                logging.debug(f"Controllo della versione remota: {version_url}")

                response = requests.get(version_url, timeout=5)
                if response.status_code == 200:
                    self.latest_version = response.text.strip()
                    logging.debug(f"Versione remota ottenuta: {self.latest_version}")
                    if self.is_newer_version(current_version, self.latest_version):
                        logging.info(f"È disponibile una nuova versione: {self.latest_version}")
                        self.update_available.emit(self.latest_version)
                    else:
                        logging.info("Nessun aggiornamento disponibile. La versione attuale è la più recente.")
                else:
                    logging.error(f"Errore nel recupero della versione dal server. Codice di stato: {response.status_code}")
            except Exception as e:
                logging.error(f"Errore durante il controllo degli aggiornamenti: {e}")

        threading.Thread(target=_check).start()

    def is_newer_version(self, current_version, latest_version):
        """Confronta le versioni."""
        try:
            logging.debug(f"Confronto delle versioni. Attuale: {current_version}, Remota: {latest_version}")
            def parse_version(v):
                return [int(x) for x in v.split('.')]
            return parse_version(latest_version) > parse_version(current_version)
        except ValueError as e:
            logging.error(f"Errore durante il parsing delle versioni: {e}")
            return False  # Se le versioni non possono essere analizzate, assume che non ci siano aggiornamenti

    @pyqtSlot()
    def prompt_update(self):
        """Chiede all'utente se desidera aggiornare."""
        logging.debug("Richiesta di conferma per aggiornamento.")
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
        """Scarica la repository ed esegue lo script di build in un ambiente sicuro."""
        # Crea il dialogo di progresso
        self.progress_dialog = ProgressDialog(self.parent)
        self.progress_dialog.show()

        def _update():
            try:
                # Controlla se l'operazione è stata annullata
                if self.progress_dialog.canceled:
                    logging.info("Aggiornamento annullato dall'utente.")
                    return

                # Aggiorna lo stato
                self.progress_dialog.update_status_signal.emit("Scaricamento della repository...")
                # URL per scaricare l'archivio ZIP della repository
                repo_zip_url = "https://github.com/capazme/VisuaLexUI/archive/refs/heads/main.zip"
                logging.debug(f"Scaricamento della repository: {repo_zip_url}")

                response = requests.get(repo_zip_url, stream=True)
                total_length = response.headers.get('content-length')

                if response.status_code == 200:
                    # Salva il file ZIP in una directory temporanea
                    temp_dir = tempfile.mkdtemp()
                    zip_path = os.path.join(temp_dir, 'repo.zip')
                    logging.debug(f"Salvataggio del file ZIP in {zip_path}")

                    with open(zip_path, 'wb') as f:
                        if total_length is None:
                            f.write(response.content)
                        else:
                            dl = 0
                            total_length = int(total_length)
                            for chunk in response.iter_content(chunk_size=8192):
                                if self.progress_dialog.canceled:
                                    logging.info("Aggiornamento annullato dall'utente durante il download.")
                                    return
                                if chunk:
                                    f.write(chunk)
                                    dl += len(chunk)
                                    done = int(50 * dl / total_length)
                                    percent = int((dl / total_length) * 100)
                                    self.progress_dialog.update_progress_signal.emit(percent)
                    logging.debug("Download completato.")

                    # Aggiorna lo stato
                    self.progress_dialog.update_status_signal.emit("Estrazione dei file...")
                    # Estrai il file ZIP
                    logging.debug("Estrazione del file ZIP.")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)

                    # Percorso della repository estratta
                    extracted_repo_path = os.path.join(temp_dir, 'VisuaLexUI-main')  # Modifica se necessario
                    logging.debug(f"Repository estratta in {extracted_repo_path}")

                    # Rileva il sistema operativo
                    current_os = platform.system()
                    logging.debug(f"Sistema operativo rilevato: {current_os}")
                    if current_os == 'Darwin':  # macOS
                        build_script = 'build_macos.sh'
                    elif current_os == 'Windows':
                        logging.warning("Aggiornamento non supportato su Windows.")
                        QMessageBox.warning(self.parent, "Sistema Operativo Non Supportato", "Il tuo sistema operativo non è supportato per gli aggiornamenti automatici.")
                        return
                    else:
                        logging.warning("Aggiornamento non supportato su questo sistema operativo.")
                        QMessageBox.warning(self.parent, "Sistema Operativo Non Supportato", "Il tuo sistema operativo non è supportato per gli aggiornamenti automatici.")
                        return

                    # Percorso dello script di build
                    build_script_path = os.path.join(extracted_repo_path, build_script)
                    logging.debug(f"Script di build trovato in {build_script_path}")

                    # Assicurati che lo script di build sia eseguibile
                    os.chmod(build_script_path, 0o755)

                    # Aggiorna lo stato
                    self.progress_dialog.update_status_signal.emit("Costruzione dell'applicazione...")

                    # Esegui lo script di build nella nuova cartella
                    logging.info(f"Esecuzione dello script di build: {build_script_path}")
                    process = subprocess.Popen(['bash', build_script_path], cwd=extracted_repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    # Monitorare l'avanzamento della build
                    while True:
                        if self.progress_dialog.canceled:
                            logging.info("Aggiornamento annullato dall'utente durante la build.")
                            process.terminate()
                            return
                        retcode = process.poll()
                        line = process.stdout.readline()
                        if line:
                            logging.debug(line.decode().strip())
                            # Puoi aggiungere logica per aggiornare la barra di progresso qui se possibile
                        if retcode is not None:
                            break

                    stdout, stderr = process.communicate()
                    logging.debug(f"Output build: {stdout.decode()}")
                    if stderr:
                        logging.error(f"Errori build: {stderr.decode()}")

                    if process.returncode != 0:
                        logging.error(f"Lo script di build ha fallito con errore: {stderr.decode()}")
                        QMessageBox.warning(self.parent, "Aggiornamento Fallito", "Il processo di aggiornamento è fallito. Per favore, riprova.")
                        return

                    # Percorso della nuova applicazione costruita
                    version = self.latest_version
                    output_name = f"VisualexApp-v{version}.app"
                    new_app_path = os.path.join(extracted_repo_path, 'dist', output_name)  # Assumendo che l'app sia nella cartella 'dist'
                    logging.debug(f"Nuova applicazione costruita in {new_app_path}")

                    # Verifica che la nuova app esista
                    if not os.path.exists(new_app_path):
                        logging.error(f"La nuova applicazione non è stata trovata in {new_app_path}")
                        QMessageBox.warning(self.parent, "Aggiornamento Fallito", "La nuova applicazione non è stata costruita correttamente.")
                        return

                    # Aggiorna lo stato
                    self.progress_dialog.update_status_signal.emit("Completato!")

                    # Chiudi la finestra di progresso
                    self.progress_dialog.close()

                    # Informa l'utente che la nuova applicazione è pronta
                    QMessageBox.information(
                        self.parent, 
                        "Aggiornamento Completato", 
                        f"L'applicazione è stata aggiornata ed è disponibile nella cartella:\n{extracted_repo_path}\n\n"
                        "Per favore, sostituisci manualmente la tua applicazione esistente con la nuova versione."
                    )
                    logging.info("Aggiornamento completato. L'applicazione aggiornata è disponibile per l'utente.")

                    # Opzionalmente, apri la cartella per l'utente
                    subprocess.Popen(['open', extracted_repo_path])

                else:
                    logging.error(f"Errore di download della repository. Codice di stato: {response.status_code}")
                    QMessageBox.warning(self.parent, "Errore di Download", "Impossibile scaricare l'aggiornamento.")

            except Exception as e:
                logging.error(f"Errore durante l'aggiornamento: {e}")
                self.progress_dialog.close()
                QMessageBox.warning(self.parent, "Errore", f"Si è verificato un errore durante l'aggiornamento: {e}")

        # Esegui l'aggiornamento in un thread separato
        threading.Thread(target=_update).start()
    
    def restart_application(self, app_bundle_path):
        """Riavvia l'applicazione aggiornata."""
        try:
            logging.info(f"Riavvio dell'applicazione da {app_bundle_path}")
            subprocess.Popen(['open', app_bundle_path])
            sys.exit()
        except Exception as e:
            logging.error(f"Errore durante il riavvio dell'applicazione: {e}")
            QMessageBox.warning(self.parent, "Errore", "Si è verificato un errore durante il riavvio dell'applicazione.")
