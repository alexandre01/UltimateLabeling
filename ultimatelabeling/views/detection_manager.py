import os
import datetime
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QMessageBox, QCheckBox, QComboBox, QFormLayout, QLabel, QVBoxLayout
from PyQt5.QtCore import QThread
from ultimatelabeling.models import FrameMode, TrackInfo
from ultimatelabeling.models.detector import SocketDetector
from ultimatelabeling.models.polygon import Bbox
from ultimatelabeling.config import DATA_DIR


class DetectionManager(QGroupBox):
    def __init__(self, state, ssh_login):
        super().__init__("Detection")

        self.state = state
        self.ssh_login = ssh_login

        self.detector = SocketDetector()
        options_layout = QFormLayout()

        self.crop_checkbox = QCheckBox("Use visible image as cropping area", self)
        options_layout.addRow(self.crop_checkbox)

        self.detached_checkbox = QCheckBox("Detached mode (for videos)", self)
        options_layout.addRow(self.detached_checkbox)

        self.fetch_info_button = QPushButton("Fetch detached info")
        self.fetch_info_button.clicked.connect(self.fetch_detached_info)
        options_layout.addRow(self.fetch_info_button)

        self.load_detached_detections_button = QPushButton("Load detached detections")
        self.load_detached_detections_button.clicked.connect(self.load_detached_detections)
        options_layout.addRow(self.load_detached_detections_button)

        self.detector_dropdown = QComboBox()
        self.detector_dropdown.addItems(["YOLO", "OpenPifPaf"])
        options_layout.addRow(QLabel("Detection net:"), self.detector_dropdown)

        self.frame_detection_thread = DetectionThread(self.state, self.detector, self, detect_video=False)
        self.frame_detection_thread.finished.connect(self.on_detection_finished)

        self.detection_thread = DetectionThread(self.state, self.detector, self, detect_video=True)
        self.detection_thread.finished.connect(self.on_detection_finished)

        run_layout = QHBoxLayout()
        self.frame_detection_button = QPushButton("Run on frame")
        self.frame_detection_button.clicked.connect(self.on_frame_detection_clicked)

        self.detection_button = QPushButton("Run on video")
        self.detection_button.clicked.connect(self.on_detection_clicked)

        run_layout.addWidget(self.frame_detection_button)
        run_layout.addWidget(self.detection_button)

        layout = QVBoxLayout()
        layout.addLayout(options_layout)
        layout.addLayout(run_layout)
        self.setLayout(layout)

    def on_frame_detection_clicked(self):
        if not self.state.detection_server_running:
            QMessageBox.warning(self, "", "Detection server is not connected.")
            return

        self.detection_button.setEnabled(False)
        self.frame_detection_button.setEnabled(False)

        self.frame_detection_thread.start()

    def on_detection_clicked(self):
        if not self.state.detection_server_running:
            QMessageBox.warning(self, "", "Detection server is not connected.")
            return

        if self.detached_checkbox.isChecked():
            if self._is_detached_running():
                qm = QMessageBox
                res = qm.question(self, "", "Are you sure you want to start a new detached detection. This will kill the currently running one", qm.Yes | qm.No)

                if res == qm.No:
                    return

        self.detection_button.setEnabled(False)
        self.frame_detection_button.setEnabled(False)

        self.detection_thread.start()

    def on_detection_finished(self):
        self.detection_button.setEnabled(True)
        self.frame_detection_button.setEnabled(True)

    def fetch_detached_info(self):
        if not self.state.detection_server_running:
            QMessageBox.warning(self, "", "Detection server is not connected.")
            return

        info = self.ssh_login.fetch_detached_info()

        message = "Video: {}\nFrame: {}/{}\nStart time: {}\nLast update: {}".format(info["video_name"], info["current_frame"], info["total_frame"], info["start_time"], info["last_update"])
        QMessageBox.information(self, "", message)

    def _is_detached_running(self):
        info = self.ssh_login.fetch_detached_info()

        if not info:
            return False

        last_update = datetime.datetime.strptime(info["last_update"], "%Y-%m-%d %H:%M:%S.%f")
        now = datetime.datetime.now()

        return (now - last_update).total_seconds() < 60

    def load_detached_detections(self):
        if not self.state.detection_server_running:
            QMessageBox.warning(self, "", "Detection server is not connected.")
            return

        self.ssh_login.load_detached_detections(self.state.current_video)  # TODO: WARNING this will overwrite current annotations

        self.state.track_info = TrackInfo(self.state.current_video, self.state.file_names)
        self.state.detections = self.state.track_info.detections[self.state.current_frame]

        self.state.notify_listeners("on_detection_change")


class DetectionThread(QThread):

    def __init__(self, state, detector, parent, detect_video=True):
        super().__init__()
        self.state = state
        self.detector = detector
        self.detect_video = detect_video
        self.parent = parent

    def run(self):
        self.detector.init()

        crop_area = None
        if self.parent.crop_checkbox.isChecked():
            crop_area = Bbox(*self.state.visible_area)

        detached = self.parent.detached_checkbox.isChecked()

        detector = str(self.parent.detector_dropdown.currentText())

        if self.detect_video:
            seq_path = os.path.join(DATA_DIR, self.state.current_video)

            if not detached:

                self.state.frame_mode = FrameMode.CONTROLLED

                for frame, detections in enumerate(self.detector.detect_sequence(seq_path, self.state.nb_frames, crop_area=crop_area, detector=detector)):
                    self.state.set_detections(detections, frame)

                    if self.state.frame_mode == FrameMode.CONTROLLED or self.state.current_frame == frame:
                        self.state.set_current_frame(frame)

                self.detector.terminate()
                self.state.frame_mode = FrameMode.MANUAL

            else:

                self.parent.ssh_login.start_detached_detection(seq_path, crop_area=crop_area, detector=detector)

        else:
            image_path = self.state.file_names[self.state.current_frame]

            detections = self.detector.detect(image_path, crop_area=crop_area, detector=detector)
            self.state.set_detections(detections, self.state.current_frame)
            self.state.set_current_frame(self.state.current_frame)

            self.detector.terminate()
