from PyQt6.QtWidgets import (
    QMainWindow, QStatusBar, QVBoxLayout, QWidget, QMessageBox, QInputDialog, QMenu, QApplication,
    QPushButton, QDockWidget, QSizePolicy, QHBoxLayout
)
from PyQt6.QtCore import QSettings, Qt, QSize, pyqtSlot
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from .search_input import SearchInputSection
from .norma_info import NormaInfoSection
from .brocardi_dock import BrocardiDockWidget
from .output_area import OutputArea
from .history_dock import HistoryDockWidget
from ..theming.theme_manager import ThemeManager, ThemeDialog
from ..network.data_fetcher import FetchDataThread
from ..utils.helpers import get_resource_path
from ..utils.cache_manager import CacheManager
from ..tools.map import FONTI_PRINCIPALI
from ..tools.text_op import clean_text, clean_article_input
from ..tools.norma import NormaVisitata
from ..utils.updater import UpdateNotifier
import logging
import subprocess
import threading
import sys
import os

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class NormaViewer(QMainWindow):
    def __init__(self):
        logging.info("Inizializzazione di NormaViewer.")
        super().__init__()
        self.setWindowTitle(f"VisuaLex v{self.get_app_version()}")
        self.setGeometry(100, 100, 900, 700)
        logging.debug("Titolo e geometria della finestra impostati.")

        # Inizializza UpdateNotifier
        self.update_notifier = UpdateNotifier(self)
        logging.debug("UpdateNotifier inizializzato.")

        # Configura il sistema di aggiornamento
        self.update_thread = None  # Thread per il controllo degli aggiornamenti
        self.download_thread = None  # Thread per il download e aggiornamento
        logging.debug("Thread di aggiornamento configurati.")

        # Abilitare il nesting e animazioni nei dock
        self.setDockNestingEnabled(True)
        self.setDockOptions(
            QMainWindow.DockOption.AnimatedDocks | 
            QMainWindow.DockOption.AllowNestedDocks | 
            QMainWindow.DockOption.AllowTabbedDocks
        )
        logging.debug("Opzioni dei dock impostate.")

        # Setup UI components
        self.setup_ui()

        # Crea l'icona di aggiornamento
        self.create_update_icon()

        # Configurare una cache manager
        self.cache_manager = CacheManager()
        logging.debug("CacheManager configurato.")

        # Carica le impostazioni del tema salvate
        self.load_theme_settings()
        logging.debug("Impostazioni del tema caricate.")

        self.normavisitate = []  # Lista per memorizzare tutte le norme visitate
        self.current_index = 0  # Indice dell'articolo attualmente visualizzato
        self.current_article = None  # Tiene traccia dell'articolo attuale nel `tree`
        logging.debug("Variabili di stato inizializzate.")

    def setup_ui(self):
        logging.debug("Impostazione dell'interfaccia utente.")
        # Impostazioni dell'applicazione
        self.settings = QSettings("NormaApp", "NormaViewer")
        self.api_url = self.settings.value("api_url", "https://localhost:8000")  # URL di default
        logging.debug(f"URL API impostato: {self.api_url}")
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        logging.debug("Barra di stato creata.")

        self.fonti_principali = FONTI_PRINCIPALI
        logging.debug("Fonti principali caricate.")
        self.create_menu()
        logging.debug("Menu creato.")

        # Layout principale
        main_layout = QVBoxLayout()

        # Sezione di input di ricerca
        self.search_input_section = SearchInputSection(self)
        logging.debug("Sezione di input di ricerca creata.")
        main_layout.addWidget(self.search_input_section)

        # Pulsanti di navigazione "Indietro" e "Avanti"
        self.previous_button = QPushButton("Indietro")
        self.previous_button.clicked.connect(self.show_previous_article)
        self.previous_button.setEnabled(False)
        logging.debug("Pulsante 'Indietro' creato.")

        self.next_button = QPushButton("Avanti")
        self.next_button.clicked.connect(self.show_next_article)
        self.next_button.setEnabled(False)
        logging.debug("Pulsante 'Avanti' creato.")

        # Layout per i pulsanti di navigazione (centrato orizzontalmente)
        navigation_layout = QHBoxLayout()
        navigation_layout.addStretch(1)
        navigation_layout.addWidget(self.previous_button)
        navigation_layout.addSpacing(10)
        navigation_layout.addWidget(self.next_button)
        navigation_layout.addStretch(1)
        logging.debug("Layout di navigazione creato.")

        # Aggiungi il layout dei pulsanti di navigazione al layout principale
        main_layout.addLayout(navigation_layout)

        # Widget centrale
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        logging.debug("Widget centrale impostato.")

        # Creare i dock
        self.create_collapsible_norma_info_dock()
        logging.debug("Dock delle informazioni sulla norma creato.")
        self.create_collapsible_brocardi_dock()
        logging.debug("Dock dei Brocardi creato.")
        self.create_collapsible_output_dock()
        logging.debug("Dock dell'output creato.")
        self.create_collapsible_history_dock()
        logging.debug("Dock della cronologia creato.")

        # Impostazioni di default per il widget centrale
        self.centralWidget().setMinimumSize(350, 420)  # Dimensioni minime ragionevoli
        logging.debug("Dimensioni minime del widget centrale impostate.")
        self.setup_shortcuts()
        logging.debug("Scorciatoie da tastiera configurate.")
        # Verifica la presenza di aggiornamenti all'avvio
        self.manual_update_check()
        logging.debug("Controllo manuale degli aggiornamenti avviato.")

    def create_update_icon(self):
        """Crea un'icona di notifica per l'aggiornamento e la aggiunge alla barra di stato."""
        logging.debug("Creazione dell'icona di aggiornamento.")
        try:
            # Crea un'azione con l'icona per l'aggiornamento
            update_action = QAction("Aggiornamento Disponibile", self)
            update_action.setToolTip("Clicca per verificare l'aggiornamento")
            update_action.triggered.connect(self.manual_update_check)  # Connette al controllo manuale

            # Aggiungi l'icona alla barra di stato
            self.statusBar().addAction(update_action)
            update_action.setVisible(True)
            logging.info("Icona di aggiornamento aggiunta alla barra di stato.")
        except Exception as e:
            logging.error(f"Errore durante la creazione dell'icona di aggiornamento: {e}")

    def manual_update_check(self):
        """Metodo per avviare manualmente il controllo degli aggiornamenti."""
        logging.debug("Avvio del controllo manuale degli aggiornamenti.")

        current_version = self.get_app_version()
        logging.debug(f"Versione corrente dell'applicazione: {current_version}")

        self.update_notifier.check_for_update(current_version)

    @pyqtSlot(bool, str)
    def on_update_checked(self, is_newer, latest_version):
        """Slot chiamato quando il controllo degli aggiornamenti è completo."""
        if is_newer:
            logging.info(f"Trovata nuova versione: {latest_version}. Avvio del processo di aggiornamento.")
            self.update_notifier.prompt_update()
        else:
            logging.info("L'applicazione è già aggiornata.")
            self.show_no_update_message()
        
    @pyqtSlot(bool, str)
    def on_update_completed(self, success, message):
        """Slot chiamato quando l'aggiornamento è completo."""
        if success:
            logging.info("Aggiornamento completato con successo.")
            QMessageBox.information(
                self, "Aggiornamento Completato",
                f"L'applicazione è stata aggiornata e si trova in:\n{message}\n"
                "Sostituisci manualmente la tua applicazione con la nuova versione."
            )
            # Apri la cartella dove si trova l'applicazione aggiornata
            subprocess.Popen(['open', os.path.dirname(message)])
        else:
            logging.error(f"Aggiornamento fallito: {message}")
            QMessageBox.warning(self, "Aggiornamento Fallito", message)

    @pyqtSlot()
    def show_no_update_message(self):
        """Mostra un messaggio quando non ci sono aggiornamenti disponibili."""
        logging.info("Nessun aggiornamento disponibile.")
        QMessageBox.information(self, "Nessun Aggiornamento", "La tua applicazione è già aggiornata.")

    def get_app_version(self):
        """Ottiene la versione dell'applicazione dal file delle risorse."""
        try:
            version_file_path = get_resource_path('version.txt')
            logging.debug(f"Percorso del file version.txt: {version_file_path}")
            with open(version_file_path, 'r') as f:
                version = f.read().strip()
                logging.debug(f"Versione letta dal file: {version}")
                return version
        except FileNotFoundError:
            logging.error("File version.txt non trovato.")
            return "0.0.1"  # Versione predefinita
        except Exception as e:
            logging.error(f"Errore nel caricamento della versione dell'app: {e}")
            return "0.0.1"

    def moveEvent(self, event):
        """Evento chiamato quando la finestra viene spostata."""
        logging.debug("Evento moveEvent chiamato.")
        self.adjust_window_size()
        super().moveEvent(event)

    def resizeEvent(self, event):
        """Evento chiamato quando la finestra viene ridimensionata."""
        logging.debug("Evento resizeEvent chiamato.")
        self.adjust_window_size()
        super().resizeEvent(event)

    def adjust_window_size(self):
        """Regola la dimensione della finestra per evitare che esca dai limiti dello schermo disponibile."""
        logging.debug("Regolazione delle dimensioni della finestra.")
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        window_geometry = self.frameGeometry()

        # Verifica i bordi a destra e ridimensiona la larghezza se necessario
        if window_geometry.right() > screen_geometry.right():
            new_width = screen_geometry.width() - window_geometry.left()
            self.resize(new_width, self.height())
            logging.debug("Larghezza della finestra regolata per adattarsi allo schermo.")

        # Verifica i bordi a sinistra e ridimensiona la larghezza se necessario
        if window_geometry.left() < screen_geometry.left():
            self.move(screen_geometry.left(), window_geometry.top())
            logging.debug("Posizione della finestra regolata per adattarsi allo schermo.")

        # Verifica i bordi in basso e ridimensiona l'altezza se necessario
        if window_geometry.bottom() > screen_geometry.bottom():
            new_height = screen_geometry.height() - window_geometry.top()
            self.resize(self.width(), new_height)
            logging.debug("Altezza della finestra regolata per adattarsi allo schermo.")

        # Verifica i bordi in alto e ridimensiona l'altezza se necessario
        if window_geometry.top() < screen_geometry.top():
            self.move(window_geometry.left(), screen_geometry.top())
            logging.debug("Posizione verticale della finestra regolata per adattarsi allo schermo.")

    def create_collapsible_norma_info_dock(self):
        """Crea un dock widget collassabile per le informazioni sulla norma."""
        logging.debug("Creazione del dock delle informazioni sulla norma.")
        self.norma_info_section = NormaInfoSection(self)
        self.norma_info_dock = QDockWidget("Informazioni sulla Norma", self)
        self.norma_info_dock.setWidget(self.norma_info_section)

        # Impostazioni del dock
        self.norma_info_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                                         QDockWidget.DockWidgetFeature.DockWidgetClosable |
                                         QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        
        # Usa QSizePolicy con espandibilità per permettere il ridimensionamento
        self.norma_info_dock.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))
        self.norma_info_dock.setMinimumSize(QSize(200, 150))  # Dimensioni minime ragionevoli
        self.norma_info_dock.setVisible(False)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.norma_info_dock)
        logging.debug("Dock delle informazioni sulla norma aggiunto alla finestra principale.")

    def create_collapsible_brocardi_dock(self):
        """Crea un dock widget collassabile per le informazioni sui Brocardi."""
        logging.debug("Creazione del dock dei Brocardi.")
        self.brocardi_dock = BrocardiDockWidget(self)
        self.brocardi_dock.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))
        self.brocardi_dock.setMinimumSize(QSize(75, 50))  # Ridurre le dimensioni minime per i dock
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.brocardi_dock)
        logging.debug("Dock dei Brocardi aggiunto alla finestra principale.")

    def create_collapsible_output_dock(self):
        """Crea un dock widget collassabile per l'area di output."""
        logging.debug("Creazione del dock dell'output.")
        self.output_dock = OutputArea(self)
        self.output_dock.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.output_dock)
        logging.debug("Dock dell'output aggiunto alla finestra principale.")

    def create_collapsible_history_dock(self):
        """Crea un dock widget collassabile per la cronologia delle ricerche."""
        logging.debug("Creazione del dock della cronologia.")
        self.history_dock = HistoryDockWidget(self)
        self.history_dock.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))
        self.history_dock.setMinimumSize(QSize(200, 100))  # Dimensioni minime ragionevoli
        self.history_dock.setVisible(False)  # Nascondi inizialmente
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.history_dock)
        logging.debug("Dock della cronologia aggiunto alla finestra principale.")

    def toggle_history_dock(self):
        """Mostra o nasconde il dock della cronologia."""
        logging.debug("Alternanza della visibilità del dock della cronologia.")
        if self.history_dock.isVisible():
            self.history_dock.hide()  # Nascondi se visibile
            logging.debug("Dock della cronologia nascosto.")
        else:
            self.history_dock.show()  # Mostra se nascosto
            logging.debug("Dock della cronologia mostrato.")

    def show_norma_info_dock(self):
        """Mostra o nasconde il dock delle informazioni sulla norma."""
        logging.debug("Alternanza della visibilità del dock delle informazioni sulla norma.")
        if not self.norma_info_dock.isVisible():
            self.norma_info_dock.show()
            logging.debug("Dock delle informazioni sulla norma mostrato.")
        else:
            self.norma_info_dock.hide()
            logging.debug("Dock delle informazioni sulla norma nascosto.")

    def show_brocardi_dock(self):
        """Mostra o nasconde il dock del Brocardi."""
        logging.debug("Alternanza della visibilità del dock dei Brocardi.")
        if not self.brocardi_dock.isVisible():
            self.brocardi_dock.show()
            logging.debug("Dock dei Brocardi mostrato.")
        else:
            self.brocardi_dock.hide()
            logging.debug("Dock dei Brocardi nascosto.")

    def show_output_dock(self):
        """Mostra o nasconde il dock di output."""
        logging.debug("Alternanza della visibilità del dock dell'output.")
        if not self.output_dock.isVisible():
            self.output_dock.show()
            logging.debug("Dock dell'output mostrato.")
        else:
            self.output_dock.hide()
            logging.debug("Dock dell'output nascosto.")

    def create_menu(self):
        logging.debug("Creazione della barra dei menu.")
        # Barra dei menu
        menu_bar = self.menuBar()

        # Menu per le impostazioni
        settings_menu = QMenu("Impostazioni", self)
        menu_bar.addMenu(settings_menu)

        # Azione per modificare l'URL dell'API
        api_url_action = QAction("Modifica URL API", self)
        api_url_action.triggered.connect(self.change_api_url)
        settings_menu.addAction(api_url_action)
        logging.debug("Azione per modificare l'URL dell'API aggiunta al menu.")

        # Aggiungi azione per la personalizzazione del tema
        theme_customize_action = QAction("Personalizza Tema", self)
        theme_customize_action.triggered.connect(self.open_theme_dialog)
        settings_menu.addAction(theme_customize_action)
        logging.debug("Azione per personalizzare il tema aggiunta al menu.")

        # Aggiungi azione per il controllo manuale degli aggiornamenti
        check_update_action = QAction("Controlla Aggiornamenti", self)
        check_update_action.triggered.connect(self.manual_update_check)
        settings_menu.addAction(check_update_action)
        logging.debug("Azione per controllare gli aggiornamenti aggiunta al menu.")

        # Aggiungi azione per mostrare/nascondere la cronologia
        toggle_history_action = QAction("Mostra/Nascondi cronologia", self)
        toggle_history_action.triggered.connect(self.toggle_history_dock)
        settings_menu.addAction(toggle_history_action)
        logging.debug("Azione per mostrare/nascondere la cronologia aggiunta al menu.")

    def toggle_norma_info(self):
        """Mostra o nasconde la sezione delle informazioni sulla norma."""
        logging.debug("Alternanza della visibilità della sezione delle informazioni sulla norma.")
        self.norma_info_section.setVisible(self.norma_info_toggle_button.isChecked())

    def toggle_brocardi_dock(self):
        """Mostra o nasconde il dock widget per le informazioni sui Brocardi."""
        logging.debug("Alternanza della visibilità del dock dei Brocardi.")
        if self.brocardi_toggle_button.isChecked():
            self.brocardi_dock.show()
            logging.debug("Dock dei Brocardi mostrato.")
        else:
            self.brocardi_dock.hide()
            logging.debug("Dock dei Brocardi nascosto.")

    def change_api_url(self):
        """Modifica l'URL dell'API attraverso un dialogo di input."""
        logging.debug("Apertura del dialogo per modificare l'URL dell'API.")
        new_url, ok = QInputDialog.getText(self, "Modifica URL API", "Inserisci il nuovo URL dell'API:")
        if ok and new_url:
            self.api_url = new_url
            self.settings.setValue("api_url", self.api_url)
            QMessageBox.information(self, "URL Aggiornato", "L'URL dell'API è stato aggiornato correttamente.")
            logging.info(f"URL API aggiornato a: {self.api_url}")
        else:
            logging.debug("Modifica dell'URL API annullata o input non valido.")

    def open_theme_dialog(self):
        """Apre il dialogo per la selezione e la personalizzazione del tema."""
        logging.debug("Apertura del dialogo per la personalizzazione del tema.")
        self.current_theme = self.settings.value("theme", "Personalizzato")
        custom_theme = self.settings.value("custom_theme", {})

        if self.current_theme == "Personalizzato" and custom_theme:
            custom_theme = {
                'font_size': int(custom_theme.get('font_size', 14)),
                'colors': custom_theme.get('colors', ['#FFFFFF', '#000000', '#CCCCCC', '#000000'])
            }
            self.custom_theme = custom_theme
            logging.debug("Tema personalizzato caricato.")
        else:
            self.custom_theme = None
            logging.debug("Nessun tema personalizzato trovato.")

        themes = ThemeManager.get_themes()  # Recupera i temi predefiniti
        logging.debug("Temi predefiniti recuperati.")

        dialog = ThemeDialog(self, themes=themes, current_theme=self.current_theme, custom_theme=self.custom_theme)
        if dialog.exec():
            selected_theme = dialog.get_selected_theme()
            if isinstance(selected_theme, dict):
                # Applica il tema personalizzato
                self.custom_theme = selected_theme
                self.current_theme = "Personalizzato"
                self.apply_custom_theme(self.custom_theme)
                self.save_theme_settings()  # Save custom theme settings
                logging.info("Tema personalizzato applicato e salvato.")
            else:
                # Applica il tema predefinito
                self.current_theme = selected_theme
                self.custom_theme = None
                self.change_theme(self.current_theme)  # Usa il nuovo metodo change_theme
                self.save_theme_settings()  # Save default theme setting
                logging.info(f"Tema predefinito '{self.current_theme}' applicato e salvato.")
        else:
            logging.debug("Dialogo di personalizzazione del tema annullato.")

    def save_theme_settings(self):
        """Salva le impostazioni del tema corrente su QSettings."""
        logging.debug("Salvataggio delle impostazioni del tema.")
        self.settings.setValue("theme", self.current_theme)
        if self.current_theme == "Personalizzato" and self.custom_theme:
            self.settings.setValue("custom_theme", self.custom_theme)
            logging.debug("Impostazioni del tema personalizzato salvate.")

    def load_theme_settings(self):
        """Carica le impostazioni del tema salvate e le applica all'avvio dell'app."""
        logging.debug("Caricamento delle impostazioni del tema.")
        self.current_theme = self.settings.value("theme", "Tema Chiaro")
        if self.current_theme == "Personalizzato":
            self.custom_theme = self.settings.value("custom_theme", None)
            if self.custom_theme:
                self.apply_custom_theme(self.custom_theme)
                logging.debug("Tema personalizzato applicato.")
        else:
            self.change_theme(self.current_theme)
            logging.debug(f"Tema predefinito '{self.current_theme}' applicato.")

    def change_theme(self, theme_name):
        """Cambia il tema dell'applicazione al tema predefinito selezionato."""
        logging.debug(f"Cambio del tema a '{theme_name}'.")
        try:
            ThemeManager.apply_custom_theme(self, ThemeManager.get_themes()[theme_name])
            logging.info(f"Tema '{theme_name}' applicato con successo.")
        except KeyError:
            QMessageBox.warning(self, "Errore", f"Tema '{theme_name}' non trovato.")
            logging.error(f"Tema '{theme_name}' non trovato.")

    def apply_custom_theme(self, custom_theme):
        """Applica il tema personalizzato."""
        logging.debug("Applicazione del tema personalizzato.")
        try:
            ThemeManager.apply_custom_theme(self, custom_theme)
            logging.info("Tema personalizzato applicato con successo.")
        except Exception as e:
            QMessageBox.warning(self, "Errore", "Impossibile applicare il tema personalizzato.")
            logging.error(f"Errore durante l'applicazione del tema personalizzato: {e}")

    def on_search_button_clicked(self):
        """Metodo per gestire il clic sul pulsante di ricerca."""
        logging.debug("Pulsante di ricerca cliccato.")
        # Ottieni il payload di ricerca dalla sezione di input
        payload = self.search_input_section.get_search_payload()
        logging.debug(f"Payload di ricerca ottenuto: {payload}")

        # Controlla se il payload è valido
        if not payload.get('act_type'):
            logging.warning("Campo 'Tipo di Atto' mancante nel payload di ricerca.")
            QMessageBox.warning(self, "Errore di Input", "Il campo 'Tipo di Atto' è obbligatorio.")
            return

        # Pulisce le tab di Brocardi e l'output prima di iniziare una nuova ricerca
        self.brocardi_dock.clear_dynamic_tabs()  # Svuota tutte le tab di Brocardi
        self.output_dock.clear()  # Pulisce l'area di output
        logging.debug("Tab di Brocardi e area di output pulite.")

        # Genera la chiave di cache dinamicamente in base al contenuto del payload
        cache_key_parts = [f"{key}={value}" for key, value in payload.items() if value]
        cache_key = "&".join(cache_key_parts)
        logging.debug(f"Chiave di cache generata: {cache_key}")

        # Controlla se i dati sono già nella cache
        cached_result = self.cache_manager.get_cached_data(cache_key)
        if cached_result:
            logging.info("Risultato trovato nella cache.")
            self.handle_data_fetch(cached_result, cache_key)
            return

        # Mostra la barra di caricamento
        self.search_input_section.search_progress_bar.setVisible(True)
        self.search_input_section.search_progress_bar.setRange(0, 0)  # Modalità indeterminata
        logging.debug("Barra di progresso della ricerca mostrata.")

        # Avvia il thread di fetching dei dati
        self.thread = FetchDataThread(url=self.api_url+'/fetch_all_data', payload=payload, endpoint_type="fetch_all_data")
        self.thread.data_fetched.connect(lambda data: self.handle_data_fetch(data, cache_key))
        self.thread.start()
        logging.info("Thread di fetching dei dati avviato.")

    def handle_data_fetch(self, normavisitate, cache_key):
        """Gestisce i dati ricevuti dal thread di fetch."""
        logging.debug("Dati ricevuti dal thread di fetch.")
        self.search_input_section.search_progress_bar.setVisible(False)

        # Controllo degli errori
        if isinstance(normavisitate, dict) and 'error' in normavisitate:
            logging.error(f"Errore dal fetching dei dati: {normavisitate['error']}")
            QMessageBox.critical(self, "Errore", normavisitate['error'])
            return

        # Salva i risultati nella cache
        self.cache_manager.cache_data(cache_key, normavisitate)
        logging.debug("Risultati salvati nella cache.")

        # Verifica se è una ricerca multipla o singola
        if isinstance(normavisitate, list):
            logging.debug("Risultati multipli ricevuti.")
            logging.debug(f"Numero di risultati ricevuti: {len(normavisitate)}")

            self.normavisitate = normavisitate  # Salva la lista dei risultati
            self.current_index = 0  # Ripristina l'indice all'inizio

            # Aggiungi la ricerca multipla alla cronologia
            self.history_dock.add_search_to_history(self.normavisitate)
            logging.debug("Ricerca multipla aggiunta alla cronologia.")

            # Pulisci il dock di Brocardi e l'area di output
            self.brocardi_dock.clear_dynamic_tabs()
            self.output_dock.clear()

            # Visualizza il primo articolo
            self.update_navigation_buttons()
            self.display_data(self.normavisitate[self.current_index])

        elif isinstance(normavisitate, NormaVisitata):
            logging.debug("Risultato singolo ricevuto.")
            logging.debug(f"Risultato dell'API: {normavisitate}")

            # Gestione della ricerca singola
            self.normavisitate = [normavisitate]

            # Aggiungi la ricerca singola alla cronologia
            self.history_dock.add_search_to_history(normavisitate)
            logging.debug("Ricerca singola aggiunta alla cronologia.")

            # Pulisci il dock di Brocardi e l'area di output
            self.brocardi_dock.clear_dynamic_tabs()
            self.output_dock.clear()

            # Visualizza l'articolo
            self.current_index = 0
            self.update_navigation_buttons()
            self.display_data(self.normavisitate[self.current_index])

        else:
            logging.error("Formato dei dati ricevuti non riconosciuto.")
            QMessageBox.critical(self, "Errore", "Formato dei dati ricevuti non riconosciuto.")

    def display_data(self, normavisitata):
        """Visualizza un singolo articolo e le informazioni correlate."""
        logging.info(f"Inizio visualizzazione dei dati per l'articolo: {normavisitata.numero_articolo}.")
        logging.debug(f"Dettagli di normavisitata: {normavisitata}")

        # Pulisce le tab dinamiche di Brocardi prima di visualizzare nuovi dati
        logging.info("Pulizia delle tab dinamiche di Brocardi in corso.")
        self.brocardi_dock.clear_dynamic_tabs()
        logging.debug("Tab dinamiche di Brocardi pulite con successo.")

        # Aggiorna la sezione di informazioni sulla norma
        logging.info("Aggiornamento della sezione informazioni sulla norma.")
        self.norma_info_section.update_info(normavisitata)
        logging.debug("Sezione informazioni sulla norma aggiornata con i dati di normavisitata.")

        # Visualizza il testo dell'articolo
        if normavisitata._article_text:
            logging.info("Pulizia del testo dell'articolo.")
            cleaned_text = clean_text(normavisitata._article_text)
            logging.debug(f"Testo dell'articolo dopo la pulizia: {cleaned_text}")
        else:
            logging.warning("Testo dell'articolo mancante in normavisitata.")
            cleaned_text = ''
        logging.info("Visualizzazione del testo dell'articolo nell'output dock.")
        self.output_dock.display_text(cleaned_text)
        logging.debug("Testo dell'articolo visualizzato nell'output dock.")

        # Visualizza le informazioni Brocardi (se presenti)
        brocardi_info = normavisitata._brocardi_info if normavisitata._brocardi_info else None
        if brocardi_info:
            logging.info("Informazioni Brocardi trovate, elaborazione in corso.")
            logging.debug(f"Dettagli di brocardi_info: {brocardi_info}")
            position = brocardi_info.get('position', "").strip()
            link = brocardi_info.get('link', "#")
            brocardi_details = {
                'Brocardi': brocardi_info.get('Brocardi'),
                'Ratio': brocardi_info.get('Ratio'),
                'Spiegazione': brocardi_info.get('Spiegazione'),
                'Massime': brocardi_info.get('Massime')
            }
            # Aggiungi tutte le informazioni di Brocardi al dock
            self.brocardi_dock.add_brocardi_info(position, link, brocardi_details)
            logging.debug("Informazioni Brocardi visualizzate nel brocardi_dock.")
        else:
            logging.warning("Nessuna informazione Brocardi presente in normavisitata.")
            self.brocardi_dock.hide()
            logging.debug("brocardi_dock nascosto poiché brocardi_info è assente.")

        logging.info(f"Fine visualizzazione dei dati per l'articolo: {normavisitata.numero_articolo}.")

    def load_multiple_articles_from_history(self, normavisitate):
        """Carica una ricerca multipla dalla cronologia."""
        logging.debug("Caricamento di articoli multipli dalla cronologia.")
        self.normavisitate = normavisitate
        self.current_index = 0
        self.update_navigation_buttons()
        self.display_data(self.normavisitate[self.current_index])

    def load_single_article_from_history(self, norma_visitata):
        """Carica una singola ricerca dalla cronologia."""
        logging.debug("Caricamento di un articolo singolo dalla cronologia.")
        self.normavisitate = [norma_visitata]
        self.current_index = 0
        self.update_navigation_buttons()
        self.display_data(self.normavisitate[self.current_index])

    def update_navigation_buttons(self):
        """Abilita o disabilita i pulsanti e gestisce la visibilità in base alla presenza di più articoli."""
        logging.debug("Aggiornamento dei pulsanti di navigazione.")
        if len(self.normavisitate) > 1:
            # Mostra i pulsanti e abilita/disabilita in base alla posizione
            self.previous_button.setVisible(True)
            self.next_button.setVisible(True)
            self.previous_button.setEnabled(self.current_index > 0)
            self.next_button.setEnabled(self.current_index < len(self.normavisitate) - 1)
            logging.debug("Pulsanti di navigazione aggiornati per risultati multipli.")
        else:
            # Nascondi i pulsanti se c'è solo un articolo
            self.previous_button.setVisible(False)
            self.next_button.setVisible(False)
            logging.debug("Pulsanti di navigazione nascosti per risultato singolo.")

    def show_previous_article(self):
        """Mostra l'articolo precedente nei risultati di ricerca multipla."""
        logging.debug("Navigazione all'articolo precedente.")
        if self.current_index > 0:
            self.current_index -= 1
            self.display_data(self.normavisitate[self.current_index])
            self.update_navigation_buttons()
            logging.debug(f"Articolo precedente mostrato: indice {self.current_index}.")

    def show_next_article(self):
        """Mostra l'articolo successivo nei risultati di ricerca multipla."""
        logging.debug("Navigazione all'articolo successivo.")
        if self.current_index < len(self.normavisitate) - 1:
            self.current_index += 1
            self.display_data(self.normavisitate[self.current_index])
            self.update_navigation_buttons()
            logging.debug(f"Articolo successivo mostrato: indice {self.current_index}.")

    
    def clipboard(self):
        """Ritorna l'oggetto clipboard dell'applicazione."""
        logging.debug("Accesso alla clipboard dell'applicazione.")
        return QApplication.clipboard()

    def show_message(self, title, message):
        """Mostra un messaggio popup con il titolo e il messaggio forniti."""
        logging.debug(f"Mostra messaggio: {title} - {message}")
        QMessageBox.information(self, title, message)

    def setup_shortcuts(self):
        """Configura le scorciatoie da tastiera."""
        logging.debug("Configurazione delle scorciatoie da tastiera.")
        # Scorciatoia per il tasto 'Invio' che avvia la ricerca
        enter_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        enter_shortcut.activated.connect(self.on_search_button_clicked)
        logging.debug("Scorciatoia per il tasto 'Invio' configurata.")

        # Scorciatoia per 'Ctrl+R' che riavvia l'applicazione
        restart_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        restart_shortcut.activated.connect(self.restart_application)
        logging.debug("Scorciatoia per 'Ctrl+R' configurata.")

        # Determina il modificatore in base al sistema operativo
        if sys.platform == "darwin":  # macOS
            modifier = Qt.KeyboardModifier.MetaModifier  # Usa Cmd su macOS
        else:  # Windows/Linux
            modifier = Qt.KeyboardModifier.ControlModifier  # Usa Ctrl su Windows/Linux

        # Scorciatoia per mostrare/nascondere la cronologia con Cmd+T (Ctrl+T su Windows/Linux)
        history_shortcut = QShortcut(QKeySequence(modifier | Qt.Key.Key_T), self)
        history_shortcut.activated.connect(self.toggle_history_dock)
        logging.debug("Scorciatoia per mostrare/nascondere la cronologia configurata.")

        # Scorciatoia per navigare agli articoli precedenti con Cmd+A (Ctrl+A su Windows/Linux)
        previous_article_shortcut = QShortcut(QKeySequence(modifier | Qt.Key.Key_A), self)
        previous_article_shortcut.activated.connect(self.show_previous_article)
        logging.debug("Scorciatoia per l'articolo precedente configurata.")

        # Scorciatoia per navigare agli articoli successivi con Cmd+D (Ctrl+D su Windows/Linux)
        next_article_shortcut = QShortcut(QKeySequence(modifier | Qt.Key.Key_D), self)
        next_article_shortcut.activated.connect(self.show_next_article)
        logging.debug("Scorciatoia per l'articolo successivo configurata.")

    def restart_application(self):
        """Riavvia l'applicazione quando si preme Ctrl+R."""
        logging.info("Riavvio dell'applicazione richiesto.")
        QMessageBox.information(self, "Riavvio", "Riavvio dell'applicazione...")
        # Salva il percorso dell'eseguibile corrente
        python = sys.executable
        # Comando per riavviare l'applicazione
        subprocess.Popen([python] + sys.argv)
        logging.debug("Comando di riavvio dell'applicazione eseguito.")
        # Chiudi l'applicazione corrente
        QApplication.quit()
