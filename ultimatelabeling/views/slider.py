import os
from PyQt5.QtWidgets import QSlider, QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from ultimatelabeling.models import StateListener, KeyboardListener, FrameMode
from ultimatelabeling.config import ROOT_DIR


class VideoSlider(QWidget, StateListener, KeyboardListener):
    def __init__(self, state):
        super().__init__()

        self.state = state
        self.state.add_listener(self)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(5)
        self.slider.setSingleStep(1)
        self.slider.setStyleSheet(open(os.path.join(ROOT_DIR, 'styles', 'slider.style')).read())
        self.slider.valueChanged.connect(lambda: self.state.set_current_frame(self.slider.value(), frame_mode=FrameMode.MANUAL))

        self.label = QLabel()
        self.label.setFixedWidth(150)
        self.on_video_change()

        layout = QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        self.setLayout(layout)

    def on_current_frame_change(self):
        self.slider.blockSignals(True)  # Don't trigger valueChanged
        self.slider.setValue(self.state.current_frame)
        self.slider.blockSignals(False)

        self.update_label()

    def update_label(self):
        self.label.setText("Frame {}/{}".format(self.state.current_frame + 1, self.state.nb_frames))

    def on_video_change(self):
        self.on_current_frame_change()
        self.slider.setMaximum(self.state.nb_frames - 1)

    def on_key_left(self):
        self.state.decrease_current_frame(frame_mode=FrameMode.MANUAL)

    def on_key_right(self):
        self.state.increase_current_frame(frame_mode=FrameMode.MANUAL)