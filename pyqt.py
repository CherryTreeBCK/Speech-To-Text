import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QColorDialog, QInputDialog
from PyQt5.QtCore import Qt

class GUI(QWidget):
    def __init__(self):
        super().__init__()

        # Window setup
        self.setWindowTitle("Text Overlay")
        self.setGeometry(100, 100, 400, 100)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.7)

        # Text label
        self.text_label = QLabel("Your text will appear here", self)
        self.text_label.setStyleSheet("background-color: white; font: 16pt Helvetica;")

        # Settings label (for simplicity, using text as a settings button)
        self.settings_label = QLabel("⚙", self)
        self.settings_label.setStyleSheet("font: 14pt Helvetica;")
        self.settings_label.move(380, 5)
        self.settings_label.mousePressEvent = self.open_settings

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.text_label)
        self.setLayout(layout)

        # Variables for dragging
        self.drag_position = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def open_settings(self, event):
        menu = self.create_settings_menu()
        menu.exec_(self.mapToGlobal(event.pos()))

    def create_settings_menu(self):
        from PyQt5.QtWidgets import QMenu

        menu = QMenu(self)
        menu.addAction("Change Background Color", self.change_color)
        menu.addAction("Change Translucency", self.change_translucency)
        return menu

    def change_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.setStyleSheet(f"background-color: {color.name()};")
            self.text_label.setStyleSheet(f"background-color: {color.name()}; font: 16pt Helvetica;")

    def change_translucency(self):
        alpha, ok = QInputDialog.getDouble(self, "Translucency", "Enter value (0.1 - 1.0):", min=0.1, max=1.0, decimals=2)
        if ok:
            self.setWindowOpacity(alpha)

    def update_text(self, new_text):
        self.text_label.setText(new_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = GUI()
    gui.show()
    sys.exit(app.exec_())
