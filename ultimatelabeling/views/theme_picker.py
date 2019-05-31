from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton
from ultimatelabeling.models import StateListener
from ultimatelabeling.styles import Theme


class ThemePicker(QGroupBox, StateListener):
    def __init__(self, state):
        super().__init__("Theme")

        self.state = state
        state.add_listener(self)

        dark_theme_button = QPushButton("Dark")
        dark_theme_button.clicked.connect(self.on_dark_clicked)

        light_theme_button = QPushButton("Light")
        light_theme_button.clicked.connect(self.on_light_clicked)

        layout = QHBoxLayout()
        layout.addWidget(dark_theme_button)
        layout.addWidget(light_theme_button)
        self.setLayout(layout)

    def on_dark_clicked(self):
        self.state.set_theme(Theme.DARK)

    def on_light_clicked(self):
        self.state.set_theme(Theme.LIGHT)
