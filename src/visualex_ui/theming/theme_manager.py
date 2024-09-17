# visualex_ui/theming/theme_manager.py

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QColorDialog, QSpinBox, QGroupBox, QFormLayout
)
from PyQt6.QtGui import QColor
from functools import partial 
from ..utils.helpers import get_resource_path
import logging

class ThemeManager:
    @staticmethod
    def apply_custom_theme(widget, custom_theme):
        """
        Applica il tema personalizzato al widget dato utilizzando i colori e la dimensione del font specificati.
        """
        if not custom_theme:
            logging.error("Tema personalizzato non fornito o non valido.")
            return

        stylesheet = ThemeManager.generate_custom_stylesheet(custom_theme)
        if stylesheet:
            widget.setStyleSheet(stylesheet)
        else:
            logging.error("Errore nella generazione del foglio di stile personalizzato.")

    @staticmethod
    def generate_custom_stylesheet(custom_theme):
        """
        Genera un foglio di stile personalizzato basato sui colori e sulla dimensione del font forniti dall'utente.

        Args:
            custom_theme (dict): Dizionario contenente 'font_size' e 'colors' personalizzati dall'utente.

        Returns:
            str: Foglio di stile QSS generato.
        """
        try:
            # Load base stylesheet from custom_style.qss
            stylesheet_template_path = get_resource_path('resources/custom_style.qss')
            with open(stylesheet_template_path, 'r', encoding='utf-8') as file:
                base_stylesheet = file.read()

            # Recupera le proprietà dal tema personalizzato
            font_size = custom_theme['font_size']
            colors = custom_theme['colors']

            # Mappatura dei colori selezionati dall'utente
            background_color = colors[0]  # Colore di sfondo principale
            text_color = colors[1]        # Colore del testo principale
            button_bg_color = colors[2]   # Colore di sfondo dei pulsanti
            button_text_color = colors[3] # Colore del testo dei pulsanti

            # Calcola i colori aggiuntivi utilizzando la funzione di regolazione del colore
            button_hover_color = ThemeManager.adjust_color(button_bg_color, 20)
            button_pressed_color = ThemeManager.adjust_color(button_bg_color, -20)
            button_disabled_color = ThemeManager.adjust_color(button_bg_color, -40)
            border_color = ThemeManager.adjust_color(text_color, -40)
            input_bg_color = ThemeManager.adjust_color(background_color, 10)
            selection_bg_color = ThemeManager.adjust_color(button_bg_color, 30)
            selection_text_color = button_text_color

            # Replace placeholders in the base stylesheet with the custom theme values
            final_stylesheet = base_stylesheet.format(
                font_size=font_size,
                background_color=background_color,
                text_color=text_color,
                button_background_color=button_bg_color,
                button_text_color=button_text_color,
                button_hover_color=button_hover_color,
                button_pressed_color=button_pressed_color,
                button_disabled_color=button_disabled_color,
                border_color=border_color,
                input_background_color=input_bg_color,
                selection_background_color=selection_bg_color,
                selection_text_color=selection_text_color
            )

            return final_stylesheet
        except Exception as e:
            logging.error(f"Errore nella generazione del foglio di stile: {e}")
            return ""

    @staticmethod
    def adjust_color(color_str, amount):
        """
        Regola la luminosità di un colore specifico per creare variazioni (es. hover, disabled).

        Args:
            color_str (str): Colore in formato hex (es. "#RRGGBB").
            amount (int): Valore per regolare la luminosità. Positivo per schiarire, negativo per scurire.

        Returns:
            str: Colore regolato in formato hex.
        """
        color = QColor(color_str)
        h, s, v, a = color.getHsv()
        v = max(0, min(255, v + amount))
        color.setHsv(h, s, v, a)
        return color.name()

    @staticmethod
    def get_themes():
        """Restituisce un dizionario con i temi predefiniti disponibili."""
        return {
            "Tema Chiaro": {
                'font_size': 14,
                'colors': ['#FFFFFF', '#000000', '#E0E0E0', '#000000']  # Colori del tema chiaro
            },
            "Tema Scuro": {
                'font_size': 14,
                'colors': ['#2E2E2E', '#FFFFFF', '#5E5E5E', '#FFFFFF']  # Colori del tema scuro
            },
            # Aggiungi altri temi predefiniti qui
        }

class ThemeDialog(QDialog):
    def __init__(self, parent=None, themes=None, current_theme=None, custom_theme=None):
        super().__init__(parent)
        self.setWindowTitle("Personalizza Tema")
        self.setMinimumSize(400, 300)

        self.parent = parent  # Keep reference to the parent to apply styles
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
        self.font_size_spinbox.valueChanged.connect(self.apply_changes)  # Apply changes in real-time
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
        if not is_custom:
            self.parent.change_theme(theme_name)  # Apply selected theme immediately

    def select_color(self, index):
        initial_color = self.selected_colors[index]
        color = QColorDialog.getColor(initial_color, self, f"Seleziona {self.color_labels[index]}")
        if color.isValid():
            self.selected_colors[index] = color
            self.color_buttons[index].setStyleSheet(f"background-color: {color.name()}")
            self.apply_changes()  # Apply changes in real-time

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

    def apply_changes(self):
        """
        Apply the custom theme in real-time as the user makes changes.
        """
        custom_theme = {
            'font_size': self.font_size_spinbox.value(),
            'colors': [color.name() for color in self.selected_colors]
        }
        self.parent.apply_custom_theme(custom_theme)
