import os
import sys

DEFAULT_LOCAL_FOLDER = os.path.expanduser("~/Documents/NC Programs")
RCLONE_REMOTE_NAME = "pycncsync"
DRIVE_ROOT_DIR = "PyCNCSync"
DRIVE_SHARED_FOLDER_ID = "1QFLqdWeb_WRyeksI-1Dx4mkeJd654m8g"

if getattr(sys, "frozen", False):
    # PyInstaller bundle
    BASE_DIR = sys._MEIPASS
else:
    # Development
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

APP_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else BASE_DIR

RCLONE_CONFIG = os.path.join(APP_DIR, "rclone.conf")
APP_CONFIG_PATH = os.path.join(APP_DIR, "config.json")
LOG_PATH = os.path.join(APP_DIR, "PyCNCSync.log")

ICONS_DIR = os.path.join(BASE_DIR, "icons")
IDLE_ICON = os.path.join(ICONS_DIR, "idle.png")
UPLOADING_ICON = os.path.join(ICONS_DIR, "uploading.png")
ERROR_ICON = os.path.join(ICONS_DIR, "error.png")
