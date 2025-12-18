'''
project/
├─ build/
├─ dist/
│  └─ main/
│     ├─ _internal/
│     ├─ log_viewer.py
│     └─ main.exe
├─ log_viewer.py
├─ main.py
└─ main.spec

pyinstaller ^
  --onedir ^
  --console ^
  main.py

'''

# log_viewer.py

import streamlit as st
import requests
import math
from datetime import date
from streamlit_autorefresh import st_autorefresh

# ---------------- 상수 ----------------
PAGE_SIZE = 50
REFRESH_SEC = 10

LOG_CATEGORIES = {
    "System": 0,
    "Control": 1,
    "IO Device": 2,
    "Database": 3,
    "Network": 4,
    "Security": 5,
    "Script": 7,
    "Schedule": 8,
    "Recipe": 9,
}

LOG_TYPES = {
    "Info": 0,
    "Trace": 1,
    "Error": 2,
    "User": 3,
}

# ---------------- UI 기본 ----------------
st.set_page_config(layout="wide")
st.title("SCADA Log Viewer")

# ---------------- IP 입력 ----------------
ip = st.text_input("SCADA Server IP", value="192.168.0.240")
st.markdown(f"### 🖥️ Connected SCADA: `{ip}`")

API_URL = f"http://{ip}/api/g/log"

# ---------------- 필터 UI ----------------
col1, col2 = st.columns(2)

with col1:
    selected_categories = st.multiselect(
        "Log Category",
        options=list(LOG_CATEGORIES.keys()),
        default=list(LOG_CATEGORIES.keys()),
    )

with col2:
    selected_types = st.multiselect(
        "Log Type",
        options=list(LOG_TYPES.keys()),
        default=list(LOG_TYPES.keys()),
    )

# ---------------- Session State ----------------
if "page_no" not in st.session_state:
    st.session_state.page_no = 0

if "last_ip" not in st.session_state:
    st.session_state.last_ip = ip

if "last_log_signature" not in st.session_state:
    st.session_state.last_log_signature = None

if "render_logs" not in st.session_state:
    st.session_state.render_logs = []

if "render_total_count" not in st.session_state:
    st.session_state.render_total_count = 0

# ---------------- HTTP Session (Keep-Alive) ----------------
if "http_session" not in st.session_state:
    session = requests.Session()

    adapter = requests.adapters.HTTPAdapter(
        pool_connections=1,
        pool_maxsize=1,
        max_retries=3,
    )

    session.mount("http://", adapter)
    st.session_state.http_session = session


# IP 변경 시 초기화
if st.session_state.last_ip != ip:
    st.session_state.page_no = 0
    st.session_state.last_ip = ip
    st.session_state.last_log_signature = None
    st.session_state.render_logs = []
    st.session_state.render_total_count = 0

# ---------------- API 파라미터 구성 ----------------
category_values = [str(LOG_CATEGORIES[c]) for c in selected_categories]
category_values.append("6")  # 항상 포함
log_category_param = ",".join(sorted(set(category_values)))

log_type_param = ",".join(str(LOG_TYPES[t]) for t in selected_types)

BASE_PARAMS = {
    "pageSize": PAGE_SIZE,
    "pageNo": st.session_state.page_no,
    "searchPeriodFrom": date.today().isoformat(),
    "searchPeriodTo": date.today().isoformat(),
    "logCategory": log_category_param,
    "logType": log_type_param,
    "order": "DESC",
}

# ---------------- 데이터 로딩 ----------------
status_container = st.empty()

with status_container:
    with st.spinner("Refreshing logs..."):
        try:
            res = st.session_state.http_session.get(API_URL, params=BASE_PARAMS, timeout=(2, 5))
            data = res.json()["data"]
            logs = data["logList"]
            total_count = data["logTotalCount"]
        except Exception as e:
            st.error(f"로그 조회 실패: {e}")
            st.stop()

# ---------------- 변경 감지 ----------------
current_signature = (
    tuple(log["time"] for log in logs),
    total_count,
    st.session_state.page_no,
    log_category_param,
    log_type_param,
)

if current_signature != st.session_state.last_log_signature:
    st.session_state.last_log_signature = current_signature
    st.session_state.render_logs = logs
    st.session_state.render_total_count = total_count

# ---------------- 로그 출력 ----------------
log_container = st.container()

with log_container:
    if not st.session_state.render_logs:
        st.info("표시할 로그가 없습니다.")
    else:
        for log in st.session_state.render_logs:
            prefix = f"[{ip}] {log['time']} | "

            if log["logType"] == 2:
                st.error(prefix + log["logMessage"])
            else:
                st.text(prefix + log["logMessage"])

# ---------------- Pagination ----------------
total_pages = max(1, math.ceil(st.session_state.render_total_count / PAGE_SIZE))

col_prev, col_page, col_next = st.columns([1, 2, 1])

with col_prev:
    if st.button("◀ Previous", disabled=st.session_state.page_no == 0):
        st.session_state.page_no -= 1
        st.rerun()

with col_page:
    st.markdown(
        f"<div style='text-align:center;'>Page {st.session_state.page_no + 1} / {total_pages}</div>",
        unsafe_allow_html=True,
    )

with col_next:
    if st.button("Next ▶", disabled=st.session_state.page_no >= total_pages - 1):
        st.session_state.page_no += 1
        st.rerun()

# ---------------- Auto Refresh ----------------
st.caption(f"Auto refresh every {REFRESH_SEC}s")
st_autorefresh(interval=REFRESH_SEC * 1000, key="refresh")
