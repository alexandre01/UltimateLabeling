from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QGroupBox, QStyle, qApp
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from ultimatelabeling.models import KeyboardListener, FrameMode
import time


class PlayerThread(QThread):
    FRAME_RATE = 20

    def __init__(self, state):
        super().__init__()

        self.state = state

    def run(self):
        while self.state.frame_mode == FrameMode.CONTROLLED and (
                (self.state.speed_player >= 0 and self.state.current_frame < self.state.nb_frames - 1) or
                (self.state.speed_player < 0 and self.state.current_frame > 0)
        ):
            if not self.state.drawing:
                self.state.increase_current_frame()

            time.sleep(1 / self.FRAME_RATE)


class PlayerWidget(QGroupBox, KeyboardListener):
    def __init__(self, state):
        super().__init__("Player")

        self.state = state

        self.thread = PlayerThread(self.state)
        self.thread.finished.connect(self.on_player_finished)

        layout = QHBoxLayout()

        # self.skip_backward_button = QPushButton()
        # self.skip_backward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        # self.skip_backward_button.clicked.connect(self.on_skip_backward_clicked)

        self.speed_left_button = QPushButton()
        self.speed_left_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.speed_left_button.clicked.connect(self.on_speed_left_clicked)

        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.on_play_clicked)

        self.pause_button = QPushButton()
        self.pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.pause_button.clicked.connect(self.on_pause_clicked)

        # self.skip_forward_button = QPushButton()
        # self.skip_forward_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        # self.skip_forward_button.clicked.connect(self.on_skip_forward_clicked)

        self.speed_right_button = QPushButton()
        self.speed_right_button.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.speed_right_button.clicked.connect(self.on_speed_right_clicked)

        layout.addWidget(self.speed_left_button)
        layout.addWidget(self.play_button)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.speed_right_button)

        self.setLayout(layout)

        self.pause_button.hide()

    def on_player_finished(self):
        self.pause_button.hide()
        self.play_button.show()

        self.speed_left_button.setText("")
        self.speed_right_button.setText("")

    def on_play_clicked(self):
        self.speed_left_button.setText("")
        self.speed_right_button.setText("")

        if not self.thread.isRunning():

            self.state.frame_mode = FrameMode.CONTROLLED
            self.thread.start()

            self.play_button.hide()
            self.pause_button.show()

    def on_pause_clicked(self):
        self.speed_left_button.setText("")
        self.speed_right_button.setText("")

        if self.thread.isRunning():
            self.state.frame_mode = FrameMode.MANUAL
            self.state.speed_player = 1
            self.thread.wait()

            self.pause_button.hide()
            self.play_button.show()

    def on_key_play_pause(self):
        if self.thread.isRunning():
            self.on_pause_clicked()
        else:
            self.on_play_clicked()

    def on_speed_left_clicked(self):
        speed_options = [-2, -5, -10]

        if self.state.speed_player in speed_options:
            current_speed_idx = speed_options.index(self.state.speed_player)
            self.state.speed_player = speed_options[(current_speed_idx + 1) % len(speed_options)]
        else:
            self.state.speed_player = speed_options[0]

        self.on_play_clicked()

        self.speed_right_button.setText("")
        self.speed_left_button.setText("x{}".format(abs(self.state.speed_player)))

    def on_speed_right_clicked(self):
        speed_options = [+2, +5, +10]

        if self.state.speed_player in speed_options:
            current_speed_idx = speed_options.index(self.state.speed_player)
            self.state.speed_player = speed_options[(current_speed_idx + 1) % len(speed_options)]
        else:
            self.state.speed_player = speed_options[0]

        self.on_play_clicked()

        self.speed_left_button.setText("")
        self.speed_right_button.setText("x{}".format(self.state.speed_player))

    def on_skip_backward_clicked(self):
        self.state.set_current_frame(0)

    def on_skip_forward_clicked(self):
        self.state.set_current_frame(self.state.nb_frames - 1)
