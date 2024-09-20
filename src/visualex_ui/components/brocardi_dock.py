# visualex_ui/components/brocardi_dock.py
from PyQt6.QtWidgets import QDockWidget, QVBoxLayout, QWidget, QLabel, QTabWidget, QPushButton, QListWidget, QTextBrowser, QListWidgetItem
from PyQt6.QtCore import Qt, QSize
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

        # Etichetta per la posizione dei Brocardi
        self.position_label = QLabel()
        brocardi_layout.addWidget(self.position_label)

        # Etichetta per il link dei Brocardi
        self.brocardi_link_label = QLabel()
        self.brocardi_link_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.brocardi_link_label.setOpenExternalLinks(True)
        brocardi_layout.addWidget(self.brocardi_link_label)

        # Tabs per visualizzare diverse sezioni di Brocardi
        self.tabs = QTabWidget()
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
        Mostra il dock solo se la posizione è valida.
        """
        # Controlla se la posizione è valida e non vuota
        if not position or position == "Not Available" or position.strip() == "":
            logging.info("La posizione di Brocardi non è valida, nascondo il dock.")
            self.hide()  # Non mostrare il dock se 'position' è vuota o non valida
            return

        # Se la posizione è valida, aggiorna il contenuto
        logging.info(f"Aggiungo informazioni Brocardi con posizione: {position}")
        self.position_label.setText(position)
        self.brocardi_link_label.setText(f'<a href="{link}">{link}</a>')

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
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        list_widget.setStyleSheet("QListWidget::item { border: 1px solid #4E878C; margin: 4px; padding: 8px; }")  # Migliora lo stile degli item

        # Usa il metodo create_collapsible_list_item per aggiungere gli elementi
        for item_text in content:
            item_text = item_text.strip()
            self.create_collapsible_list_item(item_text, list_widget)

        tab_layout = QVBoxLayout()
        tab_layout.addWidget(list_widget)
        tab.setLayout(tab_layout)

        # Aggiungi la tab dinamica al widget tabs
        self.tabs.addTab(tab, section_name)
        self.dynamic_tabs[section_name] = tab

    def add_dynamic_text_tab(self, section_name, content):
        """
        Crea una tab dinamica con un QTextBrowser per sezioni come Spiegazione e Ratio.
        """
        tab = QWidget()
        text_edit = QTextBrowser()
        text_edit.setReadOnly(True)
        cleaned_content = content.strip()
        text_edit.setText(cleaned_content)

        tab_layout = QVBoxLayout()
        tab_layout.addWidget(text_edit)
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
        text_browser.setMinimumHeight(50)  # Altezza minima
        text_browser.setMaximumHeight(200)  # Altezza massima per evitare di occupare troppo spazio

        # Aggiungi QTextBrowser al layout
        layout.addWidget(text_browser)

        item_widget.setLayout(layout)
        item.setSizeHint(item_widget.sizeHint())  # Assicurati che l'elemento abbia la dimensione corretta
        parent_widget.setItemWidget(item, item_widget)  # Imposta il widget come item di QListWidget

    def clear_dynamic_tabs(self):
        """Rimuove tutte le tab dinamiche e pulisce la struttura dei dati."""
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
