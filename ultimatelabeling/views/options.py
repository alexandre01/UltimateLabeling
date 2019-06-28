from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QCheckBox, QComboBox, QLabel
from PyQt5.QtCore import Qt
from ultimatelabeling.models import StateListener
from ultimatelabeling.styles import Theme
from ultimatelabeling.models.state import RightClickOption


class Options(QGroupBox, StateListener):
    def __init__(self, state):
        super().__init__("Options")

        self.state = state
        state.add_listener(self)

        self.copy_option_checkbox = QCheckBox("Copy annotations (⇦ ⇨)")
        self.copy_option_checkbox.setCheckState(Qt.Checked if self.state.copy_annotations_option else Qt.Unchecked)
        self.copy_option_checkbox.stateChanged.connect(lambda state: self.state.set_copy_annotations_option(state == Qt.Checked))

        right_click_label = QLabel("Right click:")
        self.right_click_dropdown = QComboBox()
        self.right_click_dropdown.addItems(["Delete current frame", "Delete all previous frames", "Delete all following frames"])
        self.right_click_dropdown.setCurrentIndex(self.state.right_click_option)
        self.right_click_dropdown.currentIndexChanged.connect(self.right_click_changed)

        layout = QHBoxLayout()
        layout.addWidget(self.copy_option_checkbox)
        layout.addStretch()
        layout.addWidget(right_click_label)
        layout.addWidget(self.right_click_dropdown)

        self.setLayout(layout)

    def right_click_changed(self, i):
        self.state.right_click_option = i
