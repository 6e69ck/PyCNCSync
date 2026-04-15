import os

from watchdog.events import FileSystemEventHandler


class SyncHandler(FileSystemEventHandler):
    def __init__(self, queue_change):
        super().__init__()
        self.queue_change = queue_change

    def on_modified(self, event):
        if not event.is_directory:
            self.queue_change(event.src_path, "upload")

    def on_created(self, event):
        if not event.is_directory:
            self.queue_change(event.src_path, "upload")

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"File deleted: {os.path.basename(event.src_path)} - Restarting 2-second timer...")
            self.queue_change(event.src_path, "delete")

    def on_moved(self, event):
        if not event.is_directory:
            print(f"File moved: {os.path.basename(event.src_path)} -> {os.path.basename(event.dest_path)}")
            self.queue_change(event.src_path, "delete")
            self.queue_change(event.dest_path, "upload")
