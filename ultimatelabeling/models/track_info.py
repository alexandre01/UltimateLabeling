import json
import os
from .polygon import Polygon, Bbox, Keypoints
from ultimatelabeling.class_names import DEFAULT_CLASS_NAMES
from ultimatelabeling.config import OUTPUT_DIR


class Detection:
    def __init__(self, class_id=0, track_id=0, polygon=Polygon(), bbox=Bbox(), keypoints=Keypoints()):
        self.class_id = class_id
        self.track_id = track_id
        self.polygon = polygon
        self.bbox = bbox
        self.keypoints = keypoints

    @staticmethod
    def from_json(data):
        return Detection(data["class_id"], data["track_id"],
                         Polygon(data["polygon"]), Bbox(*data["bbox"]), Keypoints(data["keypoints"]))

    def to_json(self):
        return {
            "track_id": self.track_id,
            "class_id": self.class_id,
            "polygon": self.polygon.to_json(),
            "bbox": self.bbox.to_json(),
            "keypoints": self.keypoints.to_json()
        }

    def copy(self):
        return Detection(self.class_id, self.track_id, self.polygon.copy(), self.bbox.copy(), self.keypoints.copy())

    def __repr__(self):
        return "Detection(class_id={}, track_id={}, bbox={}, polygon={}, keypoints={})".format(self.class_id, self.track_id,
                                                                                 self.bbox, self.polygon, self.keypoints)


class TrackInfo:
    def __init__(self, video_name="", file_names=[]):
        self.video_name = video_name
        self.file_names = file_names
        self.nb_frames = len(file_names)

        self.nb_track_ids = 0

        self.class_names = DEFAULT_CLASS_NAMES
        self.detections = [[] for _ in range(self.nb_frames)]

        self.load_from_disk()

    def load_from_disk(self):
        file_name = os.path.join(OUTPUT_DIR, "{}.json".format(self.video_name))

        if not os.path.exists(file_name):
            return

        with open(file_name, "r") as f:
            data = json.load(f)
            self.nb_track_ids = data["nb_track_ids"]
            self._load_class_names(data)
            self.detections = [[Detection.from_json(detection) for detection in frame["detections"]] for frame in data["frames"]]

    def _load_class_names(self, data):
        if "class_names" not in data:
            self.class_names = DEFAULT_CLASS_NAMES

        self.class_names = {int(k): v for k, v in json.loads(data["class_names"]).items()}

    def to_json(self):
        return {
            "video_name": self.video_name,
            "nb_track_ids": self.nb_track_ids,
            "class_names": json.dumps(self.class_names),
            "frames": [
                {
                    "frame_id": i,
                    "file_name": self.file_names[i],
                    "detections": [d.to_json() for d in detections]
                }
                for i, detections in enumerate(self.detections)
            ]
        }

    def get_min_available_track_id(self, frame):
        track_ids = set([d.track_id for d in self.detections[frame]])
        N = len(track_ids)
        missing_track_ids = set(range(N)) - track_ids
        if missing_track_ids:
            return min(missing_track_ids)
        else:
            return N+1

    def save_to_disk(self):
        with open(os.path.join(OUTPUT_DIR, "{}.json".format(self.video_name)), "w") as f:
            json.dump(self.to_json(), f, indent=4)
