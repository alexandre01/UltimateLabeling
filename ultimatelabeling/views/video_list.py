from PyQt5.QtWidgets import QListWidget
from ultimatelabeling.models import StateListener, FrameMode


class VideoListWidget(QListWidget, StateListener):
    def __init__(self, state):
        super().__init__()

        self.state = state
        self.state.add_listener(self)

        for video_name in self.state.video_list:
            self.addItem(video_name)

        self.itemDoubleClicked.connect(self.on_list_clicked)

        self.setFixedWidth(150)

    def on_list_clicked(self, item):
        self.state.frame_mode = FrameMode.MANUAL
        self.state.set_current_video(item.text())

    def on_video_change(self):
        index = self.state.video_list.index(self.state.current_video)
        # self.item(index).setSelected(True)

