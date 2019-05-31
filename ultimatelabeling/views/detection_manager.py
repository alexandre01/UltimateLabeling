from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QMessageBox, QCheckBox, QComboBox, QFormLayout, QLabel, QVBoxLayout
from PyQt5.QtCore import QThread
from ultimatelabeling.models import FrameMode
from ultimatelabeling.models.detector import SocketDetector
from ultimatelabeling.models.polygon import Bbox
import os


class DetectionManager(QGroupBox):
    def __init__(self, state):
        super().__init__("Detection")

        self.state = state
        self.detector = SocketDetector()
        options_layout = QFormLayout()

        self.crop_checkbox = QCheckBox("Use visible cropping area", self)
        options_layout.addRow(self.crop_checkbox)

        self.detector_dropdown = QComboBox()
        self.detector_dropdown.addItems(["YOLO", "OpenPifPaf"])
        options_layout.addRow(QLabel("Detection net:"), self.detector_dropdown)

        self.frame_detection_thread = DetectionThread(self.state, self.detector, self.crop_checkbox,
                                                      self.detector_dropdown, detect_video=False)
        self.frame_detection_thread.finished.connect(self.on_detection_finished)

        self.detection_thread = DetectionThread(self.state, self.detector, self.crop_checkbox, self.detector_dropdown,
                                                detect_video=True)
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

        self.detection_button.setEnabled(False)
        self.frame_detection_button.setEnabled(False)

        self.detection_thread.start()

    def on_detection_finished(self):
        self.detection_button.setEnabled(True)
        self.frame_detection_button.setEnabled(True)


class DetectionThread(QThread):

    def __init__(self, state, detector, crop_checkbox, detector_dropdown, detect_video=True):
        super().__init__()
        self.state = state
        self.detector = detector
        self.detect_video = detect_video
        self.detector_dropdown = detector_dropdown
        self.crop_checkbox = crop_checkbox

    def run(self):
        self.detector.init()

        crop_area = None
        if self.crop_checkbox.isChecked():
            crop_area = Bbox(*self.state.visible_area)

        detector = str(self.detector_dropdown.currentText())

        if self.detect_video:
            seq_path = os.path.join("data", self.state.current_video)

            self.state.frame_mode = FrameMode.CONTROLLED

            for frame, detections in enumerate(self.detector.detect_sequence(seq_path, self.state.nb_frames, crop_area=crop_area, detector=detector)):
                self.state.set_detections(detections, frame)

                if self.state.frame_mode == FrameMode.CONTROLLED or self.state.current_frame == frame:
                    self.state.set_current_frame(frame)

            self.detector.terminate()
            self.state.frame_mode = FrameMode.MANUAL

        else:
            image_path = self.state.file_names[self.state.current_frame]

            detections = self.detector.detect(image_path, crop_area=crop_area, detector=detector)
            self.state.set_detections(detections, self.state.current_frame)
            self.state.set_current_frame(self.state.current_frame)

            self.detector.terminate()
