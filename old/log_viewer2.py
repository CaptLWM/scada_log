# log viewer.py

import streamlit as st
import requests
import math
import time
from datetime import date
from streamlit_autorefresh import st_autorefresh

PAGE_SIZE = 100
REFRESH_SEC = 2

st.set_page_config(layout="wide")
st.title("SCADA Log Viewer")

# ---------------- IP 입력 ----------------
ip = st.text_input(
    "SCADA Server IP",
    value="192.168.0.240",
    help="예: 192.168.0.240"
)
st.markdown(f"### 🖥️ Connected SCADA: `{ip}`")

API_URL = f"http://{ip}/api/g/log"

BASE_PARAMS = {
    "pageSize": PAGE_SIZE,
    "searchPeriodFrom": date.today().isoformat(),
    "searchPeriodTo": date.today().isoformat(),
    "logCategory": "",
    "logType": "",
    "order": "ASC"
}

# IP 변경 시 초기화
if "last_ip" not in st.session_state:
    st.session_state.last_ip = ip

if st.session_state.last_ip != ip:
    st.session_state.logs = []
    st.session_state.last_time = None
    st.session_state.last_ip = ip

# ---------------- API 함수 ----------------
def fetch_total_count():
    params = BASE_PARAMS | {"pageNo": 0, "pageSize": 1}
    res = requests.get(API_URL, params=params, timeout=3)
    return res.json()["data"]["logTotalCount"]

def fetch_page(page_no):
    params = BASE_PARAMS | {"pageNo": page_no}
    res = requests.get(API_URL, params=params, timeout=3)
    return res.json()["data"]["logList"]

def fetch_all_logs():
    total = fetch_total_count()
    pages = math.ceil(total / PAGE_SIZE)
    logs = []

    for p in range(pages):
        logs.extend(fetch_page(p))
        time.sleep(0.2)

    return logs

# ---------------- 초기 로딩 ----------------
if "logs" not in st.session_state:
    try:
        st.session_state.logs = fetch_all_logs()
        st.session_state.last_time = (
            st.session_state.logs[-1]["timeISO"]
            if st.session_state.logs else None
        )
    except Exception as e:
        st.error(f"초기 로그 조회 실패: {e}")
        st.stop()

# ---------------- 신규 로그 ----------------
try:
    new_logs = fetch_all_logs()
    if st.session_state.last_time:
        new_logs = [
            l for l in new_logs
            if l["timeISO"] > st.session_state.last_time
        ]

    if new_logs:
        st.session_state.logs.extend(new_logs)
        st.session_state.last_time = new_logs[-1]["timeISO"]

except Exception as e:
    st.warning(f"로그 갱신 실패: {e}")

# ---------------- 출력 ----------------
display_logs = sorted(
    st.session_state.logs,
    key=lambda x: x["timeISO"],
    reverse=True
)

for log in display_logs[:300]:
    if log["logType"] == 2:
        st.error(f'{log["time"]} | {log["logMessage"]}')
    else:
        st.text(f'{log["time"]} | {log["logMessage"]}')

st.caption(f"Auto refresh every {REFRESH_SEC}s")
st_autorefresh(interval=REFRESH_SEC * 1000, key="refresh")
