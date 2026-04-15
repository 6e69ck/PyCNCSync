import tkinter as tk
from tkinter import ttk


class StartupSplash:
    def __init__(self, title="PyCNCSync Startup"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("460x150")
        self.root.resizable(False, False)

        self.status_var = tk.StringVar(value="Starting...")

        container = ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)

        title_label = ttk.Label(container, text="PyCNCSync", font=("Segoe UI", 14, "bold"))
        title_label.pack(anchor="w")

        self.status_label = ttk.Label(container, textvariable=self.status_var, wraplength=420)
        self.status_label.pack(anchor="w", pady=(10, 8))

        self.progress = ttk.Progressbar(container, mode="indeterminate", length=420)
        self.progress.pack(anchor="w", fill="x")
        self.progress.start(12)

        self._center_window()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after(300, lambda: self.root.attributes("-topmost", False))
        self.root.update_idletasks()
        self.root.update()

    def _center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def update_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()
        self.root.update()

    def close(self):
        self.progress.stop()
        self.root.update_idletasks()
        self.root.destroy()
