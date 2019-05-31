from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from .views import *
from .models import State, StateListener, KeyboardNotifier
from .styles import Theme


app = QApplication([])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UltimateLabeler")

        self.central_widget = CentralWidget()

        self.central_widget.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(self.central_widget)
        self.central_widget.setFocus(True)

        self.setCentralWidget(self.central_widget)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def closeEvent(self, event):
        print("exiting")
        self.central_widget.ssh_login.closeServers()
        self.central_widget.state.track_info.save_to_disk()
        self.central_widget.state.save_state()


class CentralWidget(QWidget, StateListener):
    def __init__(self):
        super().__init__()

        self.state = State()
        self.state.load_state()
        self.state.add_listener(self)

        self.video_list_widget = VideoListWidget(self.state)
        self.img_widget = ImageWidget(self.state)
        self.slider = VideoSlider(self.state)
        self.player = PlayerWidget(self.state)
        self.theme_picker = ThemePicker(self.state)
        self.ssh_login = SSHLogin(self.state)
        self.detection_manager = DetectionManager(self.state)
        self.tracking_manager = TrackingManager(self.state)
        self.hungarian_button = HungarianManager(self.state)
        self.info_detection = InfoDetection(self.state)

        self.keyboard_notifier = KeyboardNotifier()
        self.keyPressEvent = self.keyboard_notifier.keyPressEvent
        self.keyReleaseEvent = self.keyboard_notifier.keyReleaseEvent
        self.keyboard_notifier.add_listeners(self.player, self.slider, self.img_widget)

        # Avoid keyboard not being triggered when focus on some widgets
        self.video_list_widget.setFocusPolicy(Qt.NoFocus)
        self.slider.setFocusPolicy(Qt.NoFocus)

        self.make_layout()
        self.on_theme_change()

    def make_layout(self):
        main_layout = QHBoxLayout()

        navbar_box = QGroupBox("Videos")
        navbar_layout = QVBoxLayout()
        navbar_layout.addWidget(self.video_list_widget)
        navbar_box.setLayout(navbar_layout)
        main_layout.addWidget(navbar_box)

        image_box = QGroupBox("Image")
        image_layout = QVBoxLayout()
        image_layout.addWidget(self.img_widget)
        image_layout.addWidget(self.slider)
        image_box.setLayout(image_layout)
        main_layout.addWidget(image_box)

        control_box = QGroupBox("Control")
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.player)
        control_layout.addWidget(self.ssh_login)
        control_layout.addWidget(self.theme_picker)
        control_layout.addWidget(self.detection_manager)
        control_layout.addWidget(self.hungarian_button)
        control_layout.addWidget(self.tracking_manager)
        control_layout.addWidget(self.info_detection)

        control_layout.addStretch()
        control_box.setLayout(control_layout)
        main_layout.addWidget(control_box)

        self.setLayout(main_layout)

    def on_theme_change(self):
        app.setStyle("Fusion")
        app.setPalette(Theme.get_palette(self.state.theme))


main_window = MainWindow()
main_window.show()
main_window.center()

app.exec()


