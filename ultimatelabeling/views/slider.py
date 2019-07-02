import os
from PyQt5.QtWidgets import QSlider, QWidget, QHBoxLayout, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from ultimatelabeling.models import StateListener, KeyboardListener, FrameMode
from ultimatelabeling.config import RESOURCES_DIR


class VideoSlider(QWidget, StateListener, KeyboardListener):
    def __init__(self, state, keyboard_notifier):
        super().__init__()

        self.state = state
        self.state.add_listener(self)

        self.keyboard_notifier = keyboard_notifier

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(5)
        self.slider.setSingleStep(1)
        self.slider.setStyleSheet(open(os.path.join(RESOURCES_DIR, 'slider.style')).read())
        self.slider.valueChanged.connect(lambda: self.state.set_current_frame(self.slider.value(), frame_mode=FrameMode.SLIDER))

        self.label = QLabel()
        self.label.setFixedWidth(150)

        self.file_name_label = QLabel()
        self.file_name_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.on_video_change()

        layout = QVBoxLayout()

        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.label)
        slider_layout.addWidget(self.slider)

        layout.addLayout(slider_layout)
        layout.addWidget(self.file_name_label)

        self.setLayout(layout)

    def keyPressEvent(self, event):
        if type(event) != QKeyEvent:
            event.ignore()

        self.keyboard_notifier.keyPressEvent(event)  # delegate to keyboard_notifier

    def on_current_frame_change(self):
        self.slider.blockSignals(True)  # Don't trigger valueChanged
        self.slider.setValue(self.state.current_frame)
        self.slider.blockSignals(False)

        self.update_label()

    def update_label(self):
        self.label.setText("Frame {}/{}".format(self.state.current_frame + 1, self.state.nb_frames))
        self.file_name_label.setText(self.state.file_names[self.state.current_frame])

    def on_video_change(self):
        self.on_current_frame_change()
        self.slider.setMaximum(self.state.nb_frames - 1)

    def on_key_left(self):
        current_detection = None
        if self.state.current_detection is not None:
            current_detection = self.state.current_detection.copy()

        self.state.increase_current_frame(frame_mode=FrameMode.MANUAL, speed=-1)

        if current_detection and self.state.copy_annotations_option:
            track_ids = [d.track_id for d in self.state.track_info.detections]
            if current_detection.track_id not in track_ids:
                self.state.set_current_detection(current_detection)

    def on_key_right(self):
        current_detection = None
        if self.state.current_detection is not None:
            current_detection = self.state.current_detection.copy()

        self.state.increase_current_frame(frame_mode=FrameMode.MANUAL, speed=+1)

        if current_detection and self.state.copy_annotations_option:
            track_ids = [d.track_id for d in self.state.track_info.detections]
            if current_detection.track_id not in track_ids:
                self.state.set_current_detection(current_detection)
