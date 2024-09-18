from PyQt6.QtWidgets import QMainWindow, QStatusBar, QVBoxLayout, QWidget, QMessageBox, QInputDialog, QMenu, QApplication, QPushButton, QDockWidget, QScrollArea
from PyQt6.QtCore import QSettings, Qt, QEvent
from PyQt6.QtGui import QIcon, QAction
from .search_input import SearchInputSection
from .norma_info import NormaInfoSection
from .brocardi_dock import BrocardiDockWidget
from .output_area import OutputArea
from ..theming.theme_manager import ThemeManager, ThemeDialog
from ..network.data_fetcher import FetchDataThread
from ..utils.helpers import get_resource_path
from ..utils.cache_manager import CacheManager
from ..tools.map import FONTI_PRINCIPALI
import logging
import re

class NormaViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"VisuaLex v{self.get_app_version()}")
        self.setGeometry(100, 100, 900, 700)

        # Configurazione Logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        # Setup UI components
        self.setup_ui()

        self.cache_manager = CacheManager()

        # Load saved theme settings
        self.load_theme_settings()

    def setup_ui(self):
        # Impostazioni dell'applicazione
        self.settings = QSettings("NormaApp", "NormaViewer")
        self.api_url = self.settings.value("api_url", "https:0.0.0.0:8000")  # URL di default
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Creazione del Menu
        self.create_menu()
        self.fonti_principali = FONTI_PRINCIPALI

        # Layout principale
        main_layout = QVBoxLayout()

        # Sezione di input di ricerca
        self.search_input_section = SearchInputSection(self)
        main_layout.addWidget(self.search_input_section)

        # Dock per le informazioni sulla norma
        self.create_collapsible_norma_info_dock()

        # Dock per il Brocardi
        self.create_collapsible_brocardi_dock()

        # Dock per l'output
        self.create_collapsible_output_dock()

        # Imposta il widget centrale
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Cache per risultati di ricerca
        self.search_cache = {}
    
    def moveEvent(self, event):
        """Evento chiamato quando la finestra viene spostata."""
        self.adjust_window_size()
        super().moveEvent(event)

    def resizeEvent(self, event):
        """Evento chiamato quando la finestra viene ridimensionata."""
        self.adjust_window_size()
        super().resizeEvent(event)

    def adjust_window_size(self):
        """Regola la dimensione della finestra per evitare che esca dai limiti dello schermo disponibile."""
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_geometry = self.frameGeometry()

        # Verifica i bordi a destra e ridimensiona la larghezza se necessario
        if window_geometry.right() > screen_geometry.right():
            new_width = screen_geometry.width() - window_geometry.left()
            self.resize(new_width, self.height())

        # Verifica i bordi a sinistra e ridimensiona la larghezza se necessario
        if window_geometry.left() < screen_geometry.left():
            self.move(screen_geometry.left(), window_geometry.top())

        # Verifica i bordi in basso e ridimensiona l'altezza se necessario
        if window_geometry.bottom() > screen_geometry.bottom():
            new_height = screen_geometry.height() - window_geometry.top()
            self.resize(self.width(), new_height)

        # Verifica i bordi in alto e ridimensiona l'altezza se necessario
        if window_geometry.top() < screen_geometry.top():
            self.move(window_geometry.left(), screen_geometry.top())

    def create_collapsible_norma_info_dock(self):
        """Crea un dock widget collassabile per le informazioni sulla norma."""
        self.norma_info_section = NormaInfoSection(self)  # Crea il widget della sezione
        self.norma_info_dock = QDockWidget("Informazioni sulla Norma", self)  # Crea il QDockWidget
        self.norma_info_dock.setWidget(self.norma_info_section)  # Imposta il widget della sezione come contenuto del dock

        # Impostazioni del dock
        self.norma_info_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                                         QDockWidget.DockWidgetFeature.DockWidgetClosable |
                                         QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.norma_info_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.norma_info_dock)  # Aggiungi il dock alla finestra



    def create_collapsible_brocardi_dock(self):
        """Crea un dock widget collassabile per le informazioni sui Brocardi."""
        self.brocardi_dock = BrocardiDockWidget(self)  # Questo è già un QDockWidget
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.brocardi_dock)

    def create_collapsible_output_dock(self):
        """Crea un dock widget collassabile per l'area di output."""
        self.output_dock = OutputArea(self)  # Crea l'istanza di OutputArea direttamente
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.output_dock)  # Aggiungi il dock alla finestra

    def show_norma_info_dock(self):
        """Mostra o nasconde il dock delle informazioni sulla norma."""
        if not self.norma_info_dock.isVisible():
            self.norma_info_dock.show()
        else:
            self.norma_info_dock.hide()

    def show_brocardi_dock(self):
        """Mostra o nasconde il dock del Brocardi."""
        if not self.brocardi_dock.isVisible():
            self.brocardi_dock.show()
        else:
            self.brocardi_dock.hide()

    def show_output_dock(self):
        """Mostra o nasconde il dock di output."""
        if not self.output_dock.isVisible():
            self.output_dock.show()
        else:
            self.output_dock.hide()
        
    def create_menu(self):
        # Barra dei menu
        menu_bar = self.menuBar()

        # Menu per le impostazioni
        settings_menu = QMenu("Impostazioni", self)
        menu_bar.addMenu(settings_menu)

        # Azione per modificare l'URL dell'API
        api_url_action = QAction("Modifica URL API", self)
        api_url_action.triggered.connect(self.change_api_url)
        settings_menu.addAction(api_url_action)

        # Aggiungi azione per la personalizzazione del tema
        theme_customize_action = QAction("Personalizza Tema", self)
        theme_customize_action.triggered.connect(self.open_theme_dialog)
        settings_menu.addAction(theme_customize_action)

    def toggle_norma_info(self):
        """Mostra o nasconde la sezione delle informazioni sulla norma."""
        self.norma_info_section.setVisible(self.norma_info_toggle_button.isChecked())

    def toggle_brocardi_dock(self):
        """Mostra o nasconde il dock widget per le informazioni sui Brocardi."""
        if self.brocardi_toggle_button.isChecked():
            self.brocardi_dock.show()
        else:
            self.brocardi_dock.hide()
    
    def get_app_version(self):
        """Ottiene la versione dell'applicazione dal file delle risorse."""
        try:
            version_file_path = get_resource_path('resources/version.txt')
            with open(version_file_path, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            logging.error("File version.txt non trovato.")
            return "0.0.1"  # Versione predefinita
        except Exception as e:
            logging.error(f"Errore nel caricamento della versione dell'app: {e}")
            return "0.0.1"

    def change_api_url(self):
        """Modifica l'URL dell'API attraverso un dialogo di input."""
        new_url, ok = QInputDialog.getText(self, "Modifica URL API", "Inserisci il nuovo URL dell'API:")
        if ok and new_url:
            self.api_url = new_url
            self.settings.setValue("api_url", self.api_url)
            QMessageBox.information(self, "URL Aggiornato", "L'URL dell'API è stato aggiornato correttamente.")
            logging.info(f"URL API aggiornato a: {self.api_url}")

    def open_theme_dialog(self):
        """Apre il dialogo per la selezione e la personalizzazione del tema."""
        self.current_theme = self.settings.value("theme", "Personalizzato")
        custom_theme = self.settings.value("custom_theme", {})

        if self.current_theme == "Personalizzato" and custom_theme:
            custom_theme = {
                'font_size': int(custom_theme.get('font_size', 14)),
                'colors': custom_theme.get('colors', ['#FFFFFF', '#000000', '#CCCCCC', '#000000'])
            }
            self.custom_theme = custom_theme
        else:
            self.custom_theme = None

        themes = ThemeManager.get_themes()  # Recupera i temi predefiniti

        dialog = ThemeDialog(self, themes=themes, current_theme=self.current_theme, custom_theme=self.custom_theme)
        if dialog.exec():
            selected_theme = dialog.get_selected_theme()
            if isinstance(selected_theme, dict):
                # Applica il tema personalizzato
                self.custom_theme = selected_theme
                self.current_theme = "Personalizzato"
                self.apply_custom_theme(self.custom_theme)
                self.save_theme_settings()  # Save custom theme settings
            else:
                # Applica il tema predefinito
                self.current_theme = selected_theme
                self.custom_theme = None
                self.change_theme(self.current_theme)  # Usa il nuovo metodo change_theme
                self.save_theme_settings()  # Save default theme setting

    def save_theme_settings(self):
        """Salva le impostazioni del tema corrente su QSettings."""
        self.settings.setValue("theme", self.current_theme)
        if self.current_theme == "Personalizzato" and self.custom_theme:
            self.settings.setValue("custom_theme", self.custom_theme)

    def load_theme_settings(self):
        """Carica le impostazioni del tema salvate e le applica all'avvio dell'app."""
        self.current_theme = self.settings.value("theme", "Tema Chiaro")
        if self.current_theme == "Personalizzato":
            self.custom_theme = self.settings.value("custom_theme", None)
            if self.custom_theme:
                self.apply_custom_theme(self.custom_theme)
        else:
            self.change_theme(self.current_theme)

    def change_theme(self, theme_name):
        """Cambia il tema dell'applicazione al tema predefinito selezionato."""
        try:
            ThemeManager.apply_custom_theme(self, ThemeManager.get_themes()[theme_name])
        except KeyError:
            QMessageBox.warning(self, "Errore", f"Tema '{theme_name}' non trovato.")
            logging.error(f"Tema '{theme_name}' non trovato.")

    def apply_custom_theme(self, custom_theme):
        """Applica il tema personalizzato."""
        try:
            ThemeManager.apply_custom_theme(self, custom_theme)
        except Exception as e:
            QMessageBox.warning(self, "Errore", "Impossibile applicare il tema personalizzato.")
            logging.error(f"Errore durante l'applicazione del tema personalizzato: {e}")

    def on_search_button_clicked(self):
        """Metodo per gestire il clic sul pulsante di ricerca."""
        # Ottieni il payload di ricerca dalla sezione di input
        payload = self.search_input_section.get_search_payload()

        # Controlla se il payload è valido
        if not payload.get('act_type'):
            QMessageBox.warning(self, "Errore di Input", "Il campo 'Tipo di Atto' è obbligatorio.")
            return

        # Genera la chiave di cache dinamicamente in base al contenuto del payload
        cache_key_parts = [f"{key}={value}" for key, value in payload.items() if value]
        cache_key = "&".join(cache_key_parts)

        # Controlla se i dati sono già nella cache
        cached_result = self.cache_manager.get_cached_data(cache_key)
        if cached_result:
            self.display_data(cached_result)
            return

        # Mostra la barra di caricamento
        self.search_input_section.search_progress_bar.setVisible(True)
        self.search_input_section.search_progress_bar.setRange(0, 0)  # Modalità indeterminata

        # Avvia il thread di fetching dei dati
        self.thread = FetchDataThread(self.api_url + "/fetch_norm", payload)
        self.thread.data_fetched.connect(lambda data: self.handle_data_fetch(data, cache_key))
        self.thread.start()

        logging.info("Ricerca avviata.")

    def handle_data_fetch(self, normavisitata, cache_key):
        """Gestisce i dati ricevuti dal thread di fetch."""
        # Nascondi la barra di caricamento dopo aver caricato i dati
        self.search_input_section.search_progress_bar.setVisible(False)

        # Caching dei dati
        self.cache_manager.cache_data(cache_key, normavisitata)

        # Visualizza i dati
        self.display_data(normavisitata)

        logging.info("Dati ricevuti dal thread di fetch.")

    def display_data(self, normavisitata):
        """Visualizza i dati normativi ricevuti e gestisce dinamicamente le sezioni informative."""
        # Pulizia delle tab dinamiche esistenti
        self.brocardi_dock.clear_dynamic_tabs()

        # Verifica se i dati ricevuti contengono un errore
        if isinstance(normavisitata, dict) and 'error' in normavisitata:
            self.output_dock.display_text(normavisitata['error'])  # Usa self.output_dock
            QMessageBox.critical(self, "Errore", normavisitata['error'])
            return

        # Aggiorna la sezione di informazioni della norma
        self.norma_info_section.update_info(normavisitata)

        # Pulisce e visualizza il testo della norma
        cleaned_text = re.sub(r'\n\s*\n', '\n', normavisitata._article_text.strip()) if normavisitata._article_text else ''
        self.output_dock.display_text(cleaned_text)  # Usa self.output_dock

        # Aggiunge informazioni sui Brocardi al widget dock
        if normavisitata._brocardi_info:
            brocardi_info = normavisitata._brocardi_info
            position = brocardi_info.get('position', "Posizione non disponibile")
            link = brocardi_info.get('link', "#")
            self.brocardi_dock.add_brocardi_info(position, link, brocardi_info.get('info', {}))

    def clipboard(self):
        """Ritorna l'oggetto clipboard dell'applicazione."""
        return QApplication.clipboard()

    def show_message(self, title, message):
        """Mostra un messaggio popup con il titolo e il messaggio forniti."""
        QMessageBox.information(self, title, message)