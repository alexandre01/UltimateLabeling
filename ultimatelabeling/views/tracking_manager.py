from PyQt5.QtWidgets import QPushButton, QGroupBox, QVBoxLayout, QHBoxLayout, QStyle, QPlainTextEdit, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from ultimatelabeling.models.tracker import SocketTracker
from ultimatelabeling.models import Detection, FrameMode
from ultimatelabeling.models import KeyboardListener

PORTS = [8787, 8788, 8789]


class TrackingThread(QThread):
    err_signal = pyqtSignal(str)

    def __init__(self, state, port):
        super().__init__()

        self.state = state
        self.runs = False
        self.tracker = SocketTracker(port)

        self.selected = False

    def run(self):
        self.runs = True

        init_frame = self.state.current_frame
        if init_frame == self.state.nb_frames:
            return

        class_id = self.state.current_detection.class_id
        track_id = self.state.current_detection.track_id
        init_bbox = self.state.current_detection.bbox

        self.state.frame_mode = FrameMode.CONTROLLED
        self.selected = True

        try:
            self.tracker.init(self.state.file_names[init_frame], init_bbox)
        except Exception as e:
            self.err_signal.emit(str(e))
            return

        frame = init_frame + 1

        while frame < self.state.nb_frames and self.runs:

            image_path = self.state.file_names[frame]
            try:
                bbox, polygon = self.tracker.track(image_path)
            except Exception as e:
                self.err_signal.emit(str(e))
                return

            detection = Detection(class_id=class_id, track_id=track_id, polygon=polygon, bbox=bbox)

            self.state.add_detection(detection, frame)

            if (self.state.frame_mode == FrameMode.CONTROLLED and self.selected) or self.state.current_frame == frame:
                self.state.set_current_frame(frame)

            frame += 1

        self.tracker.terminate()

    def stop(self):
        self.runs = False


class TrackingButtons(QGroupBox):
    def __init__(self, state, parent, i):
        super().__init__("Tracker {}".format(i+1))

        self.state = state
        self.parent = parent
        self.i = i

        self.thread = TrackingThread(self.state, port=PORTS[i])
        self.thread.err_signal.connect(self.display_err_message)
        self.thread.finished.connect(self.on_finished_tracking)

        layout = QVBoxLayout()

        self.start_button = QPushButton("Start")
        self.start_button.setIcon(self.style().standardIcon(QStyle.SP_DialogYesButton))
        self.start_button.clicked.connect(self.on_start_tracking)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_DialogNoButton))
        self.stop_button.clicked.connect(self.on_stop_tracking)

        self.sync_button = QPushButton("Sync")
        self.sync_button.clicked.connect(self.on_sync)

        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.sync_button)
        self.setLayout(layout)

        self.stop_button.hide()

    def display_err_message(self, err_message):
        QMessageBox.warning(self, "", "Error: {}".format(err_message))

    def on_start_tracking(self):
        if not self.state.tracking_server_running:
            QMessageBox.warning(self, "", "Tracking server is not connected.")
            return

        if not self.thread.isRunning():
            self.thread.start()
            self.parent.select(self.i)

            self.start_button.hide()
            self.stop_button.show()

    def on_stop_tracking(self):
        if self.thread.isRunning():
            self.thread.stop()

    def on_sync(self):
        self.state.frame_mode = FrameMode.CONTROLLED
        self.parent.select(self.i)

    def on_finished_tracking(self):
        if self.thread.isRunning():
            self.thread.terminate()

        self.state.frame_mode = FrameMode.MANUAL
        self.stop_button.hide()
        self.start_button.show()


class TrackingManager(QGroupBox, KeyboardListener):
    def __init__(self, state):
        super().__init__("Tracking")
        self.state = state

        self.trackers = [TrackingButtons(self.state, self, i) for i in range(3)]

        layout = QHBoxLayout()

        for tracker in self.trackers:
            layout.addWidget(tracker)

        self.setLayout(layout)

    def select(self, selected_i):
        for i, tracker in enumerate(self.trackers):
            tracker.thread.selected = i == selected_i

    def on_key_tracker(self):
        tracker = self.trackers[0]  # Always use the first tracker

        if not tracker.thread.isRunning():
            tracker.on_start_tracking()
        else:
            tracker.on_stop_tracking()
