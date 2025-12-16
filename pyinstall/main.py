# main.py

import subprocess
import os
import shutil
import sys

def main():
    if os.environ.get("STREAMLIT_RUNNING") == "1":
        return

    streamlit_cmd = shutil.which("streamlit")
    if not streamlit_cmd:
        return

    # ⭐ exe가 있는 디렉터리 기준으로 경로 계산
    base_dir = os.path.dirname(sys.executable)
    log_viewer_path = os.path.join(base_dir, "log_viewer.py")

    if not os.path.exists(log_viewer_path):
        return

    env = os.environ.copy()
    env["STREAMLIT_RUNNING"] = "1"

    subprocess.Popen(
        [
            streamlit_cmd,
            "run",
            log_viewer_path,
            "--server.port=8501",
            "--browser.serverAddress=localhost"
        ],
        env=env,
        cwd=base_dir   # ⭐ 이것도 중요
    )

if __name__ == "__main__":
    main()
