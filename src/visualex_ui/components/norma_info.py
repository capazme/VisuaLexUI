# visualex_ui/components/norma_info.py
from PyQt6.QtWidgets import QGroupBox, QFormLayout, QLabel, QPushButton, QApplication, QMessageBox
from PyQt6.QtCore import Qt

class NormaInfoSection(QGroupBox):
    def __init__(self, parent):
        super().__init__("Informazioni sulla Norma", parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        # Etichette per mostrare le informazioni sulla norma
        self.urn_label = QLabel()
        self.urn_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.urn_label.setOpenExternalLinks(True)  # Permette di cliccare sui link se presenti
        
        self.tipo_atto_label = QLabel()
        self.data_label = QLabel()
        self.numero_atto_label = QLabel()

        # Aggiunta delle etichette al layout
        layout.addRow("URN:", self.urn_label)
        layout.addRow("Tipo di Atto:", self.tipo_atto_label)
        layout.addRow("Data:", self.data_label)
        layout.addRow("Numero Atto:", self.numero_atto_label)

        # Pulsante per copiare tutte le informazioni visualizzate
        self.copy_info_button = QPushButton("Copia Informazioni")
        self.copy_info_button.setToolTip("Copia tutte le informazioni visualizzate negli appunti.")
        self.copy_info_button.clicked.connect(self.copy_all_norma_info)
        layout.addRow(self.copy_info_button)

        self.setLayout(layout)

    def update_info(self, normavisitata):
        """
        Metodo per aggiornare le informazioni della norma visualizzate nella sezione.
        """
        if not normavisitata:
            # Gestisci il caso in cui non ci sono dati da mostrare
            self.clear_info()
            return

        # Popola le etichette con le informazioni della norma
        self.urn_label.setText(f'<a href="{normavisitata.urn}">{normavisitata.urn}</a>')
        self.tipo_atto_label.setText(normavisitata.norma.tipo_atto_str)
        self.data_label.setText(normavisitata.norma.data)
        self.numero_atto_label.setText(normavisitata.norma.numero_atto)

    def clear_info(self):
        """
        Metodo per pulire le informazioni visualizzate.
        """
        self.urn_label.clear()
        self.tipo_atto_label.clear()
        self.data_label.clear()
        self.numero_atto_label.clear()

    def copy_all_norma_info(self):
        """
        Copia tutte le informazioni della norma negli appunti.
        """
        info = []

        if self.urn_label.text():
            info.append(f"URN: {self.urn_label.text()}")
        if self.tipo_atto_label.text():
            info.append(f"Tipo di Atto: {self.tipo_atto_label.text()}")
        if self.data_label.text():
            info.append(f"Data: {self.data_label.text()}")
        if self.numero_atto_label.text():
            info.append(f"Numero Atto: {self.numero_atto_label.text()}")

        # Copia negli appunti
        clipboard = self.parent.clipboard()
        clipboard.setText("\n".join(info))

        # Mostra notifica
        self.parent.show_message("Informazione Copiata", "Tutte le informazioni visualizzate sono state copiate negli appunti.")

    def clipboard(self):
        """Ritorna l'oggetto clipboard dell'applicazione."""
        return QApplication.clipboard()

    def show_message(self, title, message):
        """Mostra un messaggio popup con il titolo e il messaggio forniti."""
        QMessageBox.information(self, title, message)