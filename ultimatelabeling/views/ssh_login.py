import os
import paramiko
from scp import SCPClient
import time
import json

from PyQt5.QtWidgets import QGroupBox, QLabel, QLineEdit, QFormLayout, QPushButton, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from ultimatelabeling.models import StateListener, SSHCredentials
from ultimatelabeling.config import OUTPUT_DIR, SERVER_DIR


class SSHLogin(QGroupBox, StateListener):
    def __init__(self, state):
        super().__init__("SSH login")

        self.state = state
        self.state.add_listener(self)

        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        form_layout = QFormLayout()

        self.hostname = QLineEdit()
        form_layout.addRow(QLabel("Host IP:"), self.hostname)

        self.username = QLineEdit()
        form_layout.addRow(QLabel("Username:"), self.username)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        form_layout.addRow(QLabel("Password:"), self.password)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.on_connect_button_clicked)
        form_layout.addRow(self.connect_button)

        self.setLayout(form_layout)
        self.setFixedWidth(250)

        self.load_credentials()

    def load_credentials(self):
        self.hostname.setText(self.state.ssh_credentials.hostname)
        self.username.setText(self.state.ssh_credentials.username)
        self.password.setText(self.state.ssh_credentials.password)

    def save_credentials(self, hostname, username, password):
        self.state.ssh_credentials = SSHCredentials(hostname, username, password)

    def on_connect_button_clicked(self):
        hostname, username, password = self.hostname.text(), self.username.text(), self.password.text()

        try:
            self.ssh_client.connect(hostname, username=username, password=password)
        except paramiko.SSHException as e:
            QMessageBox.warning(self, "", "Couldn't connect to the server.\n{}".format(str(e)))
        else:
            self.save_credentials(hostname, username, password)
            self.connect_button.setText("Connected")
            self.connect_button.setEnabled(False)

            sftp = self.ssh_client.open_sftp()
    
            try:
                sftp.stat('UltimateLabeling_server')  # Files already exist on the server
            except IOError:  # We need to copy files to the server
                QMessageBox.warning(self, "", "Code is missing on the server.")
                return

        if self.ssh_client.get_transport():
            self.state.ssh_connected = True

            self.start_detection_server()
            self.start_tracking_servers()

            time.sleep(5)  # Let the server some time to start the socket servers

            if self.check_is_running():
                QMessageBox.information(self, "", "Connected!")
            else:
                QMessageBox.information(self, "", "An error occurred. Type `tmux ls` on the server.")

    def start_tracking_server(self):
        stdin, stdout, stderr = self.ssh_client.exec_command("tmux kill-session -t tracking")  # Killing possible previous socket server
        stdin, stdout, stderr = self.ssh_client.exec_command('cd UltimateLabeling_server && source siamMask/env/bin/activate && tmux new -d -s tracking "CUDA_VISIBLE_DEVICES=0 python -m tracker"')

        print(stdout.read().decode())
        print(stderr.read().decode())

        errors = stderr.read().decode()
        if errors:
            QMessageBox.warning(self, "", errors)
        else:
            self.state.tracking_server_running = True
            print("Tracking server started...")

    def start_tracking_servers(self):
        # Killing possible previous socket server
        stdin, stdout, stderr = self.ssh_client.exec_command("tmux kill-session -t tracking_1")
        stdin, stdout, stderr = self.ssh_client.exec_command("tmux kill-session -t tracking_2")
        stdin, stdout, stderr = self.ssh_client.exec_command("tmux kill-session -t tracking_3")

        stdin, stdout, stderr = self.ssh_client.exec_command('cd UltimateLabeling_server && source siamMask/env/bin/activate && tmux new -d -s tracking_1 '
                                                             '"CUDA_VISIBLE_DEVICES=0 python -m tracker -p 8787"')

        stdin, stdout, stderr = self.ssh_client.exec_command('cd UltimateLabeling_server && source siamMask/env/bin/activate && tmux new -d -s tracking_2 '
                                                             '"CUDA_VISIBLE_DEVICES=0 python -m tracker -p 8788"')

        stdin, stdout, stderr = self.ssh_client.exec_command('cd UltimateLabeling_server && source siamMask/env/bin/activate && tmux new -d -s tracking_3 '
                                                             '"CUDA_VISIBLE_DEVICES=0 python -m tracker -p 8789"')

        print(stdout.read().decode())
        print(stderr.read().decode())

        errors = stderr.read().decode()
        if errors:
            QMessageBox.warning(self, "", errors)
        else:
            self.state.tracking_server_running = True
            print("Tracking server started...")

    def start_detection_server(self):
        stdin, stdout, stderr = self.ssh_client.exec_command("tmux kill-session -t detection")  # Killing possible previous socket server
        stdin, stdout, stderr = self.ssh_client.exec_command('cd UltimateLabeling_server && source detection/env/bin/activate && tmux new -d -s detection "CUDA_VISIBLE_DEVICES=0 python -m detector"')

        print(stdout.read().decode())
        print(stderr.read().decode())

        errors = stderr.read().decode()
        if errors:
            QMessageBox.warning(self, "", errors)
        else:
            self.state.detection_server_running = True
            print("Detection server started...")


    def start_detached_detection(self, seq_path, crop_area=None, detector="YOLO"):
        stdin, stdout, stderr = self.ssh_client.exec_command("tmux kill-session -t detached")  # Killing possible previous socket server
        stdin, stdout, stderr = self.ssh_client.exec_command('cd UltimateLabeling_server && source detection/env/bin/activate && tmux new -d -s detached '
                                                             '"CUDA_VISIBLE_DEVICES=0 python -m detector_detached -s {} -d {}"'.format(seq_path, detector))

        print(stdout.read().decode())
        print(stderr.read().decode())

        errors = stderr.read().decode()
        if errors:
            QMessageBox.warning(self, "", errors)
        else:
            self.state.detection_detached_video_name = os.path.basename(seq_path)
            print("Detached detection server started...")

    def fetch_detached_info(self):
        local_info_file = os.path.join(OUTPUT_DIR, "running_info.json")
        server_info_file = os.path.join(SERVER_DIR, local_info_file)

        try:
            with SCPClient(self.ssh_client.get_transport()) as scp:
                scp.get(server_info_file, local_info_file)
        except IOError:
            QMessageBox.warning(self, "", "Information file not found on the server.")
            return

        with open(local_info_file, "r") as f:
            data = json.load(f)

        return data

    def load_detached_detections(self, video_name):
        local_detections_file = os.path.join(OUTPUT_DIR, "{}.json".format(video_name))
        server_info_file = os.path.join(SERVER_DIR, local_detections_file)

        try:
            with SCPClient(self.ssh_client.get_transport()) as scp:
                scp.get(server_info_file, local_detections_file)
        except IOError:
            QMessageBox.warning(self, "", "Outputs not found on the server.")
            return

    def check_is_running(self):
        stdin, stdout, stderr = self.ssh_client.exec_command("tmux ls")
        tmux_out = stdout.read().decode()

        if "detection" and "tracking" in tmux_out:
            return True

        return False

    def closeServers(self):
        if self.ssh_client.get_transport():
            print("closing servers")
            stdin, stdout, stderr = self.ssh_client.exec_command("tmux kill-session -t tracking")  # Killing possible previous socket server
            print(stdout, "+", stderr)
            stdin, stdout, stderr = self.ssh_client.exec_command("tmux kill-session -t detection")  # Killing possible previous socket server
            print(stdout, "+", stderr)
            print("servers closed")


class SCPThread(QThread):
    countChanged = pyqtSignal(int)
    messageAdded = pyqtSignal(str)

    def __init__(self, ssh_client):
        super().__init__()

        self.ssh_client = ssh_client
        self.total_files = 20
        self.nb_sent = 0

    def progress(self, filename, size, sent):
        if size == sent:
            self.nb_sent += 1
            self.countChanged.emit(self.nb_sent / self.total_files * 100)
            self.messageAdded.emit("Sent {}".format(filename.decode()))

    def run(self):
        with SCPClient(self.ssh_client.get_transport(), progress=self.progress) as scp:
            scp.put('server_files', recursive=True)

        self.countChanged.emit(0)
        self.messageAdded.emit("Installing requirements...")
        stdin, stdout, stderr = self.ssh_client.exec_command('cd server_files && virtualenv venv -p /usr/bin/python3')
        print("out", stdout.read().decode(), "err", stderr.read().decode())
        stdin, stdout, stderr = self.ssh_client.exec_command('source server_files/venv/bin/activate && cd server_files && pip3 install -r requirements.txt')
        print("out", stdout.read().decode(), "err", stderr.read().decode())
        self.countChanged.emit(100)

        # Downloading pretrained model
        self.countChanged.emit(0)
        self.messageAdded.emit("Downloading pretrained weights...")
        stdin, stdout, stderr = self.ssh_client.exec_command('cd server_files/siamMask/pretrained && wget -q http://www.robots.ox.ac.uk/~qwang/SiamMask_VOT.pth')
        print("out", stdout.read().decode(), "err", stderr.read().decode())
        self.countChanged.emit(100)
