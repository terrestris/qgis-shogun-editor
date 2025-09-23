import os
import subprocess
import sys
from pathlib import Path
import urllib.request
import shutil

from pkg_resources import find_distributions
from PyQt5.QtWidgets import QMessageBox

SHOGUN_VENV_NAME = "shogun_qgis_venv"


def get_python_command():
    python_command = "python3" if shutil.which("python3") else "python"
    return python_command


def get_venv_python_path(venv_path):
    if sys.platform == "win32":
        venv_python_path = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python_command = get_python_command()
        venv_python_path = os.path.join(venv_path, "bin", python_command)
    return venv_python_path


def ensure_folder_exists(base_path: Path, folder_name: str) -> Path:
    path = base_path.joinpath(folder_name)
    path.mkdir(exist_ok=True, parents=True)
    return path


def get_requirements_path(use_dev: bool = False) -> Path:
    # we assume that a requirements.txt exists in a requirements folder
    path = Path(Path(__file__).parent.parent, "requirements", "development.txt" if use_dev else "requirements.txt")
    assert path.exists(), f"path not found {path}"
    return path


def dependencies_installed(requirements: str, path: str) -> bool:
    for d in find_distributions(path):
        entry = f"{d.key}=={d.version}"
        print(entry)
        if entry in requirements:
            requirements = requirements.replace(entry, "")

    print(requirements)
    requirements = (
        requirements.replace(" ", "").replace(";", "").replace(",", "")
    )

    print(requirements)
    if len(requirements) > 0:
        return False
    print("Dependencies already installed")
    return True


def ensure_venv(p, exit_on_miss: bool = False):
    if not os.path.exists(p) and not exit_on_miss:
        message = (
            "A Python virtual environment (venv) as well as models"
            " data are required to use the SHOGUN QGIS"
            " plugin.\n"
        )
        message += (
            "Would you like to create / install these " "required dependencies?"
        )

        reply = QMessageBox.question(
            None,
            "Missing VENV / Dependencies",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.No:
            return None

        python_command = get_python_command()
        subprocess.run([python_command, "-m", "venv", "--copies", p])
    if not os.path.exists(p) and exit_on_miss:
        raise Exception("Could not resolve venv path.")
    return p


def ensure_pip(venv_path) -> None:
    """Ensures pip and psutil are installed in the virtual environment."""
    print("Ensuring pip installation...")

    venv_python_path = get_venv_python_path(venv_path)

    try:
        # Check if ensurepip is available
        process_check = subprocess.run(
            [venv_python_path, "-c", "import ensurepip"],
            capture_output=True,
        )

        if process_check.returncode != 0:
            print("ensurepip module is missing. Installing ensurepip...")

            if sys.platform.startswith("linux"):
                subprocess.run(["sudo", "apt", "install", "-y",
                               "python3-ensurepip"])
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["brew", "install", "python3"])
            elif sys.platform == "win32":
                print("Windows should include ensurepip by default.")

        # Try installing pip using ensurepip
        process_cmp = subprocess.run(
            [venv_python_path, "-m", "ensurepip"],
            capture_output=True
        )

        if process_cmp.returncode == 0:
            print("Successfully installed pip using ensurepip.")
        else:
            print("Pip installation via ensurepip failed. Trying get-pip.py...")

            # Try to install pip using get-pip.py
            get_pip_path = Path(Path(__file__).parent.parent, "plugin_utils",
                                "get-pip.py")
            if not get_pip_path.exists():
                print("Downloading get-pip.py...")
                urllib.request.urlretrieve(
                    "https://bootstrap.pypa.io/get-pip.py",
                    str(get_pip_path))

            process_cmp = subprocess.run([venv_python_path, str(get_pip_path)],
                                         capture_output=True)

            if process_cmp.returncode == 0:
                print("Successfully installed pip using get-pip.py.")
            else:
                raise Exception(
                    f"Failed to install pip. Error: \
                    {process_cmp.stderr.decode()}")

        # Upgrade pip
        subprocess.run([venv_python_path, "-m", "pip", "install",
                       "--upgrade", "pip"], check=True)

        # Ensure psutil is installed
        try:
            subprocess.run([venv_python_path, "-c", "import psutil"],
                           check=True, capture_output=True)
            print("psutil is already installed.")
        except subprocess.CalledProcessError:
            print("psutil is not installed. Installing...")
            subprocess.run([venv_python_path, "-m", "pip", "install", "psutil"],
                           check=True)
            print("psutil successfully installed.")

        print("pip and psutil are installed successfully!")

    except subprocess.CalledProcessError as e:
        raise Exception(f"Error ensuring pip or psutil: {e.stderr.decode()}")


def install_requirements(venv_path: str, requirements_path: Path) -> None:
    print(
        "Installing / checking SHOGUN QGIS dependencies in venv {}".format(
            venv_path
        )
    )

    venv_python_path = get_venv_python_path(venv_path)

    print("{} -m pip install -r {}".format(venv_python_path, requirements_path))

    completed_process = subprocess.run(
        [
            venv_python_path,
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements_path),
        ],
        capture_output=True,
    )

    if completed_process.returncode != 0:
        m = (
            f"Failed to install dependencies through pip, got "
            f"{completed_process.returncode} as return code. "
            f"Full log: {completed_process}"
        )
        print(m)
        print(completed_process.stdout)
        print(completed_process.stderr)
        raise Exception(m)


def install_dependencies(venv_path: str, use_dev: bool = False) -> None:
    ensure_pip(venv_path)
    print("Check / install base requirements now")
    install_requirements(venv_path, get_requirements_path(use_dev))


def ensure_dependencies(venv_path: str) -> None:
    try:
        if venv_path is None:
            raise ImportError()
        print("Will install dependencies now")
        install_dependencies(venv_path)
        print("Successfully found dependencies")
        if os.environ.get('IS_DEV') == 'true':
            install_dependencies(venv_path, True)
            print("Successfully installed dev dependencies")
    except ImportError:
        raise Exception(
            "Cannot automatically ensure dependencies of SHOGUN QGIS Editor. "
            "Please try restarting QGIS and / or reinstalling the plugin."
        )
