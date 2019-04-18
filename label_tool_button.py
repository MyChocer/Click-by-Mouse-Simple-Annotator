# -*- coding: UTF-8 -*-

import os
import sys
import json

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from libs.toolbar import ToolBar

import yaml


__appname__ = 'label_tool'
__config__ = 'config.yaml'


class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        # load config file
        self.config = self.load_config(__config__)
        # file list
        self.file_list = []
        self.curr_dir_path = None
        self.curr_img_idx = None

        self.init_ui()

    def load_config(self, config):
        """load label from config file"""
        with open(config, 'r') as f:
            config = yaml.load(f)
        return config

    def init_ui(self):
        """init ui"""
        self.setWindowTitle(__appname__)
        self.setGeometry(300, 300, 1900, 800)
        # self.statusBar().showMessage('Close')

        self._init_toolbar()
        self._init_img_viewer()
        self._init_label_button()
        self._init_file_list()

        self.show()


    def _init_toolbar(self):
        open_dir_act = QAction('Open', self)
        open_dir_act.setShortcut('Ctrl+O')
        open_dir_act.triggered.connect(self.open_dir)

        prev_act = QAction('previous', self)
        prev_act.triggered.connect(self.open_prev_img)
        prev_act.setShortcut('A')

        next_act = QAction('next', self)
        next_act.triggered.connect(self.open_next_img)
        next_act.setShortcut('D')

        exit_act = QAction('exit', self)
        exit_act.setShortcut('Ctrl+Q')
        exit_act.triggered.connect(self.close)

        toolbar = ToolBar('toolbar')
        toolbar.addAction(open_dir_act)
        toolbar.addAction(prev_act)
        toolbar.addAction(next_act)
        toolbar.addSeparator()
        toolbar.addAction(exit_act)
        self.addToolBar(Qt.LeftToolBarArea, toolbar)


    def _init_img_viewer(self):
        self.img_viewer = QLabel('img')
        self.img_viewer.setAlignment(Qt.AlignCenter)
        self.img_viewer.setBaseSize(1280, 720)
        self.img_viewer.setScaledContents(True)
        self.img_viewer.setMargin(20)
        self.setCentralWidget(self.img_viewer)

    def _init_label_button(self):
        head_layer = QVBoxLayout()
        for label_name, label_idx in self.config['label'].items():
            button = 'button_{}'.format(label_idx)
            ## initialize the button
            setattr(self, button, QPushButton(label_name, self))
            ## call out function
            getattr(self, button).clicked.connect(self.rb_clicked)
            ## set button size
            getattr(self, button).setMinimumHeight(60)
            ## add the button to the layout
            head_layer.addWidget(getattr(self, button))
       

        self.head_gbox = QGroupBox('status', self)
        self.head_gbox.setLayout(head_layer)

        label_selector_layout = QVBoxLayout()
        label_selector_layout.addWidget(self.head_gbox)


        label_selector_widget = QWidget()
        label_selector_widget.setLayout(label_selector_layout)
        self.label_selector_dock = QDockWidget('Label Select', self)
        self.label_selector_dock.setObjectName('labels')
        self.label_selector_dock.setWidget(label_selector_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.label_selector_dock)



    def rb_clicked(self):
        if self.curr_img_idx == None:
            QMessageBox.information(self,                         
                                    "warning",
                                    "Please open the image folder",
                                    QMessageBox.Ok)

            return

        self.setWindowTitle(self.curr_dir_path + ' * ')

        label_name = self.sender().text()
        label = self.config['label'][label_name]
        self.save_anno(label)
        self.open_next_img()


    def _init_file_list(self):
        self.file_list_widget = QListWidget()
        self.file_list_widget.itemDoubleClicked.connect(self.file_item_double_clicked)
        self.file_list_dock = QDockWidget('File List', self)
        self.file_list_dock.setObjectName('files')
        self.file_list_dock.setWidget(self.file_list_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.file_list_dock)


    def file_item_double_clicked(self, item):
        file_name = item.text()
        img_idx = self.file_list.index(file_name)
        self._switch_img(img_idx)


    def open_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, 'Open Folder', os.path.expanduser('~'))
        if dir_path:
            self._import_dir_images(dir_path)


    def _import_dir_images(self, dir_path):
        if self.open_dir == dir_path:
            return

        self.curr_dir_path = dir_path
        self.file_list_widget.clear()

        self.file_list = sorted([name for name in os.listdir(dir_path) if self._is_img(name)])
        if not self.file_list:
            return

        for idx, file_path in enumerate(self.file_list):
            item = QListWidgetItem(file_path)
            item.setFlags(item.flags() ^ Qt.ItemIsUserCheckable)
            if self._has_label_file(idx):
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.file_list_widget.addItem(item)

        init_idx = 0
        self._switch_img(init_idx)
        self.setWindowTitle(dir_path)


    def _is_img(self, file_name):
        ext = file_name.split('.')[-1]
        return ext in ['jpg', 'jpeg', 'png', 'bmp']


    def save_anno(self, content):
        if self.curr_img_idx == None:
            self._warning_box(title="warning", message="Please open the image folder")
            return

        label_name = self._get_label_name(self.curr_img_idx)
        label_path = os.path.join(self.curr_dir_path, label_name)

        try:
            with open(label_path, 'w') as fout:
                json.dump(content, fout)
        except Exception as e:
            QMessageBox.warning(self, 'warning', str(e))
            return

        self.setWindowTitle(self.curr_dir_path)
        item = self.file_list_widget.item(self.curr_img_idx)
        item.setCheckState(Qt.Checked)

    def _get_label_name(self, img_idx):
        img_name = self.file_list[img_idx]
        label_name = img_name.split('.')[0] + '.json'
        return label_name

    def open_next_img(self):
        if self.curr_img_idx == None:
            self._warning_box(title="warning", message="Please open the image folder")
            return

        if self.curr_img_idx == len(self.file_list) - 1:
            self._warning_box(title="warning", message="Finished!!")
            return

        next_img_idx = self.curr_img_idx + 1
        self._switch_img(next_img_idx)

    def open_prev_img(self):
        if self.curr_img_idx == None:
            self._warning_box(title="warning", message="Please open the image folder")
            return

        if self.curr_img_idx == 0:
            self._warning_box(title="warning", message="No previous image. It's the first image.")
            return

        prev_img_idx = self.curr_img_idx - 1
        self._switch_img(prev_img_idx)

    def _switch_img(self, img_idx):
        self._set_default_color()
        if img_idx == self.curr_img_idx:
            return

        img_name = self.file_list[img_idx]
        img_path = os.path.join(self.curr_dir_path, img_name)

        if not self._load_img(img_path):
            return

        self.setWindowTitle(self.curr_dir_path)
        self.curr_img_idx = img_idx
        file_widget_item = self.file_list_widget.item(img_idx)
        file_widget_item.setSelected(True)

        if self._has_label_file(img_idx):
            label = self._load_label(img_idx)
            self._set_color_by_label(label)

    def _set_default_color(self):
        for label_name, label_idx in self.config['label'].items():
            button = 'button_{}'.format(label_idx)
            ## set the button color to the default color
            getattr(self, button).setStyleSheet("background-color: white")
            ## set button size  

    def _set_color_by_label(self, label):
        for label_name, label_idx in self.config['label'].items():
            if label_idx == label:
                button = 'button_{}'.format(label_idx)
                ## set the button color to the default color
                getattr(self, button).setStyleSheet("background-color: red")

    def _load_img(self, img_path):
        try:
            with open(img_path, 'rb') as f:
                img_data = f.read()
        except Exception as e:
            QMessageBox.warning(self, 'Warning', str(e))
            return

        img = QImage.fromData(img_data)
        if img.isNull():
            QMessageBox.warning(self, 'Warning', 'Invalid Image')
            return False

        pixmap = QPixmap.fromImage(img)
        pixmap.scaled(860, 500, Qt.KeepAspectRatio)
        self.img_viewer.setPixmap(pixmap)

        return True

    def _has_label_file(self, img_idx):
        label_name = self._get_label_name(img_idx)
        label_path = os.path.join(self.curr_dir_path, label_name)

        return os.path.exists(label_path)

    def _load_label(self, img_idx):
        label_name = self._get_label_name(img_idx)
        label_path = os.path.join(self.curr_dir_path, label_name)

        try:
            with open(label_path, 'r') as fin:
                curr_label = json.load(fin)
            print('[load]', label_name, curr_label)
            return curr_label
        except Exception as e:
            QMessageBox.warning(self, 'Warning', str(e))
            return None

    def _warning_box(self, title, message):
        return QMessageBox.information(self,                         
                                    title,
                                    message,
                                    QMessageBox.Ok)

    def closeEvent(self, event):
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
