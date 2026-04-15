import configparser
import json
import logging
import os
import subprocess
import sys
import urllib.error
import urllib.request

from settings import (
    APP_CONFIG_PATH,
    DEFAULT_LOCAL_FOLDER,
    DRIVE_SHARED_FOLDER_ID,
    RCLONE_CONFIG,
    RCLONE_REMOTE_NAME,
)


def _emit_status(status_callback, message):
    if status_callback is not None:
        status_callback(message)


def _no_window_creationflags():
    return subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def load_or_create_app_config():
    default_config = {
        "username": "",
        "local_folder": DEFAULT_LOCAL_FOLDER,
        "mode": "client",
    }

    if not os.path.exists(APP_CONFIG_PATH):
        with open(APP_CONFIG_PATH, "w", encoding="utf-8") as config_file:
            json.dump(default_config, config_file, indent=2)
        print(f"Created {APP_CONFIG_PATH}.")
        return default_config.copy()

    try:
        with open(APP_CONFIG_PATH, "r", encoding="utf-8") as config_file:
            config_data = json.load(config_file)
    except Exception:
        logging.exception("Failed to read config.json at %s", APP_CONFIG_PATH)
        print(f"Failed to read {APP_CONFIG_PATH}.")
        return None

    for key, value in default_config.items():
        if key not in config_data:
            config_data[key] = value

    return config_data


def save_app_config(config_data):
    with open(APP_CONFIG_PATH, "w", encoding="utf-8") as config_file:
        json.dump(config_data, config_file, indent=2)


def _read_rclone_parser():
    parser = configparser.RawConfigParser()
    if os.path.exists(RCLONE_CONFIG):
        parser.read(RCLONE_CONFIG, encoding="utf-8")
    return parser


def _extract_access_token_from_rclone_config():
    parser = _read_rclone_parser()
    if not parser.has_section(RCLONE_REMOTE_NAME):
        return None

    token_str = parser.get(RCLONE_REMOTE_NAME, "token", fallback="")
    if not token_str:
        return None

    try:
        token_data = json.loads(token_str)
    except Exception:
        logging.exception("Failed to parse token from rclone config")
        return None

    return token_data.get("access_token")


def _get_google_display_name(access_token):
    request = urllib.request.Request(
        "https://www.googleapis.com/drive/v3/about?fields=user(displayName,emailAddress)",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))

    user = payload.get("user", {})
    display_name = (user.get("displayName") or "").strip()
    if display_name:
        return display_name

    email = (user.get("emailAddress") or "").strip()
    if email and "@" in email:
        return email.split("@", 1)[0]

    return ""


def update_username_from_google_profile(config_data, rclone_exe, status_callback=None):
    _emit_status(status_callback, "Fetching Google profile...")

    # Trigger token refresh so rclone.conf contains a fresh access token.
    subprocess.run(
        [rclone_exe, "about", f"{RCLONE_REMOTE_NAME}:", "--config", RCLONE_CONFIG],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )

    access_token = _extract_access_token_from_rclone_config()
    if not access_token:
        logging.error("Could not read Google access token from rclone config")
        _emit_status(status_callback, "Could not read Google account token")
        return config_data

    try:
        display_name = _get_google_display_name(access_token)
    except urllib.error.HTTPError:
        logging.exception("Failed to fetch Google profile information")
        _emit_status(status_callback, "Failed to fetch Google profile")
        return config_data
    except Exception:
        logging.exception("Unexpected error fetching Google profile information")
        _emit_status(status_callback, "Unexpected Google profile error")
        return config_data

    if not display_name:
        logging.error("Google profile did not provide a display name")
        _emit_status(status_callback, "Google profile missing display name")
        return config_data

    first_name = display_name.split()[0]
    first_name = "".join(ch for ch in first_name if ch.isalnum() or ch in ("-", "_"))
    if not first_name:
        logging.error("Derived first name from Google profile was empty")
        _emit_status(status_callback, "Could not derive first name from Google profile")
        return config_data

    if config_data.get("username") != first_name:
        config_data["username"] = first_name
        save_app_config(config_data)
        print(f"Using Google first-name folder: {first_name}")

    _emit_status(status_callback, f"Using Drive subfolder: {first_name}")

    return config_data



def ensure_rclone_drive_remote():
    parser = _read_rclone_parser()

    if not parser.has_section(RCLONE_REMOTE_NAME):
        parser.add_section(RCLONE_REMOTE_NAME)

    section = parser[RCLONE_REMOTE_NAME]
    section["type"] = "drive"
    section.setdefault("scope", "drive")
    section["root_folder_id"] = DRIVE_SHARED_FOLDER_ID

    with open(RCLONE_CONFIG, "w", encoding="utf-8") as config_file:
        parser.write(config_file)


def ensure_google_drive_login(rclone_exe, status_callback=None):
    _emit_status(status_callback, "Preparing Google Drive remote...")
    ensure_rclone_drive_remote()

    remote = f"{RCLONE_REMOTE_NAME}:"
    verify_command = [rclone_exe, "about", remote, "--config", RCLONE_CONFIG]
    reconnect_command = [
        rclone_exe,
        "config",
        "reconnect",
        remote,
        "--config",
        RCLONE_CONFIG,
        "--auto-confirm",
    ]

    try:
        _emit_status(status_callback, "Checking existing Google login...")
        subprocess.run(
            verify_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=_no_window_creationflags(),
        )
        _emit_status(status_callback, "Google Drive already logged in")
        return True
    except Exception:
        print("Google Drive login required. Starting rclone OAuth flow...")
        _emit_status(status_callback, "Opening Google login in browser...")

    try:
        subprocess.run(
            reconnect_command,
            check=True,
            creationflags=_no_window_creationflags(),
        )
        _emit_status(status_callback, "Verifying Google login...")
        subprocess.run(
            verify_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=_no_window_creationflags(),
        )
        print("Google Drive login successful.")
        _emit_status(status_callback, "Google login successful")
        return True
    except Exception:
        logging.exception("Google Drive OAuth/login failed")
        print("Google Drive login failed. Re-run from tray menu after completing browser auth.")
        _emit_status(status_callback, "Google login failed")
        return False


def get_drive_remote_path(config_data):
    """Get the remote path for the current config (client or server mode)."""
    mode = config_data.get("mode", "client")
    if mode == "server":
        return f"{RCLONE_REMOTE_NAME}:"
    # Client mode: user's subfolder
    username = config_data["username"].strip().strip("/")
    return f"{RCLONE_REMOTE_NAME}:{username}"


def get_local_folder(config_data):
    folder = (config_data.get("local_folder") or DEFAULT_LOCAL_FOLDER).strip()
    return os.path.normpath(os.path.expanduser(folder))
