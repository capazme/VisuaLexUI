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
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import logging

class UpdateNotifier(QObject):
    update_available = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.latest_version = None
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
        """Scarica la repository ed esegue lo script di build."""
        try:
            # URL per scaricare l'archivio ZIP della repository
            repo_zip_url = "https://github.com/capazme/VisuaLexUI/archive/refs/heads/main.zip"
            logging.debug(f"Scaricamento della repository: {repo_zip_url}")

            response = requests.get(repo_zip_url, stream=True)
            if response.status_code == 200:
                # Salva il file ZIP in una directory temporanea
                temp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(temp_dir, 'repo.zip')
                logging.debug(f"Salvataggio del file ZIP in {zip_path}")
                
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
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
                    shell = True
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

                # Informa l'utente che l'aggiornamento sta per iniziare
                QMessageBox.information(self.parent, "Aggiornamento in Corso", "L'applicazione si aggiornerà ora. Attendi il completamento dell'operazione...")

                # Esegui lo script di build
                logging.info(f"Esecuzione dello script di build: {build_script_path}")
                process = subprocess.Popen(['bash', build_script_path], cwd=extracted_repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Attendi il completamento della build
                stdout, stderr = process.communicate()
                logging.debug(f"Output build: {stdout.decode()}")
                logging.error(f"Errori build: {stderr.decode()}")

                if process.returncode != 0:
                    logging.error(f"Lo script di build ha fallito con errore: {stderr.decode()}")
                    QMessageBox.warning(self.parent, "Aggiornamento Fallito", "Il processo di aggiornamento è fallito. Per favore, riprova.")
                    return

                # Percorso della nuova applicazione costruita
                version = self.latest_version
                output_name = f"VisualexApp-v{version}.app"
                new_app_path = os.path.join(extracted_repo_path, output_name)
                logging.debug(f"Nuova applicazione costruita in {new_app_path}")

                # Verifica che la nuova app esista
                if not os.path.exists(new_app_path):
                    logging.error(f"La nuova applicazione non è stata trovata in {new_app_path}")
                    QMessageBox.warning(self.parent, "Aggiornamento Fallito", "La nuova applicazione non è stata costruita correttamente.")
                    return

                # Percorso dell'applicazione corrente
                current_app_path = os.path.abspath(sys.argv[0])
                current_app_dir = os.path.dirname(current_app_path)
                current_app_bundle = os.path.abspath(os.path.join(current_app_dir, '..', '..', '..'))
                logging.debug(f"Percorso dell'applicazione corrente: {current_app_bundle}")

                # Sostituisci l'applicazione vecchia con la nuova
                try:
                    # Rinomina l'applicazione corrente per effettuare un backup
                    backup_app_bundle = current_app_bundle + "_backup"
                    if os.path.exists(backup_app_bundle):
                        logging.debug(f"Rimozione del vecchio backup: {backup_app_bundle}")
                        shutil.rmtree(backup_app_bundle)
                    os.rename(current_app_bundle, backup_app_bundle)
                    logging.debug(f"Backup dell'applicazione corrente completato: {backup_app_bundle}")

                    # Sposta la nuova app nella posizione dell'app corrente
                    shutil.move(new_app_path, current_app_bundle)
                    logging.debug(f"Spostamento della nuova applicazione in {current_app_bundle}")

                    # Rimuovi il backup
                    shutil.rmtree(backup_app_bundle)
                    logging.debug(f"Backup rimosso: {backup_app_bundle}")
                except Exception as e:
                    logging.error(f"Errore durante la sostituzione dell'applicazione: {e}")
                    QMessageBox.warning(self.parent, "Aggiornamento Fallito", "Non è stato possibile sostituire l'applicazione esistente.")
                    # Ripristina l'applicazione originale
                    if os.path.exists(backup_app_bundle):
                        os.rename(backup_app_bundle, current_app_bundle)
                    return

                # Informa l'utente e riavvia l'applicazione
                QMessageBox.information(self.parent, "Aggiornamento Completato", "L'applicazione è stata aggiornata e verrà riavviata.")
                logging.info("Aggiornamento completato. Riavvio dell'applicazione.")
                self.restart_application(current_app_bundle)

            else:
                logging.error(f"Errore di download della repository. Codice di stato: {response.status_code}")
                QMessageBox.warning(self.parent, "Errore di Download", "Impossibile scaricare l'aggiornamento.")
        except Exception as e:
            logging.error(f"Errore durante l'aggiornamento: {e}")
            QMessageBox.warning(self.parent, "Errore", "Si è verificato un errore durante l'aggiornamento.")

    def restart_application(self, app_bundle_path):
        """Riavvia l'applicazione aggiornata."""
        try:
            logging.info(f"Riavvio dell'applicazione da {app_bundle_path}")
            subprocess.Popen(['open', app_bundle_path])
            sys.exit()
        except Exception as e:
            logging.error(f"Errore durante il riavvio dell'applicazione: {e}")
            QMessageBox.warning(self.parent, "Errore", "Si è verificato un errore durante il riavvio dell'applicazione.")
