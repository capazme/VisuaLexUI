# visualex_ui/components/output_area.py

from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QTextEdit, QPushButton, QLabel, QScrollArea, QMessageBox, QApplication, QListWidget, QListWidgetItem, QTextBrowser, QDockWidget, QWidget
from PyQt6.QtGui import QFont, QTextOption
from PyQt6.QtCore import Qt
import logging

class OutputArea(QDockWidget):
    def __init__(self, parent):
        super().__init__("Testo della Norma", parent)
        self.parent = parent
        logging.info("Inizializzazione di OutputArea")
        self.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                         QDockWidget.DockWidgetFeature.DockWidgetClosable |
                         QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.setup_ui()

    def setup_ui(self):
        logging.info("Setup dell'interfaccia utente per OutputArea")
        # Widget principale per il contenuto del dock
        self.output_widget = QWidget()
        layout = QVBoxLayout()

        # Visualizzazione del testo della norma
        self.norma_text_edit = QTextEdit()
        self.norma_text_edit.setReadOnly(True)
        self.norma_text_edit.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.norma_text_edit.setFont(QFont("Arial", 12))
        logging.debug("Impostata l'area di testo per la visualizzazione della norma")

        # Area di scorrimento per la visualizzazione del testo
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.norma_text_edit)
        layout.addWidget(scroll_area)

        # Pulsante per copiare tutte le informazioni
        self.copy_all_button = QPushButton("Copia Tutte le Informazioni")
        self.copy_all_button.clicked.connect(self.copy_all_norma_info)
        self.copy_all_button.setToolTip("Copia tutte le informazioni visualizzate negli appunti.")
        layout.addWidget(self.copy_all_button)
        logging.debug("Aggiunto il pulsante 'Copia Tutte le Informazioni'")

        # Imposta il layout nel widget principale e aggiungi al dock
        self.output_widget.setLayout(layout)
        self.setWidget(self.output_widget)

    def display_text(self, text):
        """
        Visualizza il testo fornito nell'area di output.
        """
        logging.info("Visualizzazione del testo nella OutputArea")
        if text:
            logging.debug(f"Testo visualizzato: {text[:100]}...")  # Mostra solo i primi 100 caratteri per non sovraccaricare i log
        self.norma_text_edit.setText(text)

    def copy_all_norma_info(self):
        """
        Copies all the information about the law (norma), including the selected brocardi and maxims,
        the rationale, the explanation, and the text of the article, into the clipboard.
        """
        logging.info("Avviato il processo di copia di tutte le informazioni della norma")
        info = []

        # Access NormaInfoSection to get label texts
        norma_info_section = self.parent.norma_info_section

        # General information about the law
        info.append("=== Informazioni Generali ===")
        if norma_info_section.urn_label.text():
            info.append(f"URN: {norma_info_section.urn_label.text()}")
        if norma_info_section.tipo_atto_label.text():
            info.append(f"Tipo di Atto: {norma_info_section.tipo_atto_label.text()}")
        if norma_info_section.data_label.text():
            info.append(f"Data: {norma_info_section.data_label.text()}")
        if norma_info_section.numero_atto_label.text():
            info.append(f"Numero Atto: {norma_info_section.numero_atto_label.text()}")

        # Add the law text
        norma_text = self.norma_text_edit.toPlainText()
        if norma_text:
            info.append("\n=== Testo della Norma ===\n" + norma_text)
            logging.debug("Testo della norma aggiunto alla copia")

        # Brocardi and Maxims Information
        brocardi_info = self.get_brocardi_info_as_text()
        if brocardi_info:
            info.append("\n=== Brocardi, Massime, Spiegazione, e Ratio ===\n" + brocardi_info)
            logging.debug("Informazioni su Brocardi, Massime, Spiegazione e Ratio aggiunte alla copia")

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(info))

        # Show notification
        logging.info("Informazioni copiate negli appunti")
        QMessageBox.information(self, "Informazione Copiata", "Tutte le informazioni selezionate sono state copiate negli appunti.")

    def get_brocardi_info_as_text(self):
        """
        Compiles information about brocardi, maxims, explanation, ratio, and position into a formatted text.
        """
        logging.info("Raccolta informazioni su Brocardi, Massime, Spiegazione, e Ratio")
        brocardi_text = []

        # Access BrocardiDockWidget to get dynamic_tabs
        brocardi_dock = self.parent.brocardi_dock
        dynamic_tabs = brocardi_dock.dynamic_tabs

        # Position
        if brocardi_dock.position_label.text():
            brocardi_text.append(f"Posizione: {brocardi_dock.position_label.text()}")

        # Loop through tabs and extract relevant information
        for section_name, tab_widget in dynamic_tabs.items():
            if section_name in ['Brocardi', 'Massime']:
                items = self.get_all_items(tab_widget)
                if items:
                    brocardi_text.append(f"\n--- {section_name} ---\n" + "\n".join(items))
            elif section_name in ['Spiegazione', 'Ratio']:
                text_content = self.get_text_edit_content(tab_widget)
                if text_content:
                    brocardi_text.append(f"\n--- {section_name} ---\n{text_content}")

        return "\n\n".join(brocardi_text)

    def get_all_items(self, tab_widget):
        """
        Returns a list of strings for all items in QListWidget.
        """
        if not tab_widget:
            logging.warning("Tab widget non trovato per la raccolta di tutti gli elementi")
            return []

        list_widget_obj = tab_widget.findChild(QListWidget)
        if not list_widget_obj:
            logging.warning("QListWidget non trovato all'interno della tab")
            return []

        items = []
        for i in range(list_widget_obj.count()):
            item = list_widget_obj.item(i)
            item_widget = list_widget_obj.itemWidget(item)
            if item_widget:
                text_browser = item_widget.findChild(QTextBrowser)
                if text_browser and text_browser.toPlainText().strip():
                    items.append(text_browser.toPlainText().strip())
        logging.debug(f"Elementi raccolti: {items}")
        return items

    def get_text_edit_content(self, tab_widget):
        """
        Returns the text content in QTextBrowser of a tab.
        """
        if not tab_widget:
            logging.warning("Tab widget non trovato per il recupero del contenuto del QTextBrowser")
            return ""

        text_browser = tab_widget.findChild(QTextBrowser)
        if not text_browser:
            logging.warning("QTextBrowser non trovato all'interno della tab")
            return ""

        content = text_browser.toPlainText()
        logging.debug(f"Contenuto QTextBrowser raccolto: {content[:100]}...")  # Mostra i primi 100 caratteri
        return content

    def clear(self):
        """
        Pulisce il contenuto del QTextEdit.
        """
        logging.info("Pulizia dell'area di testo della norma")
        self.norma_text_edit.clear()

    def append_text(self, text):
        """
        Aggiunge il testo fornito all'area di output senza sovrascrivere il contenuto esistente.
        """
        logging.info("Aggiunta di testo nella OutputArea")
        if text:
            logging.debug(f"Testo aggiunto: {text[:100]}...")  # Mostra solo i primi 100 caratteri per non sovraccaricare i log
        current_text = self.norma_text_edit.toPlainText()
        new_text = current_text + "\n\n" + text  # Aggiunge due righe vuote tra gli articoli
        self.norma_text_edit.setText(new_text)

