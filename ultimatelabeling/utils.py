import cv2
from .models.polygon import Bbox
import numpy as np
import os
from tqdm import tqdm
import struct
import matplotlib.cm
import re

COCO_PERSON_SKELETON = [
    [16, 14], [14, 12], [17, 15], [15, 13], [12, 13], [6, 12], [7, 13],
    [6, 7], [6, 8], [7, 9], [8, 10], [9, 11], [2, 3], [1, 2], [1, 3],
    [2, 4], [3, 5], [4, 6], [5, 7]]


def get_color(id):
    np.random.seed(id)
    return tuple(map(int, np.random.choice(range(256), size=3)))


def draw_detection(img, detection, draw_anchors=True, color=None, kps_show_bbox=False, kps_instance_color=False, bbox_class_color=False):

    if detection.keypoints:
        draw_keypoints(img, detection.keypoints, object_id=detection.track_id if kps_instance_color else None)

        if not kps_show_bbox:
            return
        else:
            draw_anchors = False
            bbox_class_color = False

    if detection.bbox:
        thickness = Bbox.get_thickness()
        bbox = detection.bbox

        if color is None:
            if bbox_class_color:
                color = get_color(detection.class_id)
            else:
                color = get_color(detection.track_id)

        cv2.rectangle(img, tuple(bbox.pos.astype(int)), tuple((bbox.pos + bbox.size).astype(int)), color=color, thickness=thickness)

        if draw_anchors:
            draw_bbox_anchors(img, bbox, color=color)


def draw_bbox(img, bbox, color=(255, 0, 0), thickness=1, draw_anchors=True):
    cv2.rectangle(img, tuple(bbox.pos.astype(int)), tuple((bbox.pos + bbox.size).astype(int)), color=color, thickness=thickness)

    if draw_anchors:
        draw_bbox_anchors(img, bbox, color=color)


def draw_keypoints(img, keypoints, linewidth=3, solid_threshold=0.5, object_id=None):
    x, y, v = keypoints.coords[0::3], keypoints.coords[1::3], keypoints.coords[2::3]

    if object_id is not None:
        c = get_color(object_id)

    for ci, connection in enumerate(np.array(COCO_PERSON_SKELETON) - 1):
        if object_id is None:
            c = matplotlib.cm.get_cmap('tab20')(ci / len(COCO_PERSON_SKELETON))[:3]
            c = [int(x * 255) for x in c]

        x1, x2 = x[connection].astype(int)
        y1, y2 = y[connection].astype(int)

        if np.all(v[connection] > 0):
            # TODO: use dashed line
            cv2.line(img, (x1, y1), (x2, y2), c, linewidth)
        if np.all(v[connection] > solid_threshold):
            cv2.line(img, (x1, y1), (x2, y2), c, linewidth)

    draw_keypoint_anchors(img, keypoints)


def draw_keypoint_anchors(img, keypoints, radius=2, color=(255, 255, 255)):
    x, y, v = keypoints.coords[0::3], keypoints.coords[1::3], keypoints.coords[2::3]

    for xi, yi, in zip(x[v > 0], y[v > 0]):
        cv2.circle(img, (int(xi), int(yi)), radius, color, thickness=-1)


def draw_polygon(img, polygon, color=(255, 0, 0), thickness=1):
    coords = polygon.coords.astype(int).reshape((-1, 1, 2))
    cv2.polylines(img, [coords], True, color=color, thickness=thickness)


def draw_bbox_anchors(img, bbox, color=(255, 0, 0)):
    anchors = bbox.get_anchors()
    for anchor in anchors.values():
        x1, y1, x2, y2 = anchor
        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color=color, thickness=cv2.FILLED)


def subdivide_bbox(bbox):
    x, y, w, h = bbox.xywh
    w_, h_ = w / 2, h / 2
    return [Bbox(x, y, w_, h_), Bbox(x + w_, y, w_, h_), Bbox(x, y + h_, w_, h_), Bbox(x + w_, y + h_, w_, h_)]


def convert_video_to_frames(video_file, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    MAX_FRAMES = 1000

    vidcap = cv2.VideoCapture(video_file)
    nb_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))

    success, image = vidcap.read()
    if not success:
        return

    nb_frames = min(nb_frames, MAX_FRAMES)
    for i in tqdm(range(nb_frames)):
        cv2.imwrite(os.path.join(output_folder, "{:05d}.jpg".format(i)), image)
        success, image = vidcap.read()

        if not success:
            return


def send_data(socket, data):
    data = struct.pack('>I', len(data)) + data
    socket.sendall(data)


def recv_data(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, msglen)


def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(s)]