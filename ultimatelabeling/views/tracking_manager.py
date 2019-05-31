from PyQt5.QtWidgets import QPushButton, QGroupBox, QHBoxLayout, QStyle, QPlainTextEdit, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from ultimatelabeling.models.tracker import SocketTracker
from ultimatelabeling.models import Detection, FrameMode
import cv2


class TrackingThread(QThread):
    messageAdded = pyqtSignal(str)

    def __init__(self, state):
        super().__init__()

        self.state = state
        self.runs = False
        self.tracker = SocketTracker()  # SiamMaskTracker()

    def get_image(self, frame):
        image_file = self.state.file_names[frame]
        return cv2.imread(image_file)

    def run(self):
        self.runs = True

        init_frame = self.state.current_frame
        if init_frame == self.state.nb_frames:
            return

        class_id = self.state.current_detection.class_id
        track_id = self.state.current_detection.track_id
        init_bbox = self.state.current_detection.bbox

        self.state.frame_mode = FrameMode.CONTROLLED
        self.messageAdded.emit("Intializing tracker...")
        self.tracker.init(self.get_image(init_frame), init_bbox)
        self.messageAdded.emit("Tracker intialized!")

        frame = init_frame + 1

        while frame < self.state.nb_frames and self.runs:

            image_file = self.state.file_names[frame]
            img = cv2.imread(image_file)
            bbox, polygon = self.tracker.track(img)
            detection = Detection(class_id=class_id, track_id=track_id, polygon=polygon, bbox=bbox)

            self.state.add_detection(detection, frame)

            if self.state.frame_mode == FrameMode.CONTROLLED or self.state.current_frame == frame:
                self.state.set_current_frame(frame)

            frame += 1

        self.tracker.terminate()
        self.messageAdded.emit("Tracker terminated.")

    def stop(self):
        self.runs = False


class TrackingManager(QGroupBox):
    def __init__(self, state):
        super().__init__("Tracking")
        self.state = state

        self.thread = TrackingThread(self.state)
        self.thread.messageAdded.connect(self.add_message)
        self.thread.finished.connect(self.on_finished_tracking)

        layout = QHBoxLayout()

        self.start_button = QPushButton("Start")
        self.start_button.setIcon(self.style().standardIcon(QStyle.SP_DialogYesButton))
        self.start_button.clicked.connect(self.on_start_tracking)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_DialogNoButton))
        self.stop_button.clicked.connect(self.on_stop_tracking)

        self.textArea = QPlainTextEdit()
        self.textArea.resize(400, 200)

        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addStretch()
        layout.addWidget(self.textArea)

        self.setLayout(layout)

        self.stop_button.hide()

    def on_start_tracking(self):
        if not self.state.tracking_server_running:
            QMessageBox.warning(self, "", "Tracking server is not connected.")
            return

        if not self.thread.isRunning():
            self.thread.start()

            self.start_button.hide()
            self.stop_button.show()

    def on_stop_tracking(self):
        if self.thread.isRunning():
            self.thread.stop()

    def add_message(self, message):
        self.textArea.insertPlainText(message + "\n")

    def on_finished_tracking(self):
        if self.thread.isRunning():
            self.thread.terminate()

        self.state.frame_mode = FrameMode.MANUAL
        self.stop_button.hide()
        self.start_button.show()
