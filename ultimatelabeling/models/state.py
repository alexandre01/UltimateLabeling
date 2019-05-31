import pickle
import os
import glob
import re
from ultimatelabeling.styles import Theme
from .ssh_credentials import SSHCredentials
from .track_info import TrackInfo
from ultimatelabeling import utils
from ultimatelabeling.config import DATA_DIR, STATE_PATH


class FrameMode:
    MANUAL = "manual"  # for manually choosing the current frame
    CONTROLLED = "controlled"  # when the current frame is being controlled by some thread (Player, Tracker, ...)


class State:
    def __init__(self):
        self.video_list = []
        self.current_video = None
        self.current_frame = 0
        self.nb_frames = 0
        self.file_names = []
        self.theme = Theme.DARK
        self.ssh_credentials = SSHCredentials()
        self.track_info = TrackInfo()
        self.detections = []
        self.current_detection = None
        self.frame_mode = FrameMode.MANUAL

        self.ssh_connected = False
        self.tracking_server_running = False
        self.detection_server_running = False

        self.keypoints_show_bbox = False
        self.keypoints_instance_color = False
        self.bbox_class_color = False

        self.visible_area = (0, 0, 0, 0)

        self.listeners = set()

    def find_videos(self):
        print(DATA_DIR)
        return next(os.walk(DATA_DIR))[1]

    def check_raw_videos(self):
        files = glob.glob(os.path.join(DATA_DIR, "*.mp4"))
        files.extend(glob.glob(os.path.join(DATA_DIR, "*.mov")))

        for file in files:
            base = os.path.basename(file)
            filename = os.path.splitext(base)[0]

            if filename not in self.video_list:
                print("Extracting video {}...".format(base))
                utils.convert_video_to_frames(file, os.path.join(DATA_DIR, filename))
        self.video_list = self.find_videos()

    def update_file_names(self):
        if self.current_video:
            self.file_names = sorted(glob.glob(os.path.join(DATA_DIR, self.current_video, '*.jpg')), key = utils.natural_sort_key)
            self.nb_frames = len(self.file_names)

    def save_state(self):
        with open(STATE_PATH, 'wb') as f:
            state_dict = {k: v for k, v in self.__dict__.items() if k != "listeners" and k != "track_info"}
            pickle.dump(state_dict, f)

    def load_state(self):
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH, 'rb') as f:
                self.__dict__.update(pickle.load(f))

        # Reinitialize SSH connection info
        self.ssh_connected = False
        self.tracking_server_running = False
        self.detection_server_running = False

        self.video_list = self.find_videos()
        self.check_raw_videos()

        if self.current_video not in self.video_list:
            self.current_video = self.video_list[0] if len(self.video_list) > 0 else None
            self.current_frame = 0

        self.update_file_names()
        self.track_info = TrackInfo(self.current_video, self.file_names)
        self.detections = self.track_info.detections[self.current_frame]
        self.frame_mode = FrameMode.MANUAL

    def set_current_frame(self, current_frame, frame_mode=None):
        self.current_frame = current_frame

        if frame_mode is not None:
            self.frame_mode = frame_mode

        self.detections = self.track_info.detections[self.current_frame]

        self.notify_listeners("on_current_frame_change")

    def increase_current_frame(self, frame_mode=None):
        new_frame = min(self.current_frame + 1, self.nb_frames - 1)
        self.set_current_frame(new_frame, frame_mode=frame_mode)

    def decrease_current_frame(self, frame_mode=None):
        new_frame = max(self.current_frame - 1, 0)
        self.set_current_frame(new_frame, frame_mode=frame_mode)

    def set_current_video(self, video_name):
        if video_name != self.current_video:
            self.track_info.save_to_disk()

            self.current_video = video_name
            self.update_file_names()
            self.current_frame = 0
            self.track_info = TrackInfo(self.current_video, self.file_names)
            self.detections = self.track_info.detections[self.current_frame]
            self.current_detection = None
            self.frame_mode = FrameMode.MANUAL

            self.notify_listeners("on_video_change")

    def set_theme(self, theme):
        if self.theme != theme:
            self.theme = theme
            self.notify_listeners("on_theme_change")

    def add_detection(self, detection, frame):
        self.track_info.detections[frame].append(detection)

        print("d", detection.track_id)
        self.track_info.nb_track_ids = max(self.track_info.nb_track_ids, detection.track_id + 1)
        print("n", self.track_info.nb_track_ids)

        if frame == self.current_frame:
            self.current_detection = detection

    def set_detections(self, detections, frame):
        self.track_info.detections[frame] = detections

        self.track_info.nb_track_ids = max(self.track_info.nb_track_ids, max([d.track_id for d in detections]) + 1)

        if frame == self.current_frame:
            self.detections = self.track_info.detections[frame]

    def remove_detection(self, detection_index=None, detection=None):
        if detection_index is not None:
            self.detections.pop(detection_index)
        elif detection is not None:
            self.detections.remove(detection)

        self.notify_listeners("on_detection_change")
    
    def remove_detection_and_future(self, detection_index=None, detection=None):
        if detection_index is not None:
            detection = self.detections[detection_index]

        track_id = detection.track_id
        
        for i in range(self.current_frame, self.nb_frames):
            detections = self.track_info.detections[i]
            n = len(detections)
            for j in range(n-1, -1, -1):
                if detections[j].track_id == track_id:
                    detections.pop(j)

        self.notify_listeners("on_detection_change")
    
    def set_current_detection(self, detection):
        self.current_detection = detection
        self.detections.append(self.current_detection)
        self.track_info.nb_track_ids = max(self.track_info.nb_track_ids, detection.track_id + 1)

        self.notify_listeners("on_detection_change")

    def set_keypoints_show_bbox(self, value):
        self.keypoints_show_bbox = value
        self.notify_listeners("on_detection_change")
    def set_keypoints_instance_color(self, value):
        self.keypoints_instance_color = value
        self.notify_listeners("on_detection_change")
    def set_bbox_class_color(self, value):
        self.bbox_class_color = value
        self.notify_listeners("on_detection_change")

    def add_listener(self, listener):
        self.listeners.add(listener)

    def notify_listeners(self, method_name):
        for listener in self.listeners:
            func = getattr(listener, method_name)
            func()


class StateListener:
    def on_current_frame_change(self):
        pass

    def on_video_change(self):
        pass

    def on_theme_change(self):
        pass

    def on_detection_change(self):
        pass
