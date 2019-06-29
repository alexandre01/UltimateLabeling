from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui
from .views import *
from .models import State, StateListener, KeyboardNotifier
from .styles import Theme


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UltimateLabeler")

        self.central_widget = CentralWidget()
        self.central_widget.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(self.central_widget)
        self.central_widget.setFocus(True)

        self.statusBar()

        mainMenu = self.menuBar()

        fileMenu = mainMenu.addMenu('&File')
        helpMenu = mainMenu.addMenu('&Help')

        close = QAction('Close window', self)
        close.setShortcut('Ctrl+W')
        close.triggered.connect(self.close)
        fileMenu.addAction(close)

        import_action = QAction('Import', self)
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.central_widget.io.on_import_click)
        fileMenu.addAction(import_action)

        export = QAction('Export', self)
        export.setShortcut('Ctrl+E')
        export.triggered.connect(self.central_widget.io.on_export_click)
        fileMenu.addAction(export)

        """save = QAction('Save', self)
        save.setShortcut('Ctrl+S')
        save.triggered.connect()
        fileMenu.addAction(save)"""

        help = QAction('Documentation', self)
        help.triggered.connect(self.open_url)
        helpMenu.addAction(help)

        self.setCentralWidget(self.central_widget)

        self.show()
        self.center()

    def open_url(self):
        url = QtCore.QUrl('https://github.com/alexandre01/UltimateLabeling')
        if not QtGui.QDesktopServices.openUrl(url):
            QtGui.QMessageBox.warning(self, 'Open Url', 'Could not open url')

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

        self.keyboard_notifier = KeyboardNotifier()

        self.video_list_widget = VideoListWidget(self.state)
        self.img_widget = ImageWidget(self.state)
        self.slider = VideoSlider(self.state, self.keyboard_notifier)
        self.player = PlayerWidget(self.state)
        self.theme_picker = ThemePicker(self.state)
        self.options = Options(self.state)
        self.ssh_login = SSHLogin(self.state)

        self.detection_manager = DetectionManager(self.state, self.ssh_login)
        self.tracking_manager = TrackingManager(self.state)
        self.hungarian_button = HungarianManager(self.state)
        self.info_detection = InfoDetection(self.state)

        self.io = IO(self, self.state)

        self.keyPressEvent = self.keyboard_notifier.keyPressEvent
        self.keyReleaseEvent = self.keyboard_notifier.keyReleaseEvent
        self.keyboard_notifier.add_listeners(self.player, self.slider, self.img_widget, self.info_detection,
                                             self.tracking_manager)

        # Avoid keyboard not being triggered when focus on some widgets
        self.video_list_widget.setFocusPolicy(Qt.NoFocus)
        self.slider.setFocusPolicy(Qt.NoFocus)
        self.setFocusPolicy(Qt.StrongFocus)

        # Image widget thread signal, update function should always be called from main thread
        self.img_widget.signal.connect(self.img_widget.update)
        self.state.img_viewer = self.img_widget

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
        control_layout.addWidget(self.options)
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


if __name__ == '__main__':
    app = QApplication([])
    main_window = MainWindow()
    app.exec()


