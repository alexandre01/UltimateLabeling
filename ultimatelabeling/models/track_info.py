import json
import os
import pandas as pd
import numpy as np
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
    def __init__(self, video_name=""):
        self.video_name = video_name

        dir_name = os.path.join(OUTPUT_DIR, self.video_name)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        self.nb_track_ids = 0
        self.class_names = DEFAULT_CLASS_NAMES
        self.load_info()

        self.file_name = None
        self.detections = []

    def save_to_disk(self):
        self.write_info()
        self.write_detections(self.file_name)

    def load_info(self):
        json_file = os.path.join(OUTPUT_DIR, "{}/info.json".format(self.video_name))

        if not os.path.exists(json_file):
            return

        with open(json_file, "r") as f:
            data = json.load(f)
            self.nb_track_ids = data["nb_track_ids"]
            self.class_names = {int(k): v for k, v in json.loads(data["class_names"]).items()}

    def to_df(self, file_names):
        df = pd.DataFrame(columns=["frame", 'cls_no', "id", 'xc', 'yc', 'w', 'h', 'infer'])

        for i, file_name in enumerate(file_names):
            txt_file = os.path.join(OUTPUT_DIR, "{}/{}.txt".format(self.video_name, file_name))

            with open(txt_file, "r") as f:
                for d in f:
                    detection = json.loads(d.rstrip('\n'))
                    bbox = Bbox(*detection["bbox"]).xcycwh
                    df = df.append({"frame": i, "cls_no": detection["class_id"], "id": detection["track_id"],
                                    "xc": bbox[0], "yc": bbox[1], "w": bbox[2], "h": bbox[3], "infer": 0}, ignore_index=True)

        df[["frame", "cls_no", "id", "infer"]] = df[["frame", "cls_no", "id", "infer"]].astype(int)
        return df

    def from_df_all(self, df, file_names):

        for i, file_name in enumerate(file_names):
            detections = df[df.frame == i]

            txt_file = os.path.join(OUTPUT_DIR, "{}/{}.txt".format(self.video_name, file_name))
            with open(txt_file, "w") as f:
                for _, row in detections.iterrows():
                    # TODO: doing this we loose polgon, keypoints info

                    center, size = np.array([row["xc"], row["yc"]], dtype=float), np.array([row["w"], row["h"]], dtype=float)
                    bbox = Bbox.from_center_size(center, size)

                    d = Detection(class_id=int(row["cls_no"]), track_id=int(row["id"]),
                                  bbox=bbox)
                    f.write("{}\n".format(json.dumps(d.to_json())))

        # TODO: update nb_track_ids?

        # Update current detections
        self.detections = self.get_detections(self.file_name)

    def write_from_df(self, df, file_name):
        txt_file = os.path.join(OUTPUT_DIR, "{}/{}.txt".format(self.video_name, file_name))

        with open(txt_file, "w") as f:
            for _, row in df.iterrows():
                center, size = np.array([row["xc"], row["yc"]], dtype=float), np.array([row["w"], row["h"]], dtype=float)
                bbox = Bbox.from_center_size(center, size)
                d = Detection(class_id=int(row["cls_no"]), track_id=self.nb_track_ids, bbox=bbox)
                f.write("{}\n".format(json.dumps(d.to_json())))

                # Update nb_track_ids
                self.nb_track_ids += 1

        # Update current detections
        if file_name == self.file_name:
            self.detections = self.get_detections(self.file_name)

    def get_detections(self, file_name):
        txt_file = os.path.join(OUTPUT_DIR, "{}/{}.txt".format(self.video_name, file_name))

        if not os.path.exists(txt_file):
            return []

        with open(txt_file, "r") as f:
            return [Detection.from_json(json.loads(detection.rstrip('\n'))) for detection in f]

    def load_detections(self, file_name):
        self.file_name = file_name
        self.detections = self.get_detections(file_name)

    def write_info(self):
        json_file = os.path.join(OUTPUT_DIR, "{}/info.json".format(self.video_name))

        data = {
            "video_name": self.video_name,
            "nb_track_ids": self.nb_track_ids,
            "class_names": json.dumps(self.class_names)
        }

        with open(json_file, "w") as f:
            json.dump(data, f)

    def write_detections(self, file_name, detections=None):
        txt_file = os.path.join(OUTPUT_DIR, "{}/{}.txt".format(self.video_name, file_name))

        if detections is None:
            detections = self.detections

        if file_name == self.file_name:
            self.detections = detections

        with open(txt_file, "w") as f:
            for d in detections:
                f.write("{}\n".format(json.dumps(d.to_json())))

        self.nb_track_ids = max(self.nb_track_ids, max([d.track_id for d in detections] or [0]) + 1)

    def add_detection(self, detection, file_name=None):
        if file_name is None or file_name == self.file_name:
            self.detections.append(detection)
        else:
            txt_file = os.path.join(OUTPUT_DIR, "{}/{}.txt".format(self.video_name, file_name))

            with open(txt_file, "w") as f:
                f.write("{}\n".format(json.dumps(detection.to_json())))

        self.nb_track_ids = max(self.nb_track_ids, detection.track_id + 1)

    def remove_detection(self, track_id, file_name):
        """
        Removes detections with specific track_id from detections file
        Returns true if at least one detection was deleted
        """
        if file_name == self.file_name:
            self.detections = [d for d in self.detections if d.track_id != track_id]
            return True

        txt_file = os.path.join(OUTPUT_DIR, "{}/{}.txt".format(self.video_name, file_name))

        if not os.path.exists(txt_file):
            return False

        counter = 0
        with open(txt_file, "r+") as f:
            detections = f.readlines()
            f.seek(0)
            for d in detections:
                if json.loads(d.rstrip('\n'))["track_id"] != track_id:
                    f.write(d)
                else:
                    counter += 1
            f.truncate()

        return counter > 0

    def get_min_available_track_id(self):
        return self.nb_track_ids

    def modify_class_id(self, track_id, class_id, file_name):
        """
        Modifies class id with specific track_id from detections file
        Returns true if at least one modification was done
        """

        if file_name == self.file_name:
            for d in self.detections:
                if d.track_id == track_id:
                    d.class_id = class_id
            return True

        txt_file = os.path.join(OUTPUT_DIR, "{}/{}.txt".format(self.video_name, file_name))

        if not os.path.exists(txt_file):
            return False

        counter = 0
        with open(txt_file, "r+") as f:
            detections = f.readlines()
            f.seek(0)
            for d in detections:
                d_json = json.loads(d.rstrip('\n'))
                if d_json["track_id"] != track_id:
                    f.write(d)
                else:
                    d_json["class_id"] = class_id
                    f.write("{}\n".format(json.dumps(d_json)))
                    counter += 1
            f.truncate()

        return counter > 0