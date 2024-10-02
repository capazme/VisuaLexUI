from PyQt6.QtWidgets import QDockWidget, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt
import logging

class HistoryDockWidget(QDockWidget):
    def __init__(self, parent):
        super().__init__("Cronologia Ricerche", parent)
        self.parent = parent
        self.history_list = QListWidget()  # Lista per visualizzare la cronologia delle ricerche
        self.setWidget(self.history_list)
        
        # Collegare il clic su una voce della cronologia a un'azione
        self.history_list.itemClicked.connect(self.on_history_item_clicked)

        # Manteniamo un set per evitare duplicati
        self.history_entries = set()

    def add_search_to_history(self, norma_visitata):
        """Aggiunge una ricerca alla cronologia."""
        # Convertiamo l'oggetto NormaVisitata in una stringa unica per evitare duplicati
        entry_str = self.generate_entry_string(norma_visitata)

        if entry_str not in self.history_entries:
            # Aggiunge l'elemento alla lista della cronologia se non è già presente
            self.history_entries.add(entry_str)
            item = QListWidgetItem(entry_str)
            item.setData(Qt.ItemDataRole.UserRole, norma_visitata)  # Memorizza l'oggetto NormaVisitata
            self.history_list.addItem(item)
            logging.info(f"Aggiunta ricerca alla cronologia: {entry_str}")
        else:
            logging.info(f"Ricerca già presente in cronologia: {entry_str}")

    def generate_entry_string(self, norma_visitata):
        """Genera una stringa univoca per rappresentare una ricerca, distinguendo le ricerche multiple."""
        if isinstance(norma_visitata, list):
            # Se la ricerca contiene più articoli, creiamo una rappresentazione concatenata
            articles = ", ".join(norma.numero_articolo for norma in norma_visitata)
            entry_str = f"{norma_visitata[0].norma} articoli: {articles}"
        else:
            # Per una singola norma
            entry_str = str(norma_visitata)
        return entry_str

    def on_history_item_clicked(self, item):
        """Carica una ricerca dalla cronologia quando viene cliccata."""
        norma_visitata = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(norma_visitata, list):
            self.parent.load_multiple_articles_from_history(norma_visitata)
        else:
            self.parent.load_single_article_from_history(norma_visitata)
