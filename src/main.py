# main.py
import sys
from PyQt6.QtWidgets import QApplication
from visualex_ui.components.main_window import NormaViewer

def main():
    app = QApplication(sys.argv)
    viewer = NormaViewer()
    viewer.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
