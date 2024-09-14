from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit, QPushButton,
    QTextEdit, QTabWidget, QFormLayout, QGroupBox, QRadioButton, QComboBox, QButtonGroup,
    QScrollArea, QDateEdit, QListWidget, QListWidgetItem, QMessageBox, QProgressBar, QStatusBar,
    QDockWidget, QInputDialog, QTextBrowser
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDate, QSettings, QSize
from PyQt6.QtGui import QFont, QTextOption, QIcon, QAction, QColor
import sys
import requests
import re
import os
import time
import logging
import json
from requests.exceptions import Timeout, ConnectionError, HTTPError, RequestException
from functools import lru_cache
from tools.map import FONTI_PRINCIPALI
from tools.norma import NormaVisitata
from tools.themes import ThemeDialog
from tools.config import THEMES
import tufup

with open('version.txt', 'r') as f:
    CURRENT_VERSION = f.read()

# Configura il logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FetchDataThread(QThread):
    data_fetched = pyqtSignal(object)

    def __init__(self, url, payload):
        super().__init__()
        self.url = url
        self.payload = payload
        self.max_retries = 3  # Numero massimo di tentativi
        self.timeout = 10  # Timeout per le richieste in secondi

    def run(self):
        attempts = 0
        while attempts < self.max_retries:
            try:
                response = requests.post(self.url, json=self.payload, timeout=self.timeout)
                response.raise_for_status()  # Lancia un'eccezione per codici di stato HTTP 4xx/5xx
                data = response.json()
                if 'norma_data' in data:
                    normavisitata = NormaVisitata.from_dict(data['norma_data'])
                    normavisitata._article_text = data.get('result', '')
                    normavisitata._brocardi_info = data.get('brocardi_info', {})
                    self.data_fetched.emit(normavisitata)
                else:
                    error_msg = data.get('error', "Errore nella risposta dell'API.")
                    self.data_fetched.emit({'error': error_msg})
                logging.info("Richiesta completata con successo.")
                return  # Se la richiesta ha successo, esci dal metodo
            except (Timeout, ConnectionError) as e:
                attempts += 1
                logging.warning(f"Tentativo {attempts} fallito: {e}")
                time.sleep(2)  # Attendi 2 secondi prima di riprovare
                if attempts == self.max_retries:
                    self.data_fetched.emit({'error': "Impossibile connettersi al server. Verifica la tua connessione internet."})
            except HTTPError as e:
                self.data_fetched.emit({'error': f"Errore HTTP: {e.response.status_code}"})
                return
            except json.JSONDecodeError as e:
                self.data_fetched.emit({'error': "Errore nel decodificare la risposta del server."})
                return
            except RequestException as e:
                self.data_fetched.emit({'error': f"Errore nella richiesta: {str(e)}"})
                return
            except Exception as e:
                logging.error(f"Errore inaspettato: {e}")
                self.data_fetched.emit({'error': "Si è verificato un errore inaspettato."})
                return

class NormaViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visualizzatore di Norme Legali")
        self.setGeometry(100, 100, 900, 700)
        self.setWindowIcon(QIcon.fromTheme("text-x-generic"))

        # Caricamento delle impostazioni
        self.settings = QSettings("NormaApp", "NormaViewer")
        self.load_settings()

        tufup.init({
            'repository_url': 'https://github.com/capazme/VisuaLexUI/releases/latest/download/',  # URL per le release GitHub
            'local_directory': './.updates',  # Directory locale per scaricare gli aggiornamenti
            'target_name': 'VisuaLexUI-{version}.tar.gz'  # Nome del pacchetto di aggiornamento con segnaposto per la versione
        })

        # Controlla gli aggiornamenti all'avvio dell'applicazione
        self.check_for_updates()


        # Memorizzazione dell'URL API
        self.api_url = self.settings.value("api_url", "https://example-default-url.ngrok-free.app")  # URL di default

        # Barra di stato
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Menu per la modifica URL API e personalizzazione del tema
        self.create_menu()

        # Layout principale
        main_layout = QVBoxLayout()

        # Creazione e configurazione delle sezioni UI
        self.create_search_input_section(main_layout)
        self.create_collapsible_norma_info_section(main_layout)
        self.create_brocardi_dock_widget()
        self.create_resizable_norma_text_section(main_layout)

        # Imposta il widget centrale
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Cache per risultati di ricerca
        self.search_cache = {}

    def create_menu(self):
        # Barra dei menu
        menu_bar = self.menuBar()

        # Menu per le impostazioni
        settings_menu = menu_bar.addMenu("Impostazioni")

        # Azione per modificare l'URL dell'API
        api_url_action = QAction(QIcon.fromTheme("network-wired"), "Modifica URL API", self)
        api_url_action.triggered.connect(self.change_api_url)
        settings_menu.addAction(api_url_action)

        # Aggiungi azione per la personalizzazione del tema
        theme_customize_action = QAction("Personalizza Tema", self)
        theme_customize_action.triggered.connect(self.open_theme_dialog)
        settings_menu.addAction(theme_customize_action)
  
    def open_theme_dialog(self):
        # Carica il tema personalizzato dalle impostazioni se disponibile
        if self.current_theme == "Personalizzato":
            custom_theme = self.settings.value("custom_theme", {})
            if custom_theme:
                # Assicurati che i tipi siano corretti
                custom_theme = {
                    'font_size': int(custom_theme.get('font_size', 14)),
                    'colors': custom_theme.get('colors', ['#FFFFFF', '#000000', '#CCCCCC', '#000000'])
                }
                self.custom_theme = custom_theme
        else:
            self.custom_theme = None

        # Passa i temi come variabile locale, non come attributo di istanza
        themes = {}  # Vuoto o riempi con temi predefiniti se necessario

        dialog = ThemeDialog(self, themes=themes, current_theme=self.current_theme, custom_theme=self.custom_theme)
        if dialog.exec():
            selected_theme = dialog.get_selected_theme()
            if isinstance(selected_theme, dict):
                # Applica il tema personalizzato
                self.custom_theme = selected_theme
                self.current_theme = "Personalizzato"
                self.apply_custom_theme(self.custom_theme)
                self.settings.setValue("theme", self.current_theme)
                self.settings.setValue("custom_theme", self.custom_theme)
            else:
                # Applica il tema predefinito
                self.current_theme = selected_theme
                self.custom_theme = None
                self.apply_predefined_theme(self.current_theme)
                self.settings.setValue("theme", self.current_theme)

    def change_api_url(self):
        # Mostra un dialogo per l'input dell'URL
        new_url, ok = QInputDialog.getText(self, "Modifica URL API", "Inserisci il nuovo URL dell'API:")
        if ok and new_url:
            self.api_url = new_url
            self.settings.setValue("api_url", self.api_url)
            QMessageBox.information(self, "URL Aggiornato", "L'URL dell'API è stato aggiornato correttamente.")

    def toggle_dark_mode(self, checked):
        self.is_dark_mode = checked
        # Carica il foglio di stile appropriato in base al tema e alla modalità
        if self.is_dark_mode:
            dark_theme_name = self.current_theme.replace("Light", "Dark")
            stylesheet = load_stylesheet(dark_theme_name)
        else:
            stylesheet = load_stylesheet(self.current_theme)

        if stylesheet:
            self.setStyleSheet(stylesheet)

        # Salva la modalità nelle impostazioni
        self.settings.setValue("dark_mode", self.is_dark_mode)

    def load_settings(self):
        self.current_theme = self.settings.value("theme", "Personalizzato")
        custom_theme = self.settings.value("custom_theme", {})
        if custom_theme:
            custom_theme = {
                'font_size': int(custom_theme['font_size']),
                'colors': custom_theme['colors']
            }
            self.custom_theme = custom_theme
            self.apply_custom_theme(self.custom_theme)
            
    def create_search_input_section(self, layout):
        search_group = QGroupBox("Ricerca Normativa")
        search_layout = QFormLayout()

        # Input per il tipo di atto (ComboBox)
        self.act_type_input = QComboBox()
        self.act_type_input.addItems(FONTI_PRINCIPALI)
        self.act_type_input.currentIndexChanged.connect(self.update_input_fields)
        self.act_type_input.setToolTip("Seleziona il tipo di atto legislativo da cercare.")
        search_layout.addRow("Tipo di Atto:", self.act_type_input)

        # Campi di input aggiuntivi (data, numero atto, numero articolo)
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("dd/mm/yyyy")
        self.date_input.setToolTip("Inserisci la data dell'atto nel formato gg/mm/aaaa.")
        self.act_number_input = QLineEdit()
        self.act_number_input.setToolTip("Inserisci il numero dell'atto legislativo.")
        self.article_input = QLineEdit()
        self.article_input.setToolTip("Inserisci il numero dell'articolo da cercare.")
        search_layout.addRow("Data:", self.date_input)
        search_layout.addRow("Numero Atto:", self.act_number_input)
        search_layout.addRow("Numero Articolo:", self.article_input)

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
        search_layout.addRow("Versione:", version_layout)
        search_layout.addRow("Data di Vigenza:", self.vigency_date_input)

        # Pulsante di ricerca
        self.search_button = QPushButton("Cerca Norma")
        self.search_button.clicked.connect(self.on_search_button_clicked)
        self.search_button.setIcon(QIcon.fromTheme("edit-find"))
        self.search_button.setToolTip("Clicca per avviare la ricerca della norma.")
        search_layout.addRow(self.search_button)

        # Barra di caricamento per la ricerca
        self.search_progress_bar = QProgressBar()
        self.search_progress_bar.setVisible(False)
        search_layout.addRow(self.search_progress_bar)

        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        # Inizializza i campi di input
        self.update_input_fields()

    def update_input_fields(self):
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

    def toggle_vigency_date(self):
        self.vigency_date_input.setEnabled(self.version_vigente.isChecked())

    def create_collapsible_norma_info_section(self, layout):
        self.norma_info_button = QPushButton("Informazioni sulla Norma")
        self.norma_info_button.setCheckable(True)
        self.norma_info_button.setChecked(False)
        self.norma_info_button.setToolTip("Mostra o nascondi le informazioni dettagliate sulla norma.")
        self.norma_info_button.clicked.connect(self.toggle_norma_info)

        self.norma_info_widget = QWidget()
        info_layout = QFormLayout()

        # Campi informativi sulla norma
        self.urn_label = QLabel()
        self.urn_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.urn_label.setOpenExternalLinks(True)
        self.tipo_atto_label = QLabel()
        self.data_label = QLabel()
        self.numero_atto_label = QLabel()

        info_layout.addRow("URN:", self.urn_label)
        info_layout.addRow("Tipo di Atto:", self.tipo_atto_label)
        info_layout.addRow("Data:", self.data_label)
        info_layout.addRow("Numero Atto:", self.numero_atto_label)

        self.norma_info_widget.setLayout(info_layout)
        self.norma_info_widget.setVisible(False)

        layout.addWidget(self.norma_info_button)
        layout.addWidget(self.norma_info_widget)

    def toggle_norma_info(self):
        self.norma_info_widget.setVisible(self.norma_info_button.isChecked())

    def create_brocardi_dock_widget(self):
        # Creazione del Dock Widget per i Brocardi
        self.brocardi_dock = QDockWidget("Informazioni Brocardi", self)
        self.brocardi_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.brocardi_dock.setWindowIcon(QIcon.fromTheme("help-browser"))

        # Widget contenitore
        self.brocardi_info_widget = QWidget()
        brocardi_layout = QVBoxLayout()

        # Informazioni Brocardi
        self.position_label = QLabel()
        brocardi_layout.addWidget(self.position_label)
        self.brocardi_link_label = QLabel()
        self.brocardi_link_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.brocardi_link_label.setOpenExternalLinks(True)
        brocardi_layout.addWidget(self.brocardi_link_label)

        self.tabs = QTabWidget()
        self.dynamic_tabs = {}

        brocardi_layout.addWidget(self.tabs)
        self.brocardi_info_widget.setLayout(brocardi_layout)

        # Imposta il widget come contenuto del dock
        self.brocardi_dock.setWidget(self.brocardi_info_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.brocardi_dock)

        # Inizialmente, nascondi il dock
        self.brocardi_dock.hide()

        # Crea un pulsante per mostrare/nascondere il dock widget
        self.brocardi_toggle_button = QPushButton("Mostra/Nascondi Brocardi")
        self.brocardi_toggle_button.setCheckable(True)
        self.brocardi_toggle_button.setChecked(False)
        self.brocardi_toggle_button.setToolTip("Mostra o nascondi le informazioni sui brocardi.")
        self.brocardi_toggle_button.clicked.connect(self.toggle_brocardi_dock)
        self.brocardi_toggle_button.setVisible(False)  # Nascondi il pulsante inizialmente

        # Aggiungi il pulsante alla barra di stato
        self.status_bar.addPermanentWidget(self.brocardi_toggle_button)

    def toggle_brocardi_dock(self):
        if self.brocardi_toggle_button.isChecked():
            self.brocardi_dock.show()
        else:
            self.brocardi_dock.hide()

    def create_resizable_norma_text_section(self, layout):
        text_group = QGroupBox("Testo della Norma")
        text_layout = QVBoxLayout()

        # Visualizzazione del testo della norma
        self.norma_text_edit = QTextEdit()
        self.norma_text_edit.setReadOnly(True)
        self.norma_text_edit.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.norma_text_edit.setFont(QFont("Arial", 12))

        # Area di scorrimento per la visualizzazione del testo
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.norma_text_edit)

        text_layout.addWidget(scroll_area)

        # Pulsante per copiare tutte le informazioni
        copy_all_button = QPushButton("Copia Tutte le Informazioni")
        copy_all_button.clicked.connect(self.copy_all_norma_info)
        copy_all_button.setIcon(QIcon.fromTheme("edit-copy"))
        copy_all_button.setToolTip("Copia tutte le informazioni visualizzate negli appunti.")
        text_layout.addWidget(copy_all_button)

        text_group.setLayout(text_layout)
        layout.addWidget(text_group)

    def copy_all_norma_info(self):
        """
        Copia tutte le informazioni della norma, inclusi i brocardi e le massime selezionate, la ratio, la spiegazione e il testo dell'articolo.
        """
        info = []

        # Copia le informazioni della norma popolate
        info.append("=== Informazioni Generali ===")
        if self.urn_label.text():
            info.append(f"URN: {self.urn_label.text()}")
        if self.tipo_atto_label.text():
            info.append(f"Tipo di Atto: {self.tipo_atto_label.text()}")
        if self.data_label.text():
            info.append(f"Data: {self.data_label.text()}")
        if self.numero_atto_label.text():
            info.append(f"Numero Atto: {self.numero_atto_label.text()}")

        # Aggiungi il testo della norma
        if self.norma_text_edit.toPlainText():
            info.append("\n=== Testo della Norma ===\n" + self.norma_text_edit.toPlainText())

        # Copia i Brocardi e Massime selezionati
        brocardi_info = self.get_brocardi_info_as_text(seleziona_solo=True)
        if brocardi_info:
            info.append("\n=== Brocardi e Massime Selezionati ===\n" + brocardi_info)

        # Copia negli appunti
        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(info))

        # Mostra notifica
        QMessageBox.information(self, "Informazione Copiata", "Tutte le informazioni selezionate sono state copiate negli appunti.")

    def get_brocardi_info_as_text(self, seleziona_solo=False):
        """
        Compila le informazioni sui brocardi, massime, spiegazione, ratio e posizione in un testo formattato.
        Se seleziona_solo=True, include solo brocardi e massime selezionati.
        """
        brocardi_text = []

        # Posizione
        if self.position_label.text() and not seleziona_solo:
            brocardi_text.append(f"Posizione: {self.position_label.text()}")

        # Brocardi e Massime
        for section_name, tab_widget in self.dynamic_tabs.items():
            if section_name in ['Brocardi', 'Massime']:
                items = self.get_selected_items(tab_widget) if seleziona_solo else self.get_all_items(tab_widget)
                if items:
                    brocardi_text.append(f"\n--- {section_name} ---\n" + "\n".join(items))
            elif section_name in ['Spiegazione', 'Ratio'] and not seleziona_solo:
                text_content = self.get_text_edit_content(tab_widget)
                if text_content:
                    brocardi_text.append(f"\n--- {section_name} ---\n{text_content}")

        return "\n\n".join(brocardi_text)

    def get_selected_items(self, tab_widget):
        """
        Ritorna una lista di stringhe per tutti gli elementi selezionati di QListWidget.
        """
        if not tab_widget:
            return []

        list_widget_obj = tab_widget.findChild(QListWidget)
        if not list_widget_obj:
            return []

        items = []
        for i in range(list_widget_obj.count()):
            item = list_widget_obj.item(i)
            if item.isSelected():
                # Accediamo direttamente al testo di QTextBrowser dentro QListWidgetItem
                item_widget = list_widget_obj.itemWidget(item)
                if item_widget:
                    text_browser = item_widget.findChild(QTextBrowser)
                    if text_browser and text_browser.toPlainText().strip():
                        items.append(text_browser.toPlainText().strip())
        return items

    def get_all_items(self, tab_widget):
        """
        Ritorna una lista di stringhe per tutti gli elementi di QListWidget.
        """
        if not tab_widget:
            return []

        list_widget_obj = tab_widget.findChild(QListWidget)
        if not list_widget_obj:
            return []

        items = []
        for i in range(list_widget_obj.count()):
            item = list_widget_obj.item(i)
            # Accediamo direttamente al testo di QTextBrowser dentro QListWidgetItem
            item_widget = list_widget_obj.itemWidget(item)
            if item_widget:
                text_browser = item_widget.findChild(QTextBrowser)
                if text_browser and text_browser.toPlainText().strip():
                    items.append(text_browser.toPlainText().strip())
        return items

    @lru_cache(maxsize=32)
    def get_cached_data(self, key):
        """
        Funzione per ottenere i dati memorizzati nella cache.
        """
        return self.search_cache.get(key)

    def cache_data(self, key, data):
        """
        Funzione per memorizzare i dati nella cache.
        """
        self.search_cache[key] = data

    def get_text_edit_content(self, tab_widget):
        """
        Ritorna il testo contenuto nel QTextEdit di una scheda tab.
        """
        if not tab_widget:
            return ""

        text_edit = tab_widget.findChild(QTextEdit)
        if not text_edit:
            return ""

        return text_edit.toPlainText()

    def on_search_button_clicked(self):
        # Disabilita il pulsante di ricerca
        self.search_button.setEnabled(False)

        # Estrai i dati di input
        act_type = self.act_type_input.currentText()
        date = self.date_input.text().strip()
        act_number = self.act_number_input.text().strip()
        article = self.article_input.text().strip()
        version = "originale" if self.version_originale.isChecked() else "vigente"
        vigency_date = self.vigency_date_input.date().toString("yyyy-MM-dd") if self.version_vigente.isChecked() else None

        # Validazione degli input con feedback
        if not act_type:
            QMessageBox.warning(self, "Errore di Input", "Il campo 'Tipo di Atto' è obbligatorio.")
            self.search_button.setEnabled(True)
            return

        # Crea i dati di richiesta e avvia un thread di fetch
        payload = {
            "act_type": act_type,
            "date": date,
            "act_number": act_number,
            "article": article,
            "version": version,
            "version_date": vigency_date
        }

        # Controlla se i dati sono già nella cache
        cache_key = f"{act_type}-{date}-{act_number}-{article}-{version}-{vigency_date}"
        cached_result = self.get_cached_data(cache_key)
        if cached_result:
            self.display_data(cached_result)
            self.search_button.setEnabled(True)
            return

        # Mostra la barra di caricamento
        self.search_progress_bar.setVisible(True)
        self.search_progress_bar.setRange(0, 0)  # Modalità indeterminata

        self.thread = FetchDataThread(self.api_url + "/fetch_norm", payload)
        self.thread.data_fetched.connect(lambda data: self.handle_data_fetch(data, cache_key))
        self.thread.start()

        logging.info("Ricerca avviata.")

    def handle_data_fetch(self, normavisitata, cache_key):
        # Riemetti il pulsante di ricerca
        self.search_button.setEnabled(True)
        # Nascondi la barra di caricamento dopo aver caricato i dati
        self.search_progress_bar.setVisible(False)

        # Caching dei dati
        self.cache_data(cache_key, normavisitata)

        # Visualizza i dati
        self.display_data(normavisitata)

        logging.info("Dati ricevuti dal thread di fetch.")

    def display_data(self, normavisitata):
        self.clear_dynamic_tabs()

        if isinstance(normavisitata, dict) and 'error' in normavisitata:
            self.norma_text_edit.setText(normavisitata['error'])
            QMessageBox.critical(self, "Errore", normavisitata['error'])
            return

        # Popola l'interfaccia con i dati ricevuti
        self.urn_label.setText(f'<a href="{normavisitata.urn}">{normavisitata.urn}</a>')
        self.tipo_atto_label.setText(normavisitata.norma.tipo_atto_str)
        self.data_label.setText(normavisitata.norma.data)
        self.numero_atto_label.setText(normavisitata.norma.numero_atto)

        # Pulisce e visualizza il testo
        cleaned_text = re.sub(r'\n\s*\n', '\n', normavisitata._article_text.strip()) if normavisitata._article_text else ''
        self.norma_text_edit.setText(cleaned_text)

        # Carica dinamicamente le informazioni sui Brocardi se disponibili
        brocardi_info = normavisitata._brocardi_info
        if brocardi_info.get('position') and brocardi_info['position'] != "Not Available":
            self.position_label.setText(brocardi_info['position'])
            self.brocardi_link_label.setText(f'<a href="{brocardi_info["link"]}">{brocardi_info["link"]}</a>')

            # Mostra il pulsante e il dock widget per i Brocardi
            self.brocardi_toggle_button.setVisible(True)
            self.brocardi_toggle_button.setChecked(True)
            self.brocardi_dock.show()

            # Gestisce le sezioni dinamiche
            for section_name, content in brocardi_info.get('info', {}).items():
                if section_name in ['Brocardi', 'Massime'] and content:
                    tab = QWidget()
                    list_widget = QListWidget()
                    list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
                    list_widget.setStyleSheet("QListWidget::item { border: 1px solid #4E878C; margin: 4px; padding: 8px; }")  # Migliora lo stile degli item

                    # Usa il metodo create_collapsible_list_item per aggiungere gli elementi
                    for item_text in content:
                        item_text = re.sub(r'“|”', '', item_text) if section_name == 'Brocardi' else re.sub(r'\s+', ' ', item_text.strip())
                        self.create_collapsible_list_item(item_text, list_widget)

                    self.create_tab(tab, section_name, list_widget)
                    self.dynamic_tabs[section_name] = tab
                elif section_name in ['Spiegazione', 'Ratio'] and content:
                    tab = QWidget()
                    text_edit = QTextEdit()
                    text_edit.setReadOnly(True)
                    cleaned_content = re.sub(r'\s+', ' ', content.strip())
                    text_edit.setText(cleaned_content)
                    self.create_tab(tab, section_name, text_edit)
                    self.dynamic_tabs[section_name] = tab
        else:
            # Nascondi il pulsante e il dock widget se non ci sono informazioni sui Brocardi
            self.brocardi_toggle_button.setChecked(False)
            self.brocardi_toggle_button.setVisible(False)
            self.brocardi_dock.hide()

    def create_collapsible_list_item(self, text, parent_widget):
        """
        Crea un elemento QListWidgetItem con un QTextBrowser all'interno per gestire il testo lungo.
        """
        if not text.strip():  # Verifica se l'elemento è un riempitivo (stringa vuota o solo spazi)
            # Crea un riempitivo senza widget aggiuntivi
            item = QListWidgetItem(parent_widget)
            item.setSizeHint(QSize(0, 20))  # Altezza fissa per il riempitivo
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # Nessuna interazione per il riempitivo
            return

        # Creiamo un item per il QListWidget
        item = QListWidgetItem(parent_widget)
        item_widget = QWidget()  # Crea un QWidget per ospitare il layout

        # Layout verticale per contenere QTextBrowser
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Rimuovi i margini per evitare il ritaglio

        # QTextBrowser per visualizzare il testo lungo
        text_browser = QTextBrowser()
        text_browser.setText(text)
        text_browser.setOpenExternalLinks(True)  # Permette di cliccare su link se presenti
        text_browser.setMinimumHeight(50)  # Altezza minima
        text_browser.setMaximumHeight(200)  # Altezza massima per evitare di occupare troppo spazio

        # Aggiungi QTextBrowser al layout
        layout.addWidget(text_browser)

        item_widget.setLayout(layout)
        item.setSizeHint(item_widget.sizeHint())  # Assicurati che l'elemento abbia la dimensione corretta
        parent_widget.setItemWidget(item, item_widget)  # Imposta il widget come item di QListWidget

    def create_tab(self, tab, title, widget):
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(widget)
        tab.setLayout(tab_layout)
        self.tabs.addTab(tab, title)

    def add_divider_to_list(self, list_widget):
        divider = QListWidgetItem()
        divider.setFlags(Qt.ItemFlag.NoItemFlags)
        list_widget.addItem(divider)

    def clear_dynamic_tabs(self):
        self.tabs.clear()
        self.dynamic_tabs.clear()
    
    def load_stylesheet(self, theme_name):
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            resources_path = os.path.join(base_path, 'resources')
            stylesheet_file = THEMES.get(theme_name)
            if not stylesheet_file:
                logging.error(f"Tema '{theme_name}' non trovato.")
                return ""

            stylesheet_path = os.path.join(resources_path, stylesheet_file)
            with open(stylesheet_path, 'r', encoding='utf-8') as file:
                stylesheet = file.read()

            return stylesheet
        except FileNotFoundError:
            logging.error(f"File {stylesheet_file} non trovato nella cartella resources.")
            return ""
        except Exception as e:
            logging.error(f"Errore nel caricamento del foglio di stile '{theme_name}': {e}")
            return ""
        
    def apply_custom_theme(self, custom_theme):
        stylesheet = self.generate_custom_stylesheet(custom_theme)
        if stylesheet:
            self.setStyleSheet(stylesheet)
        else:
            QMessageBox.warning(self, "Errore", "Impossibile applicare il tema personalizzato.")

    def apply_predefined_theme(self, theme_name):
        stylesheet = self.load_stylesheet(theme_name)
        if stylesheet:
            self.setStyleSheet(stylesheet)
        else:
            QMessageBox.warning(self, "Errore", f"Impossibile caricare il tema '{theme_name}'.")

    def generate_custom_stylesheet(self, custom_theme):
        # Load stylesheet template
        stylesheet_template = self.load_custom_stylesheet_template()
        if not stylesheet_template:
            return ""

        # Map user-selected colors
        font_size = custom_theme['font_size']
        colors = custom_theme['colors']

        background_color = colors[0]  # Background color
        text_color = colors[1]        # Text color
        button_bg_color = colors[2]   # Button background color
        button_text_color = colors[3] # Button text color

        # Compute additional colors
        button_hover_color = self.adjust_color(button_bg_color, 20)
        button_pressed_color = self.adjust_color(button_bg_color, -20)
        button_disabled_color = self.adjust_color(button_bg_color, -40)
        border_color = self.adjust_color(text_color, -40)
        input_bg_color = self.adjust_color(background_color, 10)
        selection_bg_color = self.adjust_color(button_bg_color, 30)
        selection_text_color = button_text_color

        style_values = {
            'font_size': font_size,
            'background_color': background_color,
            'text_color': text_color,
            'button_background_color': button_bg_color,
            'button_text_color': button_text_color,
            'button_hover_color': button_hover_color,
            'button_pressed_color': button_pressed_color,
            'button_disabled_color': button_disabled_color,
            'border_color': border_color,
            'input_background_color': input_bg_color,
            'selection_background_color': selection_bg_color,
            'selection_text_color': selection_text_color,
        }

        try:
            stylesheet = stylesheet_template.format(**style_values)
            return stylesheet
        except KeyError as e:
            logging.error(f"Segnaposto mancante nel template: {e}")
            return ""

    def adjust_color(self, color_str, amount):
        color = QColor(color_str)
        h, s, v, a = color.getHsv()
        v = max(0, min(255, v + amount))
        color.setHsv(h, s, v, a)
        return color.name()

    def load_custom_stylesheet_template(self):
        try:
            # Determine base path
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            resources_path = os.path.join(base_path, 'resources')
            stylesheet_path = os.path.join(resources_path, 'custom_style.qss')

            with open(stylesheet_path, 'r', encoding='utf-8') as file:
                stylesheet_template = file.read()

            return stylesheet_template
        except FileNotFoundError:
            logging.error("File custom_style.qss non trovato nella cartella resources.")
            return ""
        except Exception as e:
            logging.error(f"Errore nel caricamento del template: {e}")
            return ""
        
    theme_actions = {}
    def change_theme(self, theme_name):
        self.current_theme = theme_name

        # Resetta lo stile prima di applicare il nuovo
        self.reset_stylesheet()

        stylesheet = load_stylesheet(theme_name)
        if stylesheet:
            self.setStyleSheet(stylesheet)

        # Aggiorna le azioni dei menu per riflettere il tema selezionato
        for name, action in self.theme_actions.items():
            action.setChecked(name == theme_name)

        # Salva il tema nelle impostazioni
        self.settings.setValue("theme", theme_name)
        logging.info(f"Tema cambiato a: {theme_name}")

    def reset_stylesheet(self):
        """
        Resetta il foglio di stile corrente per evitare sovrapposizioni.
        """
        self.setStyleSheet("")

    def check_for_updates(self):
        try:
            update = tufup.check_for_updates(current_version=CURRENT_VERSION)
            if update:
                reply = QMessageBox.question(self, "Aggiornamento Disponibile",
                                             f"Un nuovo aggiornamento ({update['version']}) è disponibile. Vuoi scaricarlo e installarlo?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    tufup.apply_update(update)  # Applica l'aggiornamento
                    QMessageBox.information(self, "Aggiornamento Applicato", "L'applicazione è stata aggiornata. Riavvia per applicare le modifiche.")
                    sys.exit()  # Esci e riavvia l'applicazione
            else:
                logging.info("L'applicazione è già aggiornata.")
        except Exception as e:
            logging.error(f"Errore durante il controllo degli aggiornamenti: {e}")
            QMessageBox.critical(self, "Errore Aggiornamento", "Si è verificato un errore durante il controllo degli aggiornamenti.")



if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    app = QApplication(sys.argv)
    viewer = NormaViewer()
    viewer.show()
    sys.exit(app.exec())



