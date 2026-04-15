import logging
import os
import threading

from watchdog.observers import Observer

from config_store import (
    ensure_google_drive_login,
    get_local_folder,
    load_or_create_app_config,
    save_app_config,
    update_username_from_google_profile,
)
from file_watcher import SyncHandler
from rclone_bootstrap import ensure_rclone_binary
from settings import APP_CONFIG_PATH, APP_DIR, LOG_PATH, RCLONE_CONFIG
from settings_ui import show_settings_dialog
from startup_splash import StartupSplash
from sync_service import SyncService


logging.basicConfig(
    filename=LOG_PATH,
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
)


def quit_app(icon, item, observer_holder, sync_service):
    print("Quitting app...")
    sync_service.cancel_pending_sync()
    sync_service.stop_server_polling()
    observer = observer_holder.get("observer")
    if observer is not None:
        observer.stop()
        observer.join()
    icon.stop()


if __name__ == "__main__":
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

    splash_holder = {"window": None}
    tray = None
    observer_holder = {"observer": None}
    sync_service_holder = {"service": None}
    callbacks = {
        "restart_observer": lambda: None,
        "open_settings": lambda show_pull: None,
        "rclone_exe": None,
    }

    def startup_status(message, important=False):
        splash_exists = splash_holder["window"] is not None

        if not splash_exists and not important:
            return

        if splash_holder["window"] is None:
            try:
                splash_holder["window"] = StartupSplash("PyCNCSync Startup")
            except Exception:
                logging.exception("Failed to create startup splash")
                return

        splash_holder["window"].update_status(message)

    def bootstrap_status(message):
        important = "Downloading rclone" in message or "Failed" in message
        startup_status(message, important=important)

    def login_status(message):
        important = (
            "Opening Google login" in message
            or "Google login failed" in message
            or "Google login successful" in message
        )
        startup_status(message, important=important)

    # Load config early
    had_existing_config = os.path.exists(APP_CONFIG_PATH)
    app_config = load_or_create_app_config()

    # Create tray immediately
    try:
        from tray_ui import TrayController

        tray = TrayController()

    except Exception:
        logging.exception("Failed to load tray icons")
        raise

    def perform_startup():
        """Background startup task."""
        # Now continue with heavy startup work
        rclone_exe = ensure_rclone_binary(APP_DIR, status_callback=bootstrap_status)

        mode = app_config.get("mode", "client") if app_config else "client"

        # Only resolve username for client mode
        if mode == "client":
            is_logged_in = ensure_google_drive_login(rclone_exe, status_callback=login_status)
            if is_logged_in and app_config is not None:
                app_config = update_username_from_google_profile(
                    app_config,
                    rclone_exe,
                    status_callback=login_status,
                )
        else:
            # Server mode just needs to be logged in
            is_logged_in = ensure_google_drive_login(rclone_exe, status_callback=login_status)

        if app_config is not None:
            os.makedirs(get_local_folder(app_config), exist_ok=True)

        sync_service = SyncService(
            rclone_exe=rclone_exe,
            app_config=app_config,
            set_tray_state=tray.set_state if tray else lambda s: None,
        )
        sync_service_holder["service"] = sync_service
        
        # Store rclone_exe for use in login callback
        callbacks["rclone_exe"] = rclone_exe

        restart_observer_for_current_folder = make_restart_observer(observer_holder, sync_service)
        open_settings_and_apply = make_open_settings(observer_holder, sync_service, restart_observer_for_current_folder)

        # Store callbacks for tray menu
        callbacks["restart_observer"] = restart_observer_for_current_folder
        callbacks["open_settings"] = open_settings_and_apply

        if not had_existing_config:
            startup_status("Opening settings...", important=True)
            if splash_holder["window"] is not None:
                splash_holder["window"].close()
                splash_holder["window"] = None

            open_settings_and_apply(show_pull=False)

        mode = sync_service.app_config.get("mode", "client") if sync_service.app_config else "client"
        if mode == "client":
            startup_status(
                "Force-pushing local folder to Google Drive...",
                important=splash_holder["window"] is not None,
            )
            sync_service.push_local_to_remote(status_callback=startup_status, force=True)
            restart_observer_for_current_folder()
        else:
            startup_status(
                "Pulling entire CNC folder from Google Drive...",
                important=splash_holder["window"] is not None,
            )
            sync_service.pull_remote_to_local(status_callback=startup_status)
            sync_service.start_server_polling()

        startup_status("Startup complete", important=splash_holder["window"] is not None)
        if splash_holder["window"] is not None:
            splash_holder["window"].close()

        # Update tray icon and title to indicate startup is complete
        if tray is not None:
            tray.set_state("idle")
            tray.update_title("CNC Cloud Sync (Ready)")

        print(f"Using rclone binary: {rclone_exe}")
        print(f"Using app config: {APP_CONFIG_PATH}")
        print(f"Using rclone config at: {RCLONE_CONFIG}")
        print(f"Google Drive login ready: {is_logged_in}")

    def make_restart_observer(observer_holder, sync_service):
        def restart_observer_for_current_folder():
            current = observer_holder.get("observer")
            if current is not None:
                current.stop()
                current.join()

            new_observer = Observer()
            new_observer.schedule(
                SyncHandler(sync_service.queue_change),
                path=sync_service.local_folder,
                recursive=False,
            )
            new_observer.start()
            observer_holder["observer"] = new_observer
            print(f"Watching {sync_service.local_folder} for changes...")

        return restart_observer_for_current_folder

    def make_open_settings(observer_holder, sync_service, restart_observer_for_current_folder):
        def open_settings_and_apply(show_pull):
            if sync_service.app_config is None:
                return

            updated_config = show_settings_dialog(sync_service.app_config)
            if updated_config is None:
                return

            previous_folder = sync_service.local_folder
            previous_mode = sync_service.app_config.get("mode", "client")
            sync_service.app_config = updated_config
            os.makedirs(sync_service.local_folder, exist_ok=True)
            save_app_config(sync_service.app_config)

            if show_pull:
                sync_service.pull_remote_to_local()

            current_mode = sync_service.app_config.get("mode", "client")

            if sync_service.local_folder != previous_folder:
                if previous_mode == "client":
                    restart_observer_for_current_folder()
                elif previous_mode == "server":
                    sync_service.start_server_polling()

            if previous_mode != current_mode:
                if previous_mode == "client":
                    sync_service.cancel_pending_sync()
                    observer = observer_holder.get("observer")
                    if observer is not None:
                        observer.stop()
                        observer.join()
                        observer_holder["observer"] = None
                    sync_service.start_server_polling()
                else:
                    sync_service.stop_server_polling()
                    restart_observer_for_current_folder()

        return open_settings_and_apply

    # Start startup in a background thread
    startup_thread = threading.Thread(target=perform_startup, daemon=False)
    startup_thread.start()

    # Define callbacks that will use the startup thread's results
    def on_login_clicked(icon, item):
        sync_service = sync_service_holder["service"]
        if sync_service is None:
            return

        login_splash = None
        try:
            login_splash = StartupSplash("PyCNCSync Google Login")
        except Exception:
            logging.exception("Failed to create Google login splash")

        def login_status_callback(message):
            if login_splash is not None:
                login_splash.update_status(message)

        rclone_exe = callbacks.get("rclone_exe")
        if rclone_exe is None:
            if login_splash:
                login_splash.close()
            return

        login_ok = ensure_google_drive_login(rclone_exe, status_callback=login_status_callback)
        if login_ok and sync_service.app_config is not None:
            mode = sync_service.app_config.get("mode", "client")
            if mode == "client":
                sync_service.app_config = update_username_from_google_profile(
                    sync_service.app_config,
                    rclone_exe,
                    status_callback=login_status_callback,
                )
                save_app_config(sync_service.app_config)

        if login_splash is not None:
            login_splash.close()

    # Run the tray icon in the main thread
    if tray is not None:
        tray.run(
            on_sync_clicked=lambda icon, item: sync_service_holder["service"].on_sync_clicked(icon, item) if sync_service_holder["service"] else None,
            on_quit_clicked=lambda icon, item: quit_app(icon, item, observer_holder, sync_service_holder["service"]) if sync_service_holder["service"] else icon.stop(),
            on_login_clicked=on_login_clicked,
            on_settings_clicked=lambda icon, item: callbacks["open_settings"](show_pull=False),
        )
