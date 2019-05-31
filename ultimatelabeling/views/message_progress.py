from PyQt5.QtWidgets import QMessageBox, QProgressBar, QApplication
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class MessageProgressBox(QMessageBox):
    def __init__(self, title):
        super().__init__()

        self.messages = [title]

        self.setIcon(QMessageBox.Information)
        self.setText(title)

        self.setInformativeText("")
        self.update_detailed_messages()

        self.progress = QProgressBar(self)
        self.progress.setFixedWidth(270)
        self.progress.setMaximum(100)

        l = self.layout()
        l.addWidget(self.progress, 1, 0, 1, l.columnCount(), Qt.AlignRight)

        self.setStandardButtons(QMessageBox.Cancel)

    def update_detailed_messages(self):
        self.setDetailedText("\n".join(self.messages))

    def add_message(self, message):
        self.messages.append(message)
        self.update_detailed_messages()

    def set_progress_value(self, value):
        self.progress.setValue(value)
