# visualex_ui/utils/ui_utils.py

from PyQt6.QtWidgets import QTextEdit, QListWidget, QListWidgetItem, QApplication, QMessageBox

def copy_all_norma_info(norma_info_labels):
    """
    Copia tutte le informazioni della norma negli appunti.

    Args:
        norma_info_labels (dict): Dizionario contenente le QLabel con le informazioni della norma.
    """
    info = []

    # Copia le informazioni della norma popolate
    if norma_info_labels['urn_label'].text():
        info.append(f"URN: {norma_info_labels['urn_label'].text()}")
    if norma_info_labels['tipo_atto_label'].text():
        info.append(f"Tipo di Atto: {norma_info_labels['tipo_atto_label'].text()}")
    if norma_info_labels['data_label'].text():
        info.append(f"Data: {norma_info_labels['data_label'].text()}")
    if norma_info_labels['numero_atto_label'].text():
        info.append(f"Numero Atto: {norma_info_labels['numero_atto_label'].text()}")

    # Copia negli appunti
    clipboard = QApplication.clipboard()
    clipboard.setText("\n".join(info))

    # Mostra notifica
    QMessageBox.information(None, "Informazione Copiata", "Tutte le informazioni visualizzate sono state copiate negli appunti.")

def get_text_edit_content(tab_widget):
    """
    Ritorna il testo contenuto nel QTextEdit di una scheda tab.

    Args:
        tab_widget (QWidget): Il widget della scheda tab che contiene il QTextEdit.

    Returns:
        str: Il testo del QTextEdit.
    """
    if not tab_widget:
        return ""

    text_edit = tab_widget.findChild(QTextEdit)
    if not text_edit:
        return ""

    return text_edit.toPlainText()
