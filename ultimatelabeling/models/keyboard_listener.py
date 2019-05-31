from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent


class KeyboardNotifier:
    def __init__(self):
        self.listeners = set()

    def keyPressEvent(self, event):
        if type(event) != QKeyEvent:
            event.ignore()

        if event.key() == Qt.Key_Space:
            self.notify_listeners("on_key_play_pause")

        if event.key() == Qt.Key_Left:
            self.notify_listeners("on_key_left")

        if event.key() == Qt.Key_Right:
            self.notify_listeners("on_key_right")

        if event.key() == Qt.Key_Control:
            self.notify_listeners("on_key_ctrl", True)

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
