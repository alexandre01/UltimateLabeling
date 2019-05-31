from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QComboBox, QLabel
from PyQt5.QtCore import Qt
from ultimatelabeling.models import StateListener


class InfoDetection(QGroupBox, StateListener):
    def __init__(self, state):
        super().__init__("Info")

        self.state = state
        self.state.add_listener(self)

        self.show_kps_bbox_checkbox = QCheckBox("Show keypoint bboxes", self)
        self.show_kps_bbox_checkbox.setCheckState(Qt.Checked if self.state.keypoints_show_bbox else Qt.Unchecked)
        self.show_kps_bbox_checkbox.stateChanged.connect(lambda state: self.state.set_keypoints_show_bbox(state == Qt.Checked))

        self.kps_instance_color_checkbox = QCheckBox("Color keypoints by instance", self)
        self.kps_instance_color_checkbox.setCheckState(Qt.Checked if self.state.keypoints_instance_color else Qt.Unchecked)
        self.kps_instance_color_checkbox.stateChanged.connect(lambda state: self.state.set_keypoints_instance_color(state == Qt.Checked))

        self.bbox_class_color_checkbox = QCheckBox("Color bboxes by class", self)
        self.bbox_class_color_checkbox.setCheckState(Qt.Checked if self.state.bbox_class_color else Qt.Unchecked)
        self.bbox_class_color_checkbox.stateChanged.connect(lambda state: self.state.set_bbox_class_color(state == Qt.Checked))


        checkboxes_layout = QHBoxLayout()
        checkboxes_layout.addWidget(self.show_kps_bbox_checkbox)
        checkboxes_layout.addWidget(self.kps_instance_color_checkbox)
        checkboxes_layout.addWidget(self.bbox_class_color_checkbox)

        class_layout = QHBoxLayout()
        self.class_id_dropdown = QComboBox()
        self.class_id_dropdown.addItems(self._get_class_names())
        self.class_id_dropdown.currentIndexChanged.connect(self.class_id_changed)
        self.edit_classes_button = QPushButton("Edit")
        class_layout.addWidget(QLabel("Class:"))
        class_layout.addWidget(self.class_id_dropdown)
        class_layout.addWidget(self.edit_classes_button)

        self.nb_track_ids = 0
        instance_layout = QHBoxLayout()
        self.instance_id_dropdown = QComboBox()
        self.instance_id_dropdown.addItems(self._get_track_ids())
        self.instance_id_dropdown.currentIndexChanged.connect(self.instance_id_changed)
        instance_layout.addWidget(QLabel("Instance ID:"))
        instance_layout.addWidget(self.instance_id_dropdown)

        layout = QVBoxLayout()
        layout.addLayout(checkboxes_layout)
        layout.addLayout(class_layout)
        layout.addLayout(instance_layout)
        self.setLayout(layout)

    def _get_track_ids(self):
        self.nb_track_ids = self.state.track_info.nb_track_ids

        return [str(id) for id in range(self.nb_track_ids)]

    def _get_class_names(self):
        class_names = self.state.track_info.class_names

        return ["{} ({})".format(k, cl) for k, cl in class_names.items()]

    def class_id_changed(self, i):
        """if self.state.current_detection and i >= 0:
            self.state.current_detection.class_id = list(self.state.track_info.class_names)[i]
            self.state.notify_listeners("on_detection_change")"""
        return

    def instance_id_changed(self, i):
        """if self.state.current_detection and i >= 0:
            self.state.current_detection.track_id = i
            self.state.notify_listeners("on_detection_change")"""
        return

    def on_detection_change(self):
        """detection = self.state.current_detection

        self.instance_id_dropdown.blockSignals(True)
        self.instance_id_dropdown.clear()
        self.instance_id_dropdown.addItems(self._get_track_ids())
        self.instance_id_dropdown.blockSignals(False)

        if detection:
            instance_id = detection.track_id
            class_index = list(self.state.track_info.class_names).index(detection.class_id)

            self.instance_id_dropdown.blockSignals(True)
            self.instance_id_dropdown.setCurrentIndex(instance_id)
            self.instance_id_dropdown.blockSignals(False)

            self.class_id_dropdown.blockSignals(True)
            self.class_id_dropdown.setCurrentIndex(class_index)
            self.class_id_dropdown.blockSignals(False)"""
        return

    def on_video_change(self):
        """print("v", self.state.track_info.nb_track_ids)

        self.class_id_dropdown.clear()
        self.class_id_dropdown.addItems(self._get_class_names())

        self.instance_id_dropdown.clear()
        self.instance_id_dropdown.addItems(self._get_track_ids())"""
        return