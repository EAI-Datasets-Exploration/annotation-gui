import configparser
from pathlib import Path
import streamlit.web.cli as stcli
import subprocess
import sys


if __name__ == "__main__":
    metaconfig = configparser.ConfigParser()
    metaconfig.read("config.ini")

    app_name = metaconfig.get("app_paths", "app_name")
    app_path = metaconfig.get("app_paths", app_name)

    if app_path is None:
        print("Err: No app path found in config.ini")
        sys.exit(1)

    app_path = Path(app_path).resolve()
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])
