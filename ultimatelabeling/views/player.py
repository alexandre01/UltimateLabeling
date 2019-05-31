from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QGroupBox, QStyle
from PyQt5.QtCore import QThread
from ultimatelabeling.models import KeyboardListener, FrameMode
import time


class PlayerThread(QThread):
    FRAME_RATE = 30

    def __init__(self, state):
        super().__init__()

        self.state = state

    def run(self):
        while self.state.current_frame < self.state.nb_frames - 1 and self.state.frame_mode == FrameMode.CONTROLLED:
            self.state.increase_current_frame()
            time.sleep(1 / self.FRAME_RATE)

        # TODO: auto pause when finished

class PlayerWidget(QGroupBox, KeyboardListener):
    def __init__(self, state):
        super().__init__("Player")

        self.state = state

        self.thread = PlayerThread(self.state)

        layout = QHBoxLayout()

        self.skip_backward_button = QPushButton()
        self.skip_backward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.skip_backward_button.clicked.connect(self.on_skip_backward_clicked)

        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.on_play_clicked)

        self.pause_button = QPushButton()
        self.pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.pause_button.clicked.connect(self.on_pause_clicked)

        self.skip_forward_button = QPushButton()
        self.skip_forward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.skip_forward_button.clicked.connect(self.on_skip_forward_clicked)

        layout.addWidget(self.skip_backward_button)
        layout.addWidget(self.play_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.skip_forward_button)

        self.setLayout(layout)

        self.pause_button.hide()

    def on_play_clicked(self):
        if not self.thread.isRunning():
            self.state.frame_mode = FrameMode.CONTROLLED
            self.thread.start()

            self.play_button.hide()
            self.pause_button.show()

    def on_pause_clicked(self):
        if self.thread.isRunning():
            self.state.frame_mode = FrameMode.MANUAL
            self.thread.terminate()

            self.pause_button.hide()
            self.play_button.show()

    def on_key_play_pause(self):
        if self.thread.isRunning():
            self.on_pause_clicked()
        else:
            self.on_play_clicked()

    def on_skip_backward_clicked(self):
        self.state.set_current_frame(0)

    def on_skip_forward_clicked(self):
        self.state.set_current_frame(self.state.nb_frames - 1)
