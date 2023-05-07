import sys
from typing import Optional
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenu, QMenuBar,
                             QAction, QVBoxLayout, QPushButton, QFileDialog,
                             QTextEdit, QWidget)
from PyQt5.QtGui import QIcon


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Instance variables
        self.dark_theme: bool = False
        self.directory_button: QPushButton
        self.file_button: QPushButton
        self.text_widget: QTextEdit
        self.directory_button = QPushButton('Choose Directory', self)
        self.file_button = QPushButton('Choose File', self)
        self.text_widget = QTextEdit(self)
        self.init_ui()

    def init_ui(self) -> None:
        self.setWindowTitle('Amazing Modern GUI')

        # Set the icon for the GUI
        self.setWindowIcon(QIcon('path/to/icon.png'))

        # Menu bar
        menu_bar = self.menuBar()
        file_menu = QMenu('File', self)
        menu_bar.addMenu(file_menu)

        # Basic list in menu
        basic_list = QAction('Basic List', self)
        file_menu.addAction(basic_list)

        # Theme toggle in menu
        theme_toggle = QAction('Toggle Theme', self)
        theme_toggle.triggered.connect(self.toggle_theme)
        file_menu.addAction(theme_toggle)

        # Central widget
        central_widget = QWidget()
        layout = QVBoxLayout()

        # Button to choose directory

        self.directory_button.clicked.connect(self.choose_directory)
        layout.addWidget(self.directory_button)

        # Button to choose file

        self.file_button.clicked.connect(self.choose_file)
        layout.addWidget(self.file_button)

        # Text widget
        layout.addWidget(self.text_widget)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def choose_directory(self) -> None:
        directory: Optional[str] = QFileDialog.getExistingDirectory(self, 'Select Directory')
        if directory:
            print(f'Selected Directory: {directory}')

    def choose_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select File')
        if file_path:
            with open(file_path, 'r') as file:
                content = file.read()
                self.text_widget.setText(content)

    def toggle_theme(self) -> None:
        if not self.dark_theme:
            self.dark_theme = True
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #232323; }
                QLabel, QPushButton, QMenuBar, QMenu { color: #FFFFFF; }
                QTextEdit { background-color: #353535; color: #FFFFFF; }
            """)
        else:
            self.dark_theme = False
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #F0F0F0; }
                QLabel, QPushButton, QMenuBar, QMenu { color: #000000; }
                QTextEdit { background-color: #FFFFFF; color: #000000; }
            """)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
