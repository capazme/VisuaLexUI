# visualex_ui/components/search_input.py
from PyQt6.QtWidgets import (
    QGroupBox, QFormLayout, QComboBox, QLineEdit, QPushButton, QProgressBar, QMessageBox,
    QRadioButton, QButtonGroup, QDateEdit, QVBoxLayout, QHBoxLayout
)
from PyQt6.QtCore import QDate

class SearchInputSection(QGroupBox):
    def __init__(self, parent):
        super().__init__("Ricerca Normativa", parent)
        self.parent = parent
        self.api_url = self.parent.api_url  # Riferimento all'URL API dal genitore
        self.setup_ui()

    def setup_ui(self):
        # Layout principale verticale
        main_layout = QVBoxLayout()

        # Aggiungi il layout del form per i campi di input
        form_layout = QFormLayout()

        # Input per il tipo di atto (ComboBox)
        self.act_type_input = QComboBox()
        self.act_type_input.addItems(self.parent.fonti_principali)
        self.act_type_input.currentIndexChanged.connect(self.update_input_fields)
        self.act_type_input.setToolTip("Seleziona il tipo di atto legislativo da cercare.")
        form_layout.addRow("Tipo di Atto:", self.act_type_input)

        # Campi di input aggiuntivi (data, numero atto, numero articolo)
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("dd/mm/yyyy")
        self.date_input.setToolTip("Inserisci la data dell'atto nel formato gg/mm/aaaa.")
        self.act_number_input = QLineEdit()
        self.act_number_input.setToolTip("Inserisci il numero dell'atto legislativo.")

        # New radio button for annex number
        self.annex_radio_button = QRadioButton("Allegato")
        self.annex_radio_button.setToolTip("Seleziona per inserire il numero dell'allegato.")
        self.annex_radio_button.toggled.connect(self.toggle_annex_input)

        # New input for annex number
        self.annex_number_input = QLineEdit()
        self.annex_number_input.setToolTip("Inserisci il numero dell'allegato.")
        self.annex_number_input.setEnabled(False)  # Initially disabled

        # Layout for Act Number and annex Number in the same row
        act_annex_layout = QHBoxLayout()
        act_annex_layout.addWidget(self.act_number_input)
        act_annex_layout.addWidget(self.annex_radio_button)
        act_annex_layout.addWidget(self.annex_number_input)

        form_layout.addRow("Data:", self.date_input)
        form_layout.addRow("Numero Atto:", act_annex_layout)

        # Input per il numero di articolo
        self.article_input = QLineEdit()
        self.article_input.setToolTip("Inserisci il numero dell'articolo da cercare.")
        form_layout.addRow("Numero Articolo:", self.article_input)

        # Selezione versione e data di vigenza
        self.version_group = QButtonGroup(self)
        self.version_originale = QRadioButton("Originale")
        self.version_vigente = QRadioButton("Vigente")
        self.version_group.addButton(self.version_originale)
        self.version_group.addButton(self.version_vigente)
        self.version_vigente.setChecked(True)
        self.version_originale.setToolTip("Seleziona per cercare la versione originale dell'atto.")
        self.version_vigente.setToolTip("Seleziona per cercare la versione vigente dell'atto.")

        # Input per la data di vigenza
        self.vigency_date_input = QDateEdit()
        self.vigency_date_input.setCalendarPopup(True)
        self.vigency_date_input.setDisplayFormat("dd/MM/yyyy")
        self.vigency_date_input.setDate(QDate.currentDate())
        self.vigency_date_input.setEnabled(self.version_vigente.isChecked())
        self.vigency_date_input.setToolTip("Seleziona la data di vigenza per la versione vigente.")
        self.version_group.buttonToggled.connect(self.toggle_vigency_date)

        # Layout per i bottoni di versione
        version_layout = QHBoxLayout()
        version_layout.addWidget(self.version_originale)
        version_layout.addWidget(self.version_vigente)
        form_layout.addRow("Versione:", version_layout)
        form_layout.addRow("Data di Vigenza:", self.vigency_date_input)

        # Pulsante di ricerca
        self.search_button = QPushButton("Cerca Norma")
        self.search_button.setToolTip("Clicca per avviare la ricerca della norma.")
        # Collegamento del pulsante di ricerca al metodo di ricerca del parent
        self.search_button.clicked.connect(self.parent.on_search_button_clicked)
        form_layout.addRow(self.search_button)

        # Aggiungi il layout del form al layout principale
        main_layout.addLayout(form_layout)

        # Barra di caricamento per la ricerca
        self.search_progress_bar = QProgressBar()
        self.search_progress_bar.setVisible(False)
        main_layout.addWidget(self.search_progress_bar)  # Cambia da addRow a addWidget

        # Pulsante per mostrare il dock delle informazioni sulla norma
        dock_buttons_layout = QHBoxLayout()

        self.show_norma_info_button = QPushButton("Mostra Norma Info")
        self.show_norma_info_button.clicked.connect(self.parent.show_norma_info_dock)
        dock_buttons_layout.addWidget(self.show_norma_info_button)

        self.show_brocardi_button = QPushButton("Mostra Brocardi")
        self.show_brocardi_button.clicked.connect(self.parent.show_brocardi_dock)
        dock_buttons_layout.addWidget(self.show_brocardi_button)

        self.show_output_button = QPushButton("Mostra Output")
        self.show_output_button.clicked.connect(self.parent.show_output_dock)
        dock_buttons_layout.addWidget(self.show_output_button)

        # Aggiungi il layout dei pulsanti al layout principale
        main_layout.addLayout(dock_buttons_layout)

        self.setLayout(main_layout)
        self.update_input_fields()  # Inizializza i campi di input

    def toggle_annex_input(self):
        """Enable or disable the annex number input based on the radio button selection."""
        is_checked = self.annex_radio_button.isChecked()
        self.annex_number_input.setEnabled(is_checked)

    def toggle_vigency_date(self):
        """Enable or disable the vigency date input based on the version selection."""
        self.vigency_date_input.setEnabled(self.version_vigente.isChecked())

    def update_input_fields(self):
        """Updates the input fields based on the selected act type."""
        selected_act_type = self.act_type_input.currentText()
        allowed_types = ['legge', 'decreto legge', 'decreto legislativo', 'd.p.r.', 'Regolamento UE', 'Direttiva UE', 'regio decreto']

        # Abilita/disabilita i campi in base al tipo di atto selezionato
        is_enabled = selected_act_type in allowed_types
        self.date_input.setEnabled(is_enabled)
        self.act_number_input.setEnabled(is_enabled)

        # Pulisce i campi se non sono abilitati
        if not is_enabled:
            self.date_input.clear()
            self.act_number_input.clear()

    def get_search_payload(self):
        """Raccoglie e restituisce i dati di input necessari per la ricerca come dizionario."""
        # Raccoglie i dati dagli input utente
        act_type = self.act_type_input.currentText().strip()
        date = self.date_input.text().strip() if self.date_input.text().strip() else None
        act_number = self.act_number_input.text().strip() if self.act_number_input.text().strip() else None
        article = self.article_input.text().strip() if self.article_input.text().strip() else None
        version = "originale" if self.version_originale.isChecked() else "vigente"
        vigency_date = self.vigency_date_input.date().toString("yyyy-MM-dd") if self.version_vigente.isChecked() else None

        annex = None
        if self.annex_radio_button.isChecked():
            annex = self.annex_number_input.text().strip() if self.annex_number_input.text().strip() else None

        # Crea i dati di richiesta
        payload = {
            "act_type": act_type,
            "version": version,
        }
        
        # Aggiungi campi opzionali se non vuoti
        if date:
            payload["date"] = date
            
        if act_number:
            payload["act_number"] = act_number

        if article:
            payload["article"] = article

        if vigency_date:
            payload["version_date"] = vigency_date
            
        if annex:
            payload["annex"] = annex

        return payload
