import pystray
from PIL import Image

from settings import IDLE_ICON, UPLOADING_ICON, ERROR_ICON

try:
    # Internal pystray win32 constants are needed to forward left click to popup menu.
    from pystray._util import win32 as pystray_win32
except Exception:
    pystray_win32 = None


def _create_starting_icon():
    """Create a red dot icon for starting state."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    pixels = img.load()
    # Draw a red circle in the center
    center_x, center_y = 32, 32
    radius = 12
    for x in range(64):
        for y in range(64):
            dx = x - center_x
            dy = y - center_y
            if dx*dx + dy*dy <= radius*radius:
                pixels[x, y] = (255, 0, 0, 255)
    return img


class TrayController:
    def __init__(self):
        self.icon = None
        self.images = self._load_icon_images()

    def _load_icon_images(self):
        return {
            "starting": _create_starting_icon(),
            "idle": Image.open(IDLE_ICON),
            "uploading": Image.open(UPLOADING_ICON),
            "error": Image.open(ERROR_ICON),
        }

    def set_state(self, state):
        if self.icon is None:
            return

        image = self.images.get(state)
        if image is not None:
            self.icon.icon = image

    def on_icon_clicked(self, icon, item):
        if pystray_win32 is not None and hasattr(icon, "_on_notify"):
            icon._on_notify(None, pystray_win32.WM_RBUTTONUP)

    def run(self, on_sync_clicked, on_quit_clicked, on_login_clicked=None, on_settings_clicked=None):
        menu_items = [
            pystray.MenuItem("Open Menu", self.on_icon_clicked, default=True, visible=False),
            pystray.MenuItem("Sync Now", on_sync_clicked),
        ]

        if on_login_clicked is not None:
            menu_items.append(pystray.MenuItem("Google Login", on_login_clicked))

        if on_settings_clicked is not None:
            menu_items.append(pystray.MenuItem("Settings", on_settings_clicked))

        menu_items.append(pystray.MenuItem("Quit", on_quit_clicked))

        menu = pystray.Menu(*menu_items)

        self.icon = pystray.Icon("CNCSync", self.images["starting"], "CNC Cloud Sync (Starting...)", menu)
        self.icon.run()

    def update_title(self, title):
        """Update the tray icon tooltip title."""
        if self.icon is not None:
            self.icon.title = title
