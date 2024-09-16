# src/main.py

import sys
from PyQt6.QtWidgets import QApplication
from visualex_ui.ui import NormaViewer  # Importa la classe principale della GUI dal modulo visualex_ui.ui
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

    # Crea un'istanza dell'applicazione Qt
    app = QApplication(sys.argv)

    # Crea un'istanza della finestra principale della tua applicazione
    viewer = NormaViewer()
    
    # Mostra la finestra principale
    viewer.show()

    # Esegui il ciclo principale dell'applicazione
    sys.exit(app.exec())

