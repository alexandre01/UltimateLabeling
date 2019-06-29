from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent


class KeyboardNotifier:
    NUMBERS_KEYS = [Qt.Key_0, Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4, Qt.Key_5, Qt.Key_6, Qt.Key_7, Qt.Key_8, Qt.Key_9]

    def __init__(self):
        self.listeners = set()

    def keyPressEvent(self, event):
        if type(event) != QKeyEvent:
            event.ignore()

        if event.key() == Qt.Key_Space:
            self.notify_listeners("on_key_play_pause")

        if event.key() in [Qt.Key_Left, Qt.Key_A]:
            self.notify_listeners("on_key_left")

        if event.key() in [Qt.Key_Right, Qt.Key_D]:
            self.notify_listeners("on_key_right")

        if event.key() == Qt.Key_Control:
            self.notify_listeners("on_key_ctrl", True)

        if event.key() == Qt.Key_Delete:
            self.notify_listeners("on_key_delete")

        if event.key() in self.NUMBERS_KEYS:
            self.notify_listeners("on_key_number", self.NUMBERS_KEYS.index(event.key()))

        if event.key() in [Qt.Key_W, Qt.Key_S]:
            self.notify_listeners("on_key_ws", event.key() == Qt.Key_W)

        if event.key() in [Qt.Key_E, Qt.Key_R, Qt.Key_T]:
            self.notify_listeners("on_key_tracker", [Qt.Key_E, Qt.Key_R, Qt.Key_T].index(event.key()))

    def keyReleaseEvent(self, event):
          if event.key() == Qt.Key_Control:
            self.notify_listeners("on_key_ctrl", False)

    def add_listener(self, listener):
        self.listeners.add(listener)

    def add_listeners(self, *listeners):
        self.listeners.update(listeners)

    def notify_listeners(self, method_name, *args):
        for listener in self.listeners:
            func = getattr(listener, method_name)
            func(*args)


class KeyboardListener:
    def on_key_play_pause(self):
        pass

    def on_key_ctrl(self, holding):
        pass

    def on_key_left(self):
        pass

    def on_key_right(self):
        pass

    def on_key_delete(self):
        pass

    def on_key_number(self, number):
        pass

    def on_key_ws(self, go_up):
        pass

    def on_key_tracker(self, index):
        pass
