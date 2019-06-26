from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QCheckBox
from PyQt5.QtCore import Qt
from ultimatelabeling.models import StateListener
from ultimatelabeling.styles import Theme


class Options(QGroupBox, StateListener):
    def __init__(self, state):
        super().__init__("Options")

        self.state = state
        state.add_listener(self)

        self.copy_backwards_option_checkbox = QCheckBox("Copy annotations (⇨)")
        self.copy_backwards_option_checkbox.setCheckState(Qt.Checked if self.state.copy_annotations_backwards_option else Qt.Unchecked)
        self.copy_backwards_option_checkbox.stateChanged.connect(lambda state: self.state.set_copy_annotations_backwards_option(state == Qt.Checked))

        self.copy_option_checkbox = QCheckBox("Copy annotations (⇨)")
        self.copy_option_checkbox.setCheckState(Qt.Checked if self.state.copy_annotations_option else Qt.Unchecked)
        self.copy_option_checkbox.stateChanged.connect(lambda state: self.state.set_copy_annotations_option(state == Qt.Checked))

        layout = QHBoxLayout()
        layout.addWidget(self.copy_backwards_option_checkbox)
        layout.addWidget(self.copy_option_checkbox)
        self.setLayout(layout)
