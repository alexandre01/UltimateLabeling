import cv2
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QImage, QPainter
from ultimatelabeling.models import StateListener
from ultimatelabeling.utils import draw_detection
from ultimatelabeling.models import KeyboardListener
from ultimatelabeling.models.polygon import Bbox
from ultimatelabeling.models.track_info import Detection
import numpy as np
from ultimatelabeling import utils


class Event:
    DRAWING = "drawing"
    RESIZING = "resizing"
    DRAGGING = "dragging"
    MOVING = "moving"
    KEYPOINT_DRAGGING = "keypoint_dragging"


class Anchor:
    def __init__(self, anchor_key, anchor, detection_index):
        self.anchor_key = anchor_key
        self.anchor = anchor
        self.detection_index = detection_index

    def __repr__(self):
        return "Anchor({})".format(self.anchor)


class AnchorQuadTree:
    MAX_PER_NODE = 5
    MAX_DEPTH = 8

    def __init__(self, bbox, depth=0):
        self.bbox = bbox
        self.anchors = []
        self.children = None
        self.depth = depth

    def build_quadtree(self, detections):
        for i, detection in enumerate(detections):
            if not detection.keypoints and detection.bbox:
                anchors = detection.bbox.get_anchors()
                for anchor_key, anchor in anchors.items():
                    self.add_anchor(Anchor(anchor_key, anchor, i))

    def is_leaf(self):
        return self.children is None

    def add_anchor(self, anchor):
        if self.is_leaf():
            self.anchors.append(anchor)

            if len(self.anchors) > self.MAX_PER_NODE and self.depth < self.MAX_DEPTH:
                child_bboxes = utils.subdivide_bbox(self.bbox)
                self.children = [AnchorQuadTree(bbox, self.depth + 1) for bbox in child_bboxes]

                for i, bbox in enumerate(child_bboxes):
                    for anchor in self.anchors:
                        if bbox.intersects(anchor.anchor):
                            self.children[i].add_anchor(anchor)
                self.anchors = []

        else:
            for child in self.children:
                if child.bbox.intersects(anchor.anchor):
                    child.add_anchor(anchor)

    def find_anchor(self, p):
        if self.is_leaf():
            for anchor in self.anchors:
                xmin, ymin, xmax, ymax = anchor.anchor
                if xmin <= p[0] <= xmax and ymin <= p[1] <= ymax:
                    return anchor
        else:
            for child in self.children:
                if child.bbox.is_inside(p):
                    found = child.find_anchor(p)
                    if found:
                        return found

        return None


class KeypointQuadTree:
    MAX_PER_NODE = 5
    MAX_DEPTH = 8

    def __init__(self, bbox, depth=0):
        self.bbox = bbox
        self.anchors = []
        self.children = None
        self.depth = depth

    def build_quadtree(self, detections):
        for i, detection in enumerate(detections):
            anchors = detection.keypoints.get_anchors()
            for anchor_key, anchor in anchors.items():
                self.add_anchor(Anchor(anchor_key, anchor, i))

    def is_leaf(self):
        return self.children is None

    def add_anchor(self, anchor):
        if self.is_leaf():
            self.anchors.append(anchor)

            if len(self.anchors) > self.MAX_PER_NODE and self.depth < self.MAX_DEPTH:
                child_bboxes = utils.subdivide_bbox(self.bbox)
                self.children = [KeypointQuadTree(bbox, self.depth + 1) for bbox in child_bboxes]

                for i, bbox in enumerate(child_bboxes):
                    for anchor in self.anchors:
                        if bbox.intersects(anchor.anchor):
                            self.children[i].add_anchor(anchor)
                self.anchors = []

        else:
            for child in self.children:
                if child.bbox.intersects(anchor.anchor):
                    child.add_anchor(anchor)

    def find_anchor(self, p):
        if self.is_leaf():
            for anchor in self.anchors:
                xmin, ymin, xmax, ymax = anchor.anchor
                if xmin <= p[0] <= xmax and ymin <= p[1] <= ymax:
                    return anchor
        else:
            for child in self.children:
                if child.bbox.is_inside(p):
                    found = child.find_anchor(p)
                    if found:
                        return found

        return None


class DetectionQuadTree:
    MAX_PER_NODE = 5
    MAX_DEPTH = 8

    def __init__(self, bbox, depth=0):
        self.bbox = bbox
        self.detections = []
        self.children = None
        self.depth = depth

    def build_quadtree(self, detections):
        for i, detection in enumerate(detections):
            if not detection.keypoints and detection.bbox:
                self.add_detection(detection)

    def is_leaf(self):
        return self.children is None

    def add_detection(self, detection):
        if self.is_leaf():
            self.detections.append(detection)

            if len(self.detections) > self.MAX_PER_NODE and self.depth < self.MAX_DEPTH:
                child_bboxes = utils.subdivide_bbox(self.bbox)
                self.children = [DetectionQuadTree(bbox, self.depth + 1) for bbox in child_bboxes]

                for i, bbox in enumerate(child_bboxes):
                    for detection in self.detections:
                        if bbox.intersects(detection.bbox.x1y1x2y2):
                            self.children[i].add_detection(detection)
                self.detection = []

        else:
            for child in self.children:
                if child.bbox.intersects(detection.bbox.x1y1x2y2):
                    child.add_detection(detection)

    def find_detection(self, p):
        if self.is_leaf():
            for detection in self.detections:
                if detection.bbox.is_inside(p):
                    return detection
        else:
            for child in self.children:
                if child.bbox.is_inside(p):
                    found = child.find_detection(p)
                    if found:
                        return found

        return None


class ImageWidget(QWidget, StateListener, KeyboardListener):
    def __init__(self, state):
        super().__init__()

        self.state = state
        self.state.add_listener(self)

        self.MIN_ZOOM, self.MAX_ZOOM = 0.9, 6.0
        self.zoom = 1.0
        self.offset = QPoint(0., 0.)
        self.original_img = None
        self.img = None

        self.anchors_quadtree = None
        self.detections_quadtree = None
        self.keypoints_quadtree = None

        self.current_event = None
        self.current_detection = None
        self.current_anchor_key = None
        self.cursor_offset = None
        self.holding_ctrl = False

        self.setFixedSize(900, 900)
        self.setMouseTracking(True)

        self.on_current_frame_change()

    def get_visible_area(self):
        h, w, _ = self.img.shape
        zoom = self.zoom * self.img_scale

        offset_x = min(max(-self.offset.x() / zoom, 0), w)
        offset_y = min(max(-self.offset.y() / zoom, 0), h)

        screen_offset_x = max(self.offset.x() / zoom, 0)
        screen_offset_y = max(self.offset.y() / zoom, 0)

        width = min(self.width() / zoom - screen_offset_x, w - offset_x)
        height = min(self.height() / zoom - screen_offset_y, h - offset_y)

        return offset_x, offset_y, width, height

    def on_current_frame_change(self):
        image_file = self.state.file_names[self.state.current_frame]
        img = cv2.imread(image_file)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        h, w, _ = img.shape
        self.img_scale = float(self.width()) / float(w)

        self.anchors_quadtree = AnchorQuadTree(Bbox(0, 0, w, h))
        self.anchors_quadtree.build_quadtree(self.state.detections)

        self.detections_quadtree = DetectionQuadTree(Bbox(0, 0, w, h))
        self.detections_quadtree.build_quadtree(self.state.detections)

        self.keypoints_quadtree = KeypointQuadTree(Bbox(0, 0, w, h))
        self.keypoints_quadtree.build_quadtree(self.state.detections)

        self.draw_bboxes(img)
        self.draw_image(img)

    def on_detection_change(self):
        self.on_current_frame_change()

    def draw_bboxes(self, img):
        for detection in self.state.detections:
            draw_detection(img, detection, kps_show_bbox=self.state.keypoints_show_bbox,
                           kps_instance_color=self.state.keypoints_instance_color, bbox_class_color=self.state.bbox_class_color)

    def draw_current_detection(self):
        if self.current_detection:
            self.img = self.original_img.copy()
            draw_detection(self.img, self.current_detection, draw_anchors=False,
                           kps_show_bbox=self.state.keypoints_show_bbox, kps_instance_color=self.state.keypoints_instance_color,
                           bbox_class_color=self.state.bbox_class_color)

    def on_video_change(self):
        self.on_current_frame_change()

    def draw_image(self, img):
        self.original_img = img
        self.img = img

        self.update_zoom_offset()

    def update_zoom_offset(self):
        M = np.float32([[self.zoom * self.img_scale, 0, self.offset.x()],
                        [0, self.zoom * self.img_scale, self.offset.y()]])
        self.canvas = cv2.warpAffine(self.img, M, (900, 900), borderValue=(38, 38, 38))

        self.state.visible_area = self.get_visible_area()

        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.canvas is not None:
            height, width, bpc = self.canvas.shape
            bpl = bpc * width
            img = QImage(self.canvas.data, width, height, bpl, QImage.Format_RGB888)
            qp.drawImage(QPoint(0, 0), img)
        qp.end()

    def get_abs_pos(self, pos):
        return (pos - self.offset) / (self.zoom * self.img_scale)

    def on_key_ctrl(self, holding):
        self.holding_ctrl = holding

    def wheelEvent(self, event):
        pos = event.pos()
        old_p = (pos - self.offset) / self.zoom

        numPixels = event.pixelDelta().y()
        self.zoom = max(min(self.zoom + numPixels / 40, self.MAX_ZOOM), self.MIN_ZOOM)

        new_p = old_p * self.zoom + self.offset
        self.offset += pos - new_p

        self.update_zoom_offset()

    def mousePressEvent(self, event):
        pos = self.get_abs_pos(event.pos())

        if event.buttons() == Qt.LeftButton:

            anchor = self.anchors_quadtree.find_anchor([pos.x(), pos.y()])
            detection = self.detections_quadtree.find_detection([pos.x(), pos.y()])
            keypoint = self.keypoints_quadtree.find_anchor([pos.x(), pos.y()])

            if anchor:
                self.current_event = Event.RESIZING
                self.current_anchor_key = anchor.anchor_key
                self.current_detection = self.state.detections[anchor.detection_index].copy()
                self.state.remove_detection(detection_index=anchor.detection_index)

                if anchor.anchor_key[0] == "M":
                    QApplication.setOverrideCursor(Qt.SizeVerCursor)
                elif anchor.anchor_key[1] == "M":
                    QApplication.setOverrideCursor(Qt.SizeHorCursor)
                elif anchor.anchor_key == "LT" or anchor.anchor_key == "RB":
                    QApplication.setOverrideCursor(Qt.SizeFDiagCursor)
                else:
                    QApplication.setOverrideCursor(Qt.SizeBDiagCursor)

            elif detection:
                self.current_event = Event.DRAGGING
                QApplication.setOverrideCursor(Qt.ClosedHandCursor)
                self.current_detection = detection
                self.state.remove_detection(detection=detection)
                self.cursor_offset = np.array([pos.x(), pos.y()], dtype=float) - self.current_detection.bbox.pos

            elif keypoint:
                self.current_event = Event.KEYPOINT_DRAGGING
                QApplication.setOverrideCursor(Qt.ClosedHandCursor)
                self.current_anchor_key = keypoint.anchor_key
                self.current_detection = self.state.detections[keypoint.detection_index].copy()
                self.state.remove_detection(detection_index=keypoint.detection_index)

                i = self.current_anchor_key
                keypoint_pos = self.current_detection.keypoints.coords[3*i:3*i+2]
                self.cursor_offset = np.array([pos.x(), pos.y()], dtype=float) - keypoint_pos

            else:
                if self.holding_ctrl:
                    self.current_event = Event.DRAWING
                    track_id = self.state.track_info.get_min_available_track_id(self.state.current_frame)
                    self.current_detection = Detection(track_id=track_id, bbox=Bbox(pos.x(), pos.y(), 0, 0))

                    self.on_current_frame_change()
                else:
                    self.current_event = Event.MOVING
                    self.cursor_offset = event.pos() - self.offset

        elif event.buttons() == Qt.RightButton:
            anchor = self.anchors_quadtree.find_anchor([pos.x(), pos.y()])
            detection = self.detections_quadtree.find_detection([pos.x(), pos.y()])

            if anchor:
                self.state.remove_detection_and_future(detection_index=anchor.detection_index)
            elif detection:
                self.state.remove_detection_and_future(detection=detection)

        self.draw_current_detection()
        self.update_zoom_offset()

    def mouseMoveEvent(self, event):

        if event.buttons() == Qt.NoButton:
            pos = self.get_abs_pos(event.pos())

            anchor = self.anchors_quadtree.find_anchor([pos.x(), pos.y()])
            detection = self.detections_quadtree.find_detection([pos.x(), pos.y()])
            keypoint = self.keypoints_quadtree.find_anchor([pos.x(), pos.y()])

            if anchor:
                if anchor.anchor_key[0] == "M":
                    QApplication.setOverrideCursor(Qt.SizeVerCursor)
                elif anchor.anchor_key[1] == "M":
                    QApplication.setOverrideCursor(Qt.SizeHorCursor)
                elif anchor.anchor_key == "LT" or anchor.anchor_key == "RB":
                    QApplication.setOverrideCursor(Qt.SizeFDiagCursor)
                else:
                    QApplication.setOverrideCursor(Qt.SizeBDiagCursor)

            elif detection or keypoint:
                QApplication.setOverrideCursor(Qt.OpenHandCursor)

            else:
                QApplication.restoreOverrideCursor()

        elif event.buttons() == Qt.LeftButton:
            pos = self.get_abs_pos(event.pos())
            pos = np.array([pos.x(), pos.y()], dtype=float)

            if self.current_event == Event.MOVING:
                diff = event.pos() - self.cursor_offset
                self.offset = diff
                self.update_zoom_offset()

            elif self.current_event == Event.DRAGGING:
                diff = pos - self.cursor_offset
                self.current_detection.bbox.pos = diff

            elif self.current_event == Event.KEYPOINT_DRAGGING:
                diff = pos - self.cursor_offset
                i = self.current_anchor_key
                self.current_detection.keypoints.coords[3*i:3*i+2] = diff

            elif self.current_event == Event.RESIZING:
                if self.current_anchor_key[0] == "L":
                    self.current_detection.bbox.set_x1(pos[0])
                elif self.current_anchor_key[0] == "R":
                    self.current_detection.bbox.set_x2(pos[0])
                if self.current_anchor_key[1] == "T":
                    self.current_detection.bbox.set_y1(pos[1])
                elif self.current_anchor_key[1] == "B":
                    self.current_detection.bbox.set_y2(pos[1])

            elif self.current_event == Event.DRAWING:
                diff = pos - self.current_detection.bbox.pos
                self.current_detection.bbox.size = diff

            self.draw_current_detection()
            self.update_zoom_offset()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:

            if self.current_event != Event.MOVING:
                self.current_detection.bbox.correct_negative_size()
                self.state.set_current_detection(self.current_detection)

                """self.img = self.original_img.copy()
                area = self.get_visible_area()
                utils.draw_bbox(self.img, bbox=Bbox(*area), color=(255, 0, 0))
                self.update_zoom_offset()
                self.update()"""

            QApplication.restoreOverrideCursor()
            self.current_event = None
            self.current_detection = None
            self.current_anchor_key = None
            self.cursor_offset = None
