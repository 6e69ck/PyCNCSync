import logging
import os
import platform
import shutil
import sys
import tempfile
import urllib.request
import zipfile


def rclone_binary_name():
    return "rclone.exe" if sys.platform.startswith("win") else "rclone"


def _emit_status(status_callback, message):
    if status_callback is not None:
        status_callback(message)


def _rclone_os_arch():
    if sys.platform.startswith("win"):
        os_name = "windows"
    elif sys.platform.startswith("linux"):
        os_name = "linux"
    elif sys.platform == "darwin":
        os_name = "osx"
    else:
        raise RuntimeError(f"Unsupported platform for auto-download: {sys.platform}")

    machine = platform.machine().lower()
    arch_map = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }
    arch = arch_map.get(machine)
    if arch is None:
        raise RuntimeError(f"Unsupported architecture for auto-download: {machine}")

    return os_name, arch


def ensure_rclone_binary(app_dir, status_callback=None):
    local_rclone = os.path.join(app_dir, rclone_binary_name())
    if os.path.exists(local_rclone):
        _emit_status(status_callback, "Using bundled rclone binary")
        return local_rclone

    os_name, arch = _rclone_os_arch()
    download_url = f"https://downloads.rclone.org/rclone-current-{os_name}-{arch}.zip"
    print(f"Local rclone not found. Downloading from: {download_url}")
    _emit_status(status_callback, "Downloading rclone...")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "rclone.zip")
            extract_dir = os.path.join(temp_dir, "extract")

            last_percent = -1

            def reporthook(block_count, block_size, total_size):
                nonlocal last_percent
                if total_size <= 0:
                    return
                percent = int(min(100, (block_count * block_size * 100) / total_size))
                rounded = (percent // 5) * 5
                if rounded != last_percent:
                    last_percent = rounded
                    _emit_status(status_callback, f"Downloading rclone... {rounded}%")

            urllib.request.urlretrieve(download_url, zip_path, reporthook=reporthook)
            _emit_status(status_callback, "Extracting rclone package...")
            with zipfile.ZipFile(zip_path, "r") as archive:
                archive.extractall(extract_dir)

            extracted_binary = None
            target_name = rclone_binary_name().lower()
            for root, _, files in os.walk(extract_dir):
                for filename in files:
                    if filename.lower() == target_name:
                        extracted_binary = os.path.join(root, filename)
                        break
                if extracted_binary is not None:
                    break

            if extracted_binary is None:
                raise RuntimeError("Downloaded archive does not contain rclone binary")

            _emit_status(status_callback, "Installing rclone binary...")
            shutil.copy2(extracted_binary, local_rclone)
            if not sys.platform.startswith("win"):
                os.chmod(local_rclone, 0o755)

            print(f"rclone downloaded to: {local_rclone}")
            _emit_status(status_callback, "rclone ready")
            return local_rclone
    except Exception:
        logging.exception("Failed to auto-download rclone binary")
        print("Failed to auto-download rclone. Falling back to system rclone in PATH.")
        _emit_status(status_callback, "Failed to download rclone; using system PATH")
        return "rclone"
