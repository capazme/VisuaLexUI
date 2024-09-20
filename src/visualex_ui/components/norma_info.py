from PyQt6.QtWidgets import QGroupBox, QFormLayout, QLabel, QPushButton, QApplication, QMessageBox, QScrollArea, QSizePolicy
from PyQt6.QtCore import Qt, QSize

class NormaInfoSection(QGroupBox):
    def __init__(self, parent):
        super().__init__("Informazioni sulla Norma", parent)
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        self.layout = QFormLayout()

            # Configurazione del layout senza spaziatura aggiuntiva
        #self.layout.setContentsMargins(0, 0, 0, 0)
        #self.layout.setSpacing(2)  # Imposta uno spacing più compatto

        # Crea una QScrollArea per racchiudere il QLabel dell'URN
        self.urn_scroll_area = QScrollArea()
        self.urn_scroll_area.setFixedSize(QSize(300, 30))
        self.urn_scroll_area.setWidgetResizable(True)  # Permette di adattare il contenuto
        self.urn_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Scrollbar orizzontale
        self.urn_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)  # Scrollbar verticale, se necessario

        # Etichetta per mostrare l'URN
        self.urn_label = QLabel()
        self.urn_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.urn_label.setOpenExternalLinks(True)
        self.urn_label.setWordWrap(False)  # Abilita il wrapping del testo
        
        # Imposta la QLabel come widget della QScrollArea
        self.urn_scroll_area.setWidget(self.urn_label)

        self.tipo_atto_label = QLabel()
        self.tipo_atto_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)  # Allineamento in alto a sinistra

        self.data_label = QLabel()
        self.data_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.numero_atto_label = QLabel()
        self.numero_atto_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Aggiunta delle etichette al layout
        self.layout.addRow("URN:", self.urn_scroll_area)  # Aggiungi la QScrollArea invece della QLabel direttamente
        self.layout.addRow("Tipo di Atto:", self.tipo_atto_label)

        # Aggiungi righe con le etichette di testo per Data e Numero Atto
        self.data_row = self.layout.addRow("Data:", self.data_label)
        self.numero_atto_row = self.layout.addRow("Numero Atto:", self.numero_atto_label)

        # Pulsante per copiare tutte le informazioni visualizzate
        self.copy_info_button = QPushButton("Copia Informazioni")
        self.copy_info_button.setToolTip("Copia tutte le informazioni visualizzate negli appunti.")
        self.copy_info_button.clicked.connect(self.copy_all_norma_info)
        self.layout.addRow(self.copy_info_button)

        self.setLayout(self.layout)
            # Imposta dimensioni minime ragionevoli per evitare che il widget si espanda inutilmente
        self.setMaximumHeight(230)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum))

    def update_info(self, normavisitata):
        """
        Metodo per aggiornare le informazioni della norma visualizzate nella sezione.
        """
        if not normavisitata:
            self.clear_info()
            return

        # Popola le etichette con le informazioni della norma
        full_url = normavisitata.urn
        self.urn_label.setText(f'<a href="{full_url}">{full_url}</a>')  # Mostra l'URL completo all'interno della scroll area

        self.tipo_atto_label.setText(normavisitata.norma.tipo_atto_str)

        # Gestione della data
        if normavisitata.norma.data:
            self.data_label.setText(normavisitata.norma.data)
            self.data_label.setVisible(True)
            self.layout.labelForField(self.data_label).setVisible(True)
        else:
            self.data_label.setVisible(False)
            self.layout.labelForField(self.data_label).setVisible(False)

        # Gestione del numero di atto
        if normavisitata.norma.numero_atto:
            self.numero_atto_label.setText(normavisitata.norma.numero_atto)
            self.numero_atto_label.setVisible(True)
            self.layout.labelForField(self.numero_atto_label).setVisible(True)
        else:
            self.numero_atto_label.setVisible(False)
            self.layout.labelForField(self.numero_atto_label).setVisible(False)

    def clear_info(self):
        """
        Metodo per pulire le informazioni visualizzate.
        """
        self.urn_label.clear()
        self.tipo_atto_label.clear()

        self.data_label.clear()
        self.data_label.setVisible(False)
        self.layout.labelForField(self.data_label).setVisible(False)

        self.numero_atto_label.clear()
        self.numero_atto_label.setVisible(False)
        self.layout.labelForField(self.numero_atto_label).setVisible(False)

    def copy_all_norma_info(self):
        """
        Copia tutte le informazioni della norma negli appunti.
        """
        info = []

        if self.urn_label.text():
            info.append(f"URN: {self.urn_label.text()}")
        if self.tipo_atto_label.text():
            info.append(f"Tipo di Atto: {self.tipo_atto_label.text()}")
        if self.data_label.isVisible() and self.data_label.text():  # Copia solo se visibile
            info.append(f"Data: {self.data_label.text()}")
        if self.numero_atto_label.isVisible() and self.numero_atto_label.text():  # Copia solo se visibile
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
