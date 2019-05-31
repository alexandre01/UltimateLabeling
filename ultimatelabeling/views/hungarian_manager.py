from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton
from PyQt5.QtCore import QThread
from ultimatelabeling.models.hungarian_tracker import track


class HungarianManager(QGroupBox):
    def __init__(self, state):
        super().__init__("Hungarian")

        self.state = state

        self.hungarian_thread = HungarianThread(self.state)

        self.hungarian_button = QPushButton("Run Hung. algorithm")
        self.hungarian_button.clicked.connect(self.on_hungarian_clicked)

        layout = QHBoxLayout()
        layout.addWidget(self.hungarian_button)
        self.setLayout(layout)


    def on_hungarian_clicked(self):
        self.hungarian_button.setEnabled(False)
        self.hungarian_thread.finished.connect(self.on_hungarian_finished)
        self.hungarian_thread.start()

    def on_hungarian_finished(self):
        self.hungarian_button.setEnabled(True)
        self.state.notify_listeners("on_current_frame_change")


class HungarianThread(QThread):

    def __init__(self, state):
        super().__init__()
        self.state = state

    def run(self):
        track(self.state.track_info)

