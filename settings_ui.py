import os
import tkinter as tk
from tkinter import filedialog, ttk

from config_store import get_local_folder


class SettingsDialog:
    def __init__(self, app_config):
        self.app_config = dict(app_config)
        self.result = None

        self.root = tk.Tk()
        self.root.title("PyCNCSync Settings")
        self.root.geometry("560x320")
        self.root.resizable(False, False)

        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Google Name Folder", font=("Segoe UI", 10, "bold")).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 4),
        )
        username = self.app_config.get("username", "")
        ttk.Label(frame, text=username or "(not resolved yet)").grid(row=1, column=0, columnspan=3, sticky="w")

        ttk.Label(frame, text="Mode", font=("Segoe UI", 10, "bold")).grid(
            row=2,
            column=0,
            sticky="w",
            pady=(16, 4),
        )

        self.mode_var = tk.StringVar(value=self.app_config.get("mode", "client"))
        ttk.Radiobutton(frame, text="Client", variable=self.mode_var, value="client").grid(
            row=3, column=0, sticky="w", padx=(20, 0)
        )
        ttk.Radiobutton(frame, text="Server", variable=self.mode_var, value="server").grid(
            row=3, column=1, sticky="w", padx=(20, 0)
        )

        ttk.Label(frame, text="Local Sync Folder", font=("Segoe UI", 10, "bold")).grid(
            row=4,
            column=0,
            sticky="w",
            pady=(16, 4),
        )

        self.local_folder_var = tk.StringVar(value=get_local_folder(self.app_config))
        self.local_folder_entry = ttk.Entry(frame, textvariable=self.local_folder_var, width=58)
        self.local_folder_entry.grid(row=5, column=0, columnspan=2, sticky="we", padx=(0, 8))

        browse_button = ttk.Button(frame, text="Browse", command=self._browse_folder)
        browse_button.grid(row=5, column=2, sticky="e")

        hint = ttk.Label(
            frame,
            text="Choose the local folder to keep in sync with your Google Drive subfolder.",
            foreground="#555555",
        )
        hint.grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 0))

        actions = ttk.Frame(frame)
        actions.grid(row=7, column=0, columnspan=3, sticky="e", pady=(20, 0))

        ttk.Button(actions, text="Cancel", command=self._cancel).pack(side="right")
        ttk.Button(actions, text="Save", command=self._save).pack(side="right", padx=(0, 8))

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        self.root.protocol("WM_DELETE_WINDOW", self._cancel)
        self._center_window()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(300, lambda: self.root.attributes("-topmost", False))

    def _center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _browse_folder(self):
        initial_dir = self.local_folder_var.get().strip() or os.path.expanduser("~")
        selected = filedialog.askdirectory(
            parent=self.root,
            title="Select local sync folder",
            initialdir=initial_dir,
            mustexist=False,
        )

        if isinstance(selected, (tuple, list)):
            selected = selected[0] if selected else ""

        selected = str(selected).strip()
        if selected:
            normalized = os.path.normpath(os.path.expanduser(selected))
            self.local_folder_var.set(normalized)

            # Also update the widget directly for Tk variants that delay StringVar refresh.
            self.local_folder_entry.delete(0, tk.END)
            self.local_folder_entry.insert(0, normalized)
            self.local_folder_entry.focus_set()
            self.local_folder_entry.icursor(tk.END)
            self.root.update_idletasks()

    def _save(self):
        self.app_config["local_folder"] = self.local_folder_var.get().strip()
        self.app_config["mode"] = self.mode_var.get()
        self.result = self.app_config
        self.root.destroy()

    def _cancel(self):
        self.result = None
        self.root.destroy()

    def show(self):
        self.root.mainloop()
        return self.result


def show_settings_dialog(app_config):
    dialog = SettingsDialog(app_config)
    return dialog.show()
