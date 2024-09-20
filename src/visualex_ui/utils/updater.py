import requests
import os
from PyQt6.QtWidgets import QMessageBox, QSystemTrayIcon, QMenu, QAction
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

class UpdateNotifier:
    GITHUB_REPO = "https://github.com/username/repo"
    VERSION_FILE_URL = f"{GITHUB_REPO}/raw/main/src/visualex_ui/resources/version.txt"
    
    def __init__(self, parent, version_icon=None):
        self.parent = parent  # Riferimento alla finestra principale
        self.version_icon = version_icon  # Riferimento all'icona grafica per notificare l'aggiornamento

    def check_for_update(self, local_version):
        """
        Controlla la versione remota e notifica l'utente se c'è un aggiornamento disponibile.
        """
        remote_version = self.get_remote_version()
        if remote_version and self.is_newer_version(local_version, remote_version):
            self.notify_user(remote_version)
            if self.version_icon:
                self.version_icon.setToolTip(f"Aggiornamento disponibile: {remote_version}")
                self.version_icon.setVisible(True)
        else:
            if self.version_icon:
                self.version_icon.setVisible(False)

    def get_remote_version(self):
        """
        Recupera la versione remota dal file version.txt su GitHub.
        """
        try:
            response = requests.get(self.VERSION_FILE_URL)
            if response.status_code == 200:
                return response.text.strip()
            else:
                print(f"Errore nel recuperare la versione remota: {response.status_code}")
                return None
        except Exception as e:
            print(f"Errore durante la richiesta HTTP: {e}")
            return None

    def is_newer_version(self, local_version, remote_version):
        """
        Confronta due versioni nel formato major.minor.patch.
        Ritorna True se la versione remota è più recente.
        """
        local_parts = list(map(int, local_version.split('.')))
        remote_parts = list(map(int, remote_version.split('.')))

        for local_part, remote_part in zip(local_parts, remote_parts):
            if remote_part > local_part:
                return True
            elif local_part > remote_part:
                return False

        return len(remote_parts) > len(local_parts)

    def notify_user(self, remote_version):
        """
        Notifica l'utente della disponibilità di un aggiornamento.
        """
        msg = QMessageBox(self.parent)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(f"È disponibile una nuova versione ({remote_version}).")
        msg.setInformativeText("Si desidera aggiornare ora?")
        msg.setWindowTitle("Aggiornamento Disponibile")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        result = msg.exec()

        if result == QMessageBox.StandardButton.Yes:
            self.launch_external_updater()

    def launch_external_updater(self):
        """
        Lancia il processo di aggiornamento esterno (update.py).
        """
        update_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'update', 'update.py')
        if os.path.exists(update_script):
            os.system(f'python {update_script}')
        else:
            print("Script di aggiornamento non trovato.")
