from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QColorDialog, QSpinBox, QMessageBox, QGroupBox, QFormLayout
)
from PyQt6.QtGui import QColor
from functools import partial  # Importa partial per risolvere il problema con le funzioni lambda

class ThemeDialog(QDialog):
    def __init__(self, parent=None, themes=None, current_theme=None, custom_theme=None):
        super().__init__(parent)
        self.setWindowTitle("Personalizza Tema")
        self.setMinimumSize(400, 300)

        self.themes = themes or {}
        self.current_theme = current_theme
        self.custom_theme = custom_theme

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Theme selector
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Seleziona Tema:")
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(list(self.themes.keys()) + ["Personalizzato"])
        self.theme_selector.currentTextChanged.connect(self.on_theme_selected)

        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_selector)
        main_layout.addLayout(theme_layout)

        # Customization options
        self.custom_group = QGroupBox("Opzioni Personalizzate")
        self.custom_group.setEnabled(False)
        custom_layout = QFormLayout()

        # Color options
        self.color_labels = ["Colore Sfondo", "Colore Testo", "Colore Pulsanti", "Colore Testo Pulsanti"]
        self.color_buttons = []
        self.selected_colors = []

        for i, label in enumerate(self.color_labels):
            color_button = QPushButton()
            color_button.setFixedSize(40, 20)
            color_button.clicked.connect(partial(self.select_color, i))
            self.color_buttons.append(color_button)
            custom_layout.addRow(QLabel(f"{label}:"), color_button)

        # Font size option
        font_label = QLabel("Dimensione del Font:")
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 32)
        custom_layout.addRow(font_label, self.font_size_spinbox)

        self.custom_group.setLayout(custom_layout)
        main_layout.addWidget(self.custom_group)

        # Dialog buttons
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Applica")
        apply_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Annulla")
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Initialize controls based on current theme
        self.initialize_controls()

    def initialize_controls(self):
        # Set current theme in selector
        if self.current_theme in self.themes:
            index = list(self.themes.keys()).index(self.current_theme)
            self.theme_selector.setCurrentIndex(index)
        else:
            self.theme_selector.setCurrentIndex(self.theme_selector.count() - 1)

        # Initialize custom theme controls
        if self.current_theme == "Personalizzato" and self.custom_theme:
            colors = self.custom_theme.get('colors', ['#FFFFFF', '#000000', '#CCCCCC', '#000000'])
            font_size = self.custom_theme.get('font_size', 14)

            # Update `self.selected_colors` with the current colors
            self.selected_colors = [QColor(color) for color in colors]
            for i, color_button in enumerate(self.color_buttons):
                color_button.setStyleSheet(f"background-color: {self.selected_colors[i].name()}")
            
            # Set the font size correctly
            self.font_size_spinbox.setValue(font_size)
        else:
            # Default values
            self.selected_colors = [QColor(255, 255, 255), QColor(0, 0, 0),
                                    QColor(200, 200, 200), QColor(0, 0, 0)]
            for i, color_button in enumerate(self.color_buttons):
                color_button.setStyleSheet(f"background-color: {self.selected_colors[i].name()}")
            self.font_size_spinbox.setValue(14)

        # Enable/disable custom options based on theme
        self.on_theme_selected(self.theme_selector.currentText())

    def on_theme_selected(self, theme_name):
        is_custom = theme_name == "Personalizzato"
        self.custom_group.setEnabled(is_custom)

    def select_color(self, index):
        initial_color = self.selected_colors[index]
        color = QColorDialog.getColor(initial_color, self, f"Seleziona {self.color_labels[index]}")
        if color.isValid():
            self.selected_colors[index] = color
            self.color_buttons[index].setStyleSheet(f"background-color: {color.name()}")

    def get_selected_theme(self):
        selected_theme = self.theme_selector.currentText()
        if selected_theme == "Personalizzato":
            custom_theme = {
                'font_size': self.font_size_spinbox.value(),
                'colors': [color.name() for color in self.selected_colors]
            }
            return custom_theme
        else:
            return selected_theme

        
        