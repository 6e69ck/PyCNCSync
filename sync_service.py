import logging
import os
import subprocess
import threading
import sys

from config_store import get_drive_remote_path, get_local_folder
from settings import APP_CONFIG_PATH, RCLONE_CONFIG


def _no_window_creationflags():
    return subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


class SyncService:
    def __init__(self, rclone_exe, app_config, set_tray_state):
        self.rclone_exe = rclone_exe
        self.app_config = app_config
        self.set_tray_state = set_tray_state
        self.sync_timer = None
        self.has_pending_changes = False
        self.poll_timer = None
        self.lock = threading.Lock()

    @property
    def local_folder(self):
        if self.app_config is None:
            return None
        return get_local_folder(self.app_config)

    def queue_change(self, filepath, action):
        filename = os.path.basename(filepath)
        print(f"Activity on: {filename} - Restarting 2-second timer...")

        with self.lock:
            self.has_pending_changes = True

            if self.sync_timer is not None:
                self.sync_timer.cancel()

            self.sync_timer = threading.Timer(2.0, self.run_sync)
            self.sync_timer.start()

    def push_local_to_remote(self, status_callback=None, force=False):
        if self.app_config is None:
            logging.error("Push skipped: app config not ready")
            return False

        mode = self.app_config.get("mode", "client")
        if mode != "client":
            logging.error(f"Push not applicable in {mode} mode")
            return False

        if not self.app_config.get("username"):
            logging.error("Push skipped: username not set (Google login required)")
            return False

        local_folder = self.local_folder
        if not local_folder:
            logging.error("Push skipped: local folder not configured")
            return False

        os.makedirs(local_folder, exist_ok=True)
        remote_base = get_drive_remote_path(self.app_config)

        if status_callback is not None:
            status_callback("Pushing local files to Google Drive...")

        command = [
            self.rclone_exe,
            "sync",
            local_folder,
            remote_base,
            "--config",
            RCLONE_CONFIG,
            "--quiet",
        ]
        if force:
            # Force push uploads all local files and enforces local state remotely.
            command.insert(-1, "--ignore-times")

        try:
            subprocess.run(command, check=True, creationflags=_no_window_creationflags())
            if status_callback is not None:
                status_callback("Push to Google Drive complete")
            return True
        except Exception:
            logging.exception("Push to Google Drive failed")
            if status_callback is not None:
                status_callback("Push failed")
            return False

    def run_sync(self):
        if self.app_config is None:
            print(f"Sync failed: app config not ready at {APP_CONFIG_PATH}\\n")
            self.set_tray_state("error")
            logging.error("Sync aborted because app config is not ready")
            return

        mode = self.app_config.get("mode", "client")

        local_folder = self.local_folder
        if not local_folder:
            print(f"Sync failed: local folder is not configured in {APP_CONFIG_PATH}\\n")
            self.set_tray_state("error")
            logging.error("Sync aborted because local folder is not configured")
            return

        if mode == "client" and not self.app_config.get("username"):
            print(f"Sync failed: username not set (Google login required)\\n")
            self.set_tray_state("error")
            logging.error("Sync aborted because username is not set")
            return

        with self.lock:
            has_pending = self.has_pending_changes
            self.has_pending_changes = False

        if not has_pending:
            return

        if mode == "client":
            print("\n--- Dust settled. Syncing local folder to Google Drive... ---")
        else:
            print("\n--- Dust settled. Syncing Google Drive to local folder... ---")

        self.set_tray_state("uploading")

        if mode == "client":
            success = self.push_local_to_remote(force=False)
        else:
            success = self.pull_remote_to_local()

        if success:
            self.set_tray_state("idle")
            print("Sync successful.\n")
        else:
            self.set_tray_state("error")
            print("Sync failed.\n")

    def on_sync_clicked(self, icon, item):
        print("Manual sync triggered (processing pending changes).")
        self.run_sync()

    def start_server_polling(self):
        """Start polling Google Drive every 15 seconds in server mode."""
        if self.app_config is None:
            return

        mode = self.app_config.get("mode", "client")
        if mode != "server":
            return

        with self.lock:
            if self.poll_timer is not None:
                self.poll_timer.cancel()
            self.poll_timer = threading.Timer(15.0, self._poll_server)
            self.poll_timer.daemon = True
            self.poll_timer.start()
            print("Server polling started (15-second interval)")

    def _poll_server(self):
        """Internal method to poll Google Drive and reschedule."""
        if self.app_config is None:
            return

        mode = self.app_config.get("mode", "client")
        if mode != "server":
            return

        print("Polling Google Drive for changes...")
        self.pull_remote_to_local()

        # Reschedule the next poll
        with self.lock:
            if self.poll_timer is not None:
                self.poll_timer.cancel()
            self.poll_timer = threading.Timer(15.0, self._poll_server)
            self.poll_timer.daemon = True
            self.poll_timer.start()

    def stop_server_polling(self):
        """Stop the server polling timer."""
        with self.lock:
            if self.poll_timer is not None:
                self.poll_timer.cancel()
                self.poll_timer = None
                print("Server polling stopped")

    def pull_remote_to_local(self, status_callback=None):
        if self.app_config is None:
            logging.error("Pull skipped: app config not ready")
            return False

        local_folder = self.local_folder
        if not local_folder:
            logging.error("Pull skipped: local folder not configured")
            return False

        mode = self.app_config.get("mode", "client")
        if mode == "client" and not self.app_config.get("username"):
            logging.error("Pull skipped: username not set")
            return False

        os.makedirs(local_folder, exist_ok=True)
        remote_base = get_drive_remote_path(self.app_config)

        if status_callback is not None:
            status_callback("Pulling latest files from Google Drive...")

        try:
            subprocess.run(
                [
                    self.rclone_exe,
                    "sync",
                    remote_base,
                    local_folder,
                    "--config",
                    RCLONE_CONFIG,
                    "--quiet",
                ],
                check=True,
                creationflags=_no_window_creationflags(),
            )
            if status_callback is not None:
                status_callback("Pull from Google Drive complete")
            return True
        except Exception:
            logging.exception("Pull from Google Drive failed")
            if status_callback is not None:
                status_callback("Pull failed; continuing startup")
            return False

    def cancel_pending_sync(self):
        if self.sync_timer is not None:
            self.sync_timer.cancel()
