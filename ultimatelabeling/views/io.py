import glob
import os
import pandas as pd
from PyQt5.QtWidgets import QWidget, QMessageBox, QFileDialog
from ultimatelabeling.models import State
from ultimatelabeling import utils


class IO:
    def __init__(self, parent, state: State):
        self.parent = parent
        self.state = state

    def undo_ctrl(self):
        self.parent.img_widget.holding_ctrl = False

    def on_import_click(self):
        qm = QMessageBox
        res = qm.question(self.parent, "", "Are you sure you want to import? This will overwrite the current labels",
                          qm.Yes | qm.No)
        if res == qm.No:
            self.undo_ctrl()
            return

        folder_path = self.open_folder_name_dialog()
        if folder_path is None or folder_path == "":
            self.undo_ctrl()
            return

        imported_files = glob.glob(os.path.join(folder_path, "*.csv"))
        imported_files.extend(glob.glob(os.path.join(folder_path, "*.txt")))

        imported_base_names = [os.path.splitext(os.path.basename(file_path))[0] for file_path in imported_files]

        h, w = self.state.image_size

        counter = 0
        for file_name in self.state.get_file_names():
            if file_name in imported_base_names:
                idx = imported_base_names.index(file_name)
                df = pd.read_csv(imported_files[idx], names=["class_id", "xc", "yc", "w", "h"], sep=" ", header=None, index_col=False)

                # Convert coordinates from percentage to absolute
                df.xc, df.w = df.xc * w, df.w * w
                df.yc, df.h = df.yc * h, df.h * h

                df["x"] = df.xc - df.w / 2
                df["y"] = df.yc - df.h / 2
                df["polygon"] = ""
                df["kp"] = ""

                n = len(df)
                df["track_id"] = range(counter, counter + n)
                counter += n

                df = df[["track_id", "class_id", "x", "y", "w", "h", "polygon", "kp"]]

                self.state.track_info.write_from_df(df, file_name)

        self.state.notify_listeners("on_current_frame_change")
        self.undo_ctrl()
        QMessageBox.information(self.parent, "", "Done!")

    def on_export_click(self):
        file_path = self.save_file_dialog()
        if file_path is None or file_path == "":
            self.undo_ctrl()
            return

        df = self.state.track_info.to_df(self.state.get_file_names())

        df[["xc", "yc", "w", "h"]] = df[["xc", "yc", "w", "h"]].astype(int)

        df.to_csv(file_path, sep=" ", header=False, index=False)

        self.undo_ctrl()
        QMessageBox.information(self.parent, "", "Done!")

    def open_folder_name_dialog(self):
        options = QFileDialog.Options()
        folder_path = QFileDialog.getExistingDirectory(self.parent, "Import labels", options=options)
        return folder_path

    def save_file_dialog(self):
        file_name = "{}_tracked_all.csv".format(self.state.current_video)

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self.parent, "Export labels", file_name,
                                                   "All Files (*);;CSV (*.csv)", options=options)
        return file_path
