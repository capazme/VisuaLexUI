from PyQt6.QtWidgets import (QMainWindow, QStatusBar, QVBoxLayout, QWidget, QMessageBox, QInputDialog, QMenu, QApplication, 
                             QPushButton, QDockWidget, QSizePolicy, QMessageBox, QProgressDialog, QHBoxLayout)

from PyQt6.QtCore import QSettings, Qt, QSize, pyqtSlot, QThread
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QShortcut
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
from ..utils.updater import UpdateNotifier, UpdateCheckWorker, ProgressDialog
import logging
import subprocess
import threading
import sys
import os

class NormaViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"VisuaLex v{self.get_app_version()}")
        self.setGeometry(100, 100, 900, 700)
        # Inizializza UpdateNotifier
        self.update_notifier = UpdateNotifier(self)
        # Configura il sistema di aggiornamento
        self.update_thread = None  # Thread per il controllo degli aggiornamenti
        self.download_thread = None  # Thread per il download e aggiornamento
   
        # Abilitare il nesting e animazioni nei dock
        self.setDockNestingEnabled(True)
        self.setDockOptions(
            QMainWindow.DockOption.AnimatedDocks | 
            QMainWindow.DockOption.AllowNestedDocks | 
            QMainWindow.DockOption.AllowTabbedDocks
        )

        # Setup UI components
        self.setup_ui()

        # Crea l'icona di aggiornamento
        self.create_update_icon()
        
        # Crea la cronologia delle ricerche
        self.create_collapsible_history_dock()

        # Configurare una cache manager
        self.cache_manager = CacheManager()

        # Carica le impostazioni del tema salvate
        self.load_theme_settings()
        
        self.normavisitate = []  # Lista per memorizzare tutte le norme visitate
        self.current_index = 0  # Indice dell'articolo attualmente visualizzato
        self.current_article = None  # Tiene traccia dell'articolo attuale nel `tree`


    def setup_ui(self):
        # Impostazioni dell'applicazione
        self.settings = QSettings("NormaApp", "NormaViewer")
        self.api_url = self.settings.value("api_url", "https://localhost:8000")  # URL di default
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        

        # Crea l'icona di aggiornamento
        self.update_icon = self.create_update_icon()

        self.fonti_principali = FONTI_PRINCIPALI
        self.create_menu()

        # Layout principale
        main_layout = QVBoxLayout()

        
        # Sezione di input di ricerca
        self.search_input_section = SearchInputSection(self)
        #self.search_input_section.setMinimumWidth(400)
        #self.search_input_section.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed))
        
        main_layout.addWidget(self.search_input_section)

        # Pulsanti di navigazione "Indietro" e "Avanti"
        self.previous_button = QPushButton("Indietro")
        self.previous_button.clicked.connect(self.show_previous_article)
        self.previous_button.setEnabled(False)

        self.next_button = QPushButton("Avanti")
        self.next_button.clicked.connect(self.show_next_article)
        self.next_button.setEnabled(False)

        # Layout per i pulsanti di navigazione (centrato orizzontalmente)
        navigation_layout = QHBoxLayout()
        navigation_layout.addStretch(1)
        navigation_layout.addWidget(self.previous_button)
        navigation_layout.addSpacing(10)
        navigation_layout.addWidget(self.next_button)
        navigation_layout.addStretch(1)

        # Aggiungi il layout dei pulsanti di navigazione al layout principale
        main_layout.addLayout(navigation_layout)

        """ # Aggiungi pulsante per attivare/disattivare la cronologia
        self.toggle_history_button = QPushButton("Mostra/Nascondi Cronologia")
        self.toggle_history_button.clicked.connect(self.toggle_history_dock)
        main_layout.addWidget(self.toggle_history_button)  # Aggiungi il pulsante alla UI
 """

            
        # Widget centrale
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Creare i dock
        self.create_collapsible_norma_info_dock()
        self.create_collapsible_brocardi_dock()
        self.create_collapsible_output_dock()
        self.create_collapsible_history_dock()  # Crea il dock della cronologia


        # Impostazioni di default per il widget centrale
        self.centralWidget().setMinimumSize(350, 420)  # Dimensioni minime ragionevoli
        self.setup_shortcuts()
        # Verifica la presenza di aggiornamenti all'avvio
        self.manual_update_check()

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
            QMessageBox.information(
                self, "Aggiornamento Completato",
                f"L'applicazione è stata aggiornata e si trova in:\n{message}\n"
                "Sostituisci manualmente la tua applicazione con la nuova versione."
            )
            logging.info("Aggiornamento completato con successo.")
            # Apri la cartella dove si trova l'applicazione aggiornata
            subprocess.Popen(['open', os.path.dirname(message)])
        else:
            QMessageBox.warning(self, "Aggiornamento Fallito", message)
            logging.error(f"Aggiornamento fallito: {message}")

    @pyqtSlot()
    def show_no_update_message(self):
        """Mostra un messaggio quando non ci sono aggiornamenti disponibili."""
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
        self.adjust_window_size()
        super().moveEvent(event)

    def resizeEvent(self, event):
        """Evento chiamato quando la finestra viene ridimensionata."""
        super().resizeEvent(event)
        self.adjust_window_size()

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

    def create_collapsible_brocardi_dock(self):
        """Crea un dock widget collassabile per le informazioni sui Brocardi."""
        self.brocardi_dock = BrocardiDockWidget(self)
        self.brocardi_dock.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))
        self.brocardi_dock.setMinimumSize(QSize(75, 50))  # Ridurre le dimensioni minime per i dock
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.brocardi_dock)

    def create_collapsible_output_dock(self):
        """Crea un dock widget collassabile per l'area di output."""
        self.output_dock = OutputArea(self)
        self.output_dock.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))
        #self.output_dock.setMinimumSize(QSize(75, 37))  # Ridurre le dimensioni minime per i dock
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.output_dock)

    def create_collapsible_history_dock(self):
        """Crea un dock widget collassabile per la cronologia delle ricerche."""
        self.history_dock = HistoryDockWidget(self)
        self.history_dock.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))
        self.history_dock.setMinimumSize(QSize(200, 100))  # Dimensioni minime ragionevoli
        self.history_dock.setVisible(False)  # Nascondi inizialmente
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.history_dock)

    def toggle_history_dock(self):
        """Mostra o nasconde il dock della cronologia."""
        if self.history_dock.isVisible():
            self.history_dock.hide()  # Nascondi se visibile
        else:
            self.history_dock.show()  # Mostra se nascosto

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

        # Aggiungi azione per il controllo manuale degli aggiornamenti
        check_update_action = QAction("Controlla Aggiornamenti", self)
        check_update_action.triggered.connect(self.manual_update_check)
        settings_menu.addAction(check_update_action)
        
        # Aggiungi azione per il controllo manuale degli aggiornamenti
        toggle_history_action = QAction("Mostra/Nascondi cronologia", self)
        toggle_history_action.triggered.connect(self.toggle_history_dock)
        settings_menu.addAction(toggle_history_action)

    def toggle_norma_info(self):
        """Mostra o nasconde la sezione delle informazioni sulla norma."""
        self.norma_info_section.setVisible(self.norma_info_toggle_button.isChecked())

    def toggle_brocardi_dock(self):
        """Mostra o nasconde il dock widget per le informazioni sui Brocardi."""
        if self.brocardi_toggle_button.isChecked():
            self.brocardi_dock.show()
        else:
            self.brocardi_dock.hide()
    
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

        
        # Pulisce le tab di Brocardi e l'output prima di iniziare una nuova ricerca
        self.brocardi_dock.clear_dynamic_tabs()  # Svuota tutte le tab di Brocardi
        self.output_dock.clear()  # Pulisce l'area di output


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

    def handle_data_fetch(self, normavisitate, cache_key):
        """Gestisce i dati ricevuti dal thread di fetch."""
        self.search_input_section.search_progress_bar.setVisible(False)

        # Verifica se è una ricerca multipla o singola
        if isinstance(normavisitate, list):
            # Gestione della ricerca multipla
            self.normavisitate = normavisitate  # Salva la lista dei risultati
            self.current_index = 0  # Ripristina l'indice all'inizio
            self.current_article = self.normavisitate[self.current_index].numero_articolo  # Inizializza l'articolo attuale

            # Aggiungi la ricerca multipla alla cronologia
            self.history_dock.add_search_to_history(self.normavisitate)

            # Pulisci il dock di Brocardi e l'area di output
            self.brocardi_dock.clear_dynamic_tabs()
            self.output_dock.clear()

            # Visualizza il primo articolo
            self.update_navigation_buttons()
            self.display_data(self.normavisitate[self.current_index])

        elif isinstance(normavisitate, NormaVisitata):
            # Gestione della ricerca singola
            self.normavisitate = [normavisitate]

            # Aggiungi la ricerca singola alla cronologia
            self.history_dock.add_search_to_history(normavisitate)

            # Pulisci il dock di Brocardi e l'area di output
            self.brocardi_dock.clear_dynamic_tabs()
            self.output_dock.clear()

            # Visualizza l'articolo
            self.current_index = 0
            self.update_navigation_buttons()
            self.display_data(self.normavisitate[self.current_index])

    def load_multiple_articles_from_history(self, normavisitate):
        """Carica una ricerca multipla dalla cronologia."""
        self.normavisitate = normavisitate
        self.current_index = 0
        self.update_navigation_buttons()
        self.display_data(self.normavisitate[self.current_index])

    def load_single_article_from_history(self, norma_visitata):
        """Carica una singola ricerca dalla cronologia."""
        self.normavisitate = [norma_visitata]
        self.current_index = 0
        self.update_navigation_buttons()
        self.display_data(self.normavisitate[self.current_index])


    def update_navigation_buttons(self):
        """Abilita o disabilita i pulsanti e gestisce la visibilità in base alla presenza di più articoli."""
        if len(self.normavisitate) > 1:
            # Mostra i pulsanti e abilita/disabilita in base alla posizione
            self.previous_button.setVisible(True)
            self.next_button.setVisible(True)
            self.previous_button.setEnabled(self.current_index > 0)
            self.next_button.setEnabled(self.current_index < len(self.normavisitate) - 1)
        else:
            # Nascondi i pulsanti se c'è solo un articolo
            self.previous_button.setVisible(False)
            self.next_button.setVisible(False)




    def show_previous_article(self):
        """Mostra l'articolo precedente nei risultati di ricerca multipla."""
        if self.current_index > 0:
            self.current_index -= 1
            self.display_data(self.normavisitate[self.current_index])
            self.update_navigation_buttons()

    def show_next_article(self):
        """Mostra l'articolo successivo nei risultati di ricerca multipla."""
        if self.current_index < len(self.normavisitate) - 1:
            self.current_index += 1
            self.display_data(self.normavisitate[self.current_index])
            self.update_navigation_buttons()


    def display_data(self, normavisitata):
        """Visualizza un singolo articolo e le informazioni correlate."""
        # Pulisce le tab dinamiche di Brocardi prima di visualizzare nuovi dati
        self.brocardi_dock.clear_dynamic_tabs()

        # Aggiorna la sezione di informazioni sulla norma
        self.norma_info_section.update_info(normavisitata)

        # Visualizza il testo dell'articolo
        cleaned_text = clean_text(normavisitata._article_text) if normavisitata._article_text else ''
        self.output_dock.display_text(cleaned_text)

        # Visualizza le informazioni Brocardi (se presenti)
        brocardi_info = normavisitata._brocardi_info if normavisitata._brocardi_info else None
        if brocardi_info:
            position = brocardi_info.get('position', "").strip()
            if position:
                link = brocardi_info.get('link', "#")
                self.brocardi_dock.add_brocardi_info(position, link, brocardi_info.get('info', {}))
            else:
                self.brocardi_dock.hide()
        else:
            self.brocardi_dock.hide()



    def clipboard(self):
        """Ritorna l'oggetto clipboard dell'applicazione."""
        return QApplication.clipboard()

    def show_message(self, title, message):
        """Mostra un messaggio popup con il titolo e il messaggio forniti."""
        QMessageBox.information(self, title, message)
        
    def setup_shortcuts(self):
        """Configura le scorciatoie da tastiera."""
        # Scorciatoia per il tasto 'Invio' che avvia la ricerca
        enter_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        enter_shortcut.activated.connect(self.on_search_button_clicked)

        # Scorciatoia per 'Ctrl+R' che riavvia l'applicazione
        restart_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        restart_shortcut.activated.connect(self.restart_application)
        
        # Scorciatoia per 'Ctrl+H' che mostra la cronoloigia
        history_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        history_shortcut.activated.connect(self.toggle_history_dock)
    
    def restart_application(self):
        """Riavvia l'applicazione quando si preme Ctrl+R."""
        QMessageBox.information(self, "Riavvio", "Riavvio dell'applicazione...")
        # Salva il percorso dell'eseguibile corrente
        python = sys.executable
        # Comando per riavviare l'applicazione
        subprocess.Popen([python] + sys.argv)
        # Chiudi l'applicazione corrente
        QApplication.quit()
