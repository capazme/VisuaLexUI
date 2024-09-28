# visualex_ui/utils/helpers.py

import os
import sys
from PyQt6.QtWidgets import QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt
import logging
import sys

def get_resource_path(relative_path):
    """
    Ottiene il percorso della risorsa per il runtime di PyInstaller.

    Args:
        relative_path (str): Il percorso relativo della risorsa.

    Returns:
        str: Il percorso assoluto della risorsa.
    """
    if hasattr(sys, '_MEIPASS'):
        # Quando l'app è eseguita come bundle PyInstaller
        base_path = sys._MEIPASS
    else:
        # Quando l'app è eseguita in ambiente di sviluppo
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, 'resources', relative_path)




def add_divider_to_list(list_widget):
    """
    Aggiunge un separatore visuale (divider) a un widget QListWidget per migliorare l'organizzazione e la leggibilità.

    Args:
        list_widget (QListWidget): Il widget di lista a cui aggiungere il separatore.
    """
    divider = QListWidgetItem()
    divider.setFlags(Qt.ItemFlag.NoItemFlags)  # Nessuna interazione per il divider
    divider.setSizeHint(divider.sizeHint().expandedTo(Qt.QSize(0, 10)))  # Altezza fissa per il separatore
    list_widget.addItem(divider)
