import sys
from PyQt5 import QtWidgets, QtGui, QtCore

class GUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text Overlay")
        self.setGeometry(100, 100, 400, 100)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.7)

        self.text_label = QtWidgets.QLabel("Your text will appear here", self)
        self.text_label.setStyleSheet("background-color: white;")
        self.text_label.setFont(QtGui.QFont("Helvetica", 16))
        self.text_label.setGeometry(0, 0, self.width(), self.height())

        # Settings icon
        self.settings_icon = QtWidgets.QLabel("⚙", self)
        self.settings_icon.setFont(QtGui.QFont("Helvetica", 14))
        self.settings_icon.setGeometry(self.width() - 20, 5, 20, 20)
        self.settings_icon.mousePressEvent = self.open_settings

        # Initialize variables for dragging and resizing
        self.start_x = 0
        self.start_y = 0
        self.drag_enabled = False

    def open_settings(self, event):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Toggle Dragging", self.toggle_dragging)
        menu.addAction("Toggle Resizing", self.toggle_resizing)
        menu.addAction("Change Background Color", self.change_color)
        menu.addAction("Change Translucency", self.change_translucency)
        menu.exec_(self.mapToGlobal(event.pos()))

    def toggle_dragging(self):
        self.drag_enabled = not self.drag_enabled

    def toggle_resizing(self):
        if self.isTopLevel():
            self.setWindowFlag(QtCore.Qt.FramelessWindowHint, False)
        else:
            self.setWindowFlag(QtCore.Qt.FramelessWindowHint, True)
        self.show()

    def change_color(self):
        color = QtWidgets.QColorDialog.getColor(self, title="Choose background color")
        if color.isValid():
            self.setStyleSheet(f"background-color: {color.name()};")
            self.text_label.setStyleSheet(f"background-color: {color.name()};")

    def change_translucency(self):
        alpha, ok = QtWidgets.QInputDialog.getDouble(self, "Translucency", "Enter value (0.1 - 1.0):", value=0.7, min=0.1, max=1.0, decimals=2)
        if ok:
            self.setWindowOpacity(alpha)

    def mousePressEvent(self, event):
        if self.drag_enabled:
            self.start_x = event.x()
            self.start_y = event.y()

    def mouseMoveEvent(self, event):
        if self.drag_enabled:
            x = self.x() + (event.x() - self.start_x)
            y = self.y() + (event.y() - self.start_y)
            self.move(x, y)

    def update_text(self, new_text):
        self.text_label.setText(new_text)
        self.update()

    def run(self):
        self.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    gui = GUI()
    sys.exit(app.exec_())
