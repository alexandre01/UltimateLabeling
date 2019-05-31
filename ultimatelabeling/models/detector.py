import torch
from .track_info import Detection
import json
import socket
import pickle
from ultimatelabeling import utils


class Detector:
    def __init__(self):
        self.use_cuda = torch.cuda.is_available()
        self.device = torch.device('cuda' if self.use_cuda else 'cpu')
        torch.backends.cudnn.benchmark = True

    def init(self):
        pass

    def detect(self, image_path, crop_area=None):
        """
        Output:
            detections ([Detection])
        """
        raise NotImplementedError

    def terminate(self):
        pass


class SocketDetector(Detector):
    HOST = "128.178.17.112"
    PORT = 8788
    TERMINATE_SIGNAL = b"terminate"

    def init(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.HOST, self.PORT))
        self.receive_ok_signal()

    def detect(self, image_path, detector="YOLO", crop_area=None):
        options = {
            "filename": image_path,
            "seq_path": None,
            "detector": detector,
            "crop_area": crop_area.to_json() if crop_area else None
        }
        self.send_options(options)

        detections = self.receive_detections()

        return detections

    def detect_sequence(self, seq_path, nb_frames, crop_area=None, detector="YOLO"):

        options = {
            "filename": None,
            "seq_path": seq_path,
            "detector": detector,
            "crop_area": crop_area.to_json() if crop_area else None
        }
        self.send_options(options)

        for i in range(nb_frames):
            detections = self.receive_detections()
            yield detections

    def send_image_path(self, image_path):
        data = image_path.encode()
        self.client_socket.sendall(data)

    def send_options(self, options):
        print(options)

        data = pickle.dumps(options)
        self.client_socket.sendall(data)

    def send_crop_area(self, crop_area):
        """
        crop_area (Bbox)
        """
        data = pickle.dumps(crop_area.to_json())
        self.client_socket.send(data)

    def receive_detections(self):
        json_response = utils.recv_data(self.client_socket)
        response = json.loads(json_response.decode())
        detections = [Detection.from_json(d) for d in response]
        return detections

    def receive_ok_signal(self):
        self.client_socket.recv(1024)

    def send_terminate_signal(self):
        self.client_socket.sendall(self.TERMINATE_SIGNAL)

    def terminate(self):
        self.send_terminate_signal()
        self.client_socket.close()
