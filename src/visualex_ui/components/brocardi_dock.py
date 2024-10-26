# visualex_ui/components/brocardi_dock.py
from PyQt6.QtWidgets import QDockWidget, QVBoxLayout, QWidget, QLabel, QTabWidget, QListWidget, QTextBrowser, QListWidgetItem, QScrollArea, QSizePolicy
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QTextOption
import logging

class BrocardiDockWidget(QDockWidget):
    def __init__(self, parent):
        super().__init__("Informazioni Brocardi", parent)
        self.parent = parent
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.setup_ui()

    def setup_ui(self):
        # Widget principale per le informazioni sui Brocardi
        self.brocardi_info_widget = QWidget()
        brocardi_layout = QVBoxLayout()

        # Crea una QScrollArea per la position_label con scroll orizzontale disabilitato
        position_scroll_area = QScrollArea()
        position_scroll_area.setFixedHeight(40)
        position_scroll_area.setWidgetResizable(True)
        position_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Disabilita scrollbar orizzontale
        position_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Disabilita scrollbar verticale (se non necessario)

        # Etichetta per la posizione dei Brocardi
        self.position_label = QLabel()
        self.position_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction | Qt.TextInteractionFlag.TextSelectableByMouse)
        self.position_label.setWordWrap(True)  # Abilita il wrapping del testo
        self.position_label.setOpenExternalLinks(True)

        position_scroll_area.setWidget(self.position_label)

        brocardi_layout.addWidget(position_scroll_area)  # Aggiungi la scroll area al layout

        # Tabs per visualizzare diverse sezioni di Brocardi
        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred))  # Politica di espansione
        self.dynamic_tabs = {}  # Dizionario per le tabs dinamiche
        brocardi_layout.addWidget(self.tabs)

        # Impostazione del layout principale del widget
        self.brocardi_info_widget.setLayout(brocardi_layout)
        self.setWidget(self.brocardi_info_widget)
        
        # Nascondi il widget all'inizio
        self.hide()


    def add_brocardi_info(self, position, link, brocardi_info):
        """
        Aggiunge informazioni sui Brocardi al widget, inclusa la posizione e il link.
        """
        # Controlla se la posizione è valida e non vuota
        if not position or position == "Not Available" or position.strip() == "":
            logging.info("La posizione di Brocardi non è valida, nascondo il dock.")
            self.hide()  # Non mostrare il dock se 'position' è vuota o non valida
            return

        # Se la posizione è valida, aggiorna il contenuto
        logging.info(f"Aggiungo informazioni Brocardi con posizione: {position}")
        
        # Incorpora il link all'interno della posizione e rendi l'etichetta cliccabile
        html_text = f'<a href="{link}">{position}</a>'
        self.position_label.setText(html_text)

        # Pulisci le tabs dinamiche esistenti
        self.clear_dynamic_tabs()

        # Aggiungi sezioni dinamiche per le informazioni sui Brocardi (se presenti)
        for section_name, content in brocardi_info.items():
            if section_name in ['Brocardi', 'Massime'] and content:
                self.add_dynamic_list_tab(section_name, content)
            elif section_name in ['Spiegazione', 'Ratio'] and content:
                self.add_dynamic_text_tab(section_name, content)

        # Mostra il dock se ci sono informazioni valide
        self.show()

    def add_dynamic_list_tab(self, section_name, content):
        """
        Crea una tab dinamica con una lista di item per Brocardi o Massime.
        """
        tab = QWidget()

        # Crea il QListWidget con elementi wrappati
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        list_widget.setStyleSheet("QListWidget::item { border: 1px solid #4E878C; margin: 4px; padding: 8px; }")

        # Abilita il wrapping del testo negli elementi
        list_widget.setWordWrap(True)
        list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Disabilita scrollbar orizzontale
        list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)    # Abilita scrollbar verticale se necessario

        # Aggiungi gli item alla lista
        for item_text in content:
            item_text = item_text.strip()
            self.create_collapsible_list_item(item_text, list_widget)

        # Avvolgi il QListWidget in una QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Disabilita scrollbar orizzontale
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)     # Abilita scrollbar verticale se necessario
        scroll_area.setWidget(list_widget)

        tab_layout = QVBoxLayout()
        tab_layout.addWidget(scroll_area)
        tab.setLayout(tab_layout)

        # Aggiungi la tab dinamica al widget tabs
        self.tabs.addTab(tab, section_name)
        self.dynamic_tabs[section_name] = tab

    def add_dynamic_text_tab(self, section_name, content):
        """
        Crea una tab dinamica con un QTextBrowser per sezioni come Spiegazione e Ratio.
        """
        tab = QWidget()

        # Crea un QTextBrowser con wrapping abilitato
        text_edit = QTextBrowser()
        text_edit.setReadOnly(True)
        text_edit.setWordWrapMode(QTextOption.WrapMode.WordWrap)  # Abilita il wrapping del testo
        text_edit.setText(content.strip())
        text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Disabilita scrollbar orizzontale
        text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)     # Abilita scrollbar verticale se necessario
        text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Avvolgi il QTextBrowser in una QScrollArea per gestire contenuti lunghi
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Disabilita scrollbar orizzontale
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)     # Abilita scrollbar verticale se necessario
        scroll_area.setWidget(text_edit)
        
        tab_layout = QVBoxLayout()
        tab_layout.addWidget(scroll_area)
        tab.setLayout(tab_layout)

        # Aggiungi la tab dinamica al widget tabs
        self.tabs.addTab(tab, section_name)
        self.dynamic_tabs[section_name] = tab


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
        text_browser.setWordWrapMode(QTextOption.WrapMode.WordWrap)  # Abilita il wrapping del testo
        text_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Disabilita scrollbar orizzontale
        text_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)    # Se non vuoi scrolling verticale in questo widget
        text_browser.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # Aggiungi QTextBrowser al layout
        layout.addWidget(text_browser)

        item_widget.setLayout(layout)
        item.setSizeHint(item_widget.sizeHint())  # Assicurati che l'elemento abbia la dimensione corretta
        parent_widget.setItemWidget(item, item_widget)  # Imposta il widget come item di QListWidget

    def clear_dynamic_tabs(self):
        """Pulisce le tabs dinamiche esistenti."""
        self.tabs.clear()
        self.dynamic_tabs.clear()

    def hide_brocardi_dock(self):
        """Nasconde il dock widget dei Brocardi e pulisce i dati."""
        self.clear_dynamic_tabs()
        self.hide()

    def get_brocardi_info(self):
        """
        Ritorna le informazioni sui Brocardi e le Massime come testo formattato.
        """
        info_texts = []
        
        # Loop through dynamic tabs and extract their content
        for tab_name, tab_widget in self.dynamic_tabs.items():
            tab_content = self.extract_tab_content(tab_widget)
            if tab_content:
                info_texts.append(f"**{tab_name}:**\n{tab_content}")
        
        # Combine all information into a single formatted string
        return "\n\n".join(info_texts)

    def extract_tab_content(self, tab_widget):
        """
        Extract content from a specific tab widget.
        """
        # Example implementation to extract text from QListWidget or QTextBrowser inside the tab
        content_list = []
        if isinstance(tab_widget, QListWidget):
            for index in range(tab_widget.count()):
                item = tab_widget.item(index)
                content_list.append(item.text())
        elif isinstance(tab_widget, QTextBrowser):
            content_list.append(tab_widget.toPlainText())
        
        return "\n".join(content_list)
