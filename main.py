import sys
import os
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


# ================= WINDOWS TASKBAR ICON =================
app_id = "smart.pdf.fusion.pro"
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
except:
    pass

# ================= APP =================
app = QApplication(sys.argv)

# ================= ICON =================
icon_path = resource_path(os.path.join("assets", "ginger_96794.ico"))
icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
app.setWindowIcon(icon)

# ================= WINDOW =================
window = MainWindow()
window.setWindowIcon(icon)
window.show()


sys.exit(app.exec())