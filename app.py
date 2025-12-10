import streamlit as st
import datetime
import json
import os
import time

# --- 1. 기본 설정 ---
st.set_page_config(layout="wide", page_title="로미의 다이어트 매니저", page_icon="📅")

DB_FILE = "romi_data.json"

# --- 2. 데이터 함수 ---
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "history" not in st.session_state:
    st.session_state.history = load_data()

# --- 3. CSS 스타일 (디자인의 핵심!) ---
st.markdown("""
<style>
    /* [사이드바 너비 고정] */
    section[data-testid="stSidebar"] {
        min-width: 350px !important;
        max-width: 350px !important;
    }

    /* [메인 카드 디자인] */
    section[data-testid="stMain"] div[data-testid="stColumn"] {
        background-color: var(--secondary-background-color);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }

    /* [사이드바 안의 카드 박스 스타일] */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
        gap: 0.5rem; /* 박스 사이 간격 */
    }
    
    /* 사이드바 버튼 스타일 (투명하게, 글씨는 깔끔하게) */
    [data-testid="stSidebar"] .stButton button {
        background-color: transparent !important;
        border: none !important;
        color: inherit !important;
        padding: 0px !important;
        height: auto !important;
    }
    
    /* 사이드바 제목 말줄임표 (...) 처리 */
    [data-testid="stSidebar"] .stButton button p {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 160px; /* 제목 길이 제한 */
        font-weight: normal;
        font-size: 14px;
        text-align: left;
    }

    /* 삭제(X) 버튼 빨간색 강조 */
    .delete-btn button {
        color: #ff7675 !important;
        font-weight: bold !important;
    }

    /* 복사(clipboard) 버튼 파란색 강조 */
    .copy-btn button {
        color: #74b9ff !important;
    }

    /* [저장 버튼 중앙 정렬] */
    /* 버튼을 감싸는 컨테이너를 강제로 중앙으로 보냄 */
    .save-button-container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-top: 20px;
    }
    
    .save-button-container .stButton {
        width: auto !important;
    }
    
    .save-button-container .stButton > button {
        width: 300px !important; /* 버튼 고정 너비 */
        border-radius: 50px;
        font-weight: bold;
        padding: 10px 20px;
    }

    /* 입력창 배경 투명 */
    .stTextInput input {
        background-color: transparent !important;
    }
</style>
""", unsafe_allow_html=True)


# --- 4. 사이드바 (지난 기록) ---
with st.sidebar:
    st.title("📅 Romi's History")
    
    if st.button("➕ 새 주간 시작하기", use_container_width=True, type="primary"):
        st.session_state.current_data = None 
        st.rerun()

    st.write("") # 여백

    # 리스트 출력
    for i, item in enumerate(st.session_state.history):
        # 하나의 박스(Container) 안에 3개의 컬럼을 넣음
        with st.container(border=True):
            # [삭제 X] - [제목 (불러오기)] - [복사] 비율 설정
            c_del, c_load, c_copy = st.columns([0.15, 0.7, 0.15])
            
            # 1. 삭제 버튼 (좌측)
            with c_del:
                st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                if st.button("✕", key=f"del_{i}", help="삭제"):
                    del st.session_state.history[i]
                    save_data(st.session_state.history)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # 2. 제목 버튼 (가운데, 클릭 시 로드)
            with c_load:
                if st.button(f"{item['title']}", key=f"load_{i}"):
                    st.session_state.current_data = item
                    st.rerun()
            
            # 3. 복사 버튼 (우측)
            with c_copy:
                st.markdown('<div class="copy-btn">', unsafe_allow_html=True)
                if st.button("📋", key=f"copy_{i}", help="복사해서 새 주간 만들기"):
                    new_item = item.copy()
                    new_item['id'] = str(datetime.datetime.now().timestamp())
                    new_item['title'] = f"{datetime.date.today().month}월 {datetime.date.today().day}일 시작 (복사됨)"
                    for day in new_item['content']:
                        new_item['content'][day]['weight'] = ""
                        new_item['content'][day]['eval'] = None
                    st.session_state.history.insert(0, new_item)
                    save_data(st.session_state.history)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)


# --- 5. 메인 화면 ---

if "current_data" not in st.session_state or st.session_state.current_data is None:
    today_str = f"{datetime.date.today().month}월 {datetime.date.today().day}일 시작 주간"
    st.session_state.current_data = {
        "id": str(datetime.datetime.now().timestamp()),
        "title": today_str,
        "goal": "",
        "content": {day: {"weight": "", "bf": "", "lc": "", "sn": "", "dn": "", "eval": None} 
                    for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
    }

data = st.session_state.current_data
days_info = [
    ("Mon", "월요일", "🐻"), ("Tue", "화요일", "🔥"), ("Wed", "수요일", "🥗"),
    ("Thu", "목요일", "🥩"), ("Fri", "금요일", "🍷"), ("Sat", "토요일", "🛍️"), ("Sun", "일요일", "🛁")
]

st.title("🏃‍♀️ 로미의 유지어터 매니저")
new_title = st.text_input("날짜/제목", value=data['title'])
data['title'] = new_title
data['goal'] = st.text_input("이번 주 목표", value=data['goal'], placeholder="예: 평일 저녁 쉐이크, 물 2L 마시기")

st.divider()

# 요일별 카드 배치
cols = st.columns(4)
for idx, (day_code, label, icon) in enumerate(days_info[:4]):
    day_data = data['content'][day_code]
    with cols[idx]:
        st.subheader(f"{icon} {label}")
        day_data['weight'] = st.text_input("몸무게", value=day_data['weight'], key=f"w_{day_code}")
        day_data['bf'] = st.text_input("아침", value=day_data['bf'], key=f"b_{day_code}")
        day_data['lc'] = st.text_input("점심", value=day_data['lc'], key=f"l_{day_code}")
        day_data['sn'] = st.text_input("간식", value=day_data['sn'], key=f"s_{day_code}")
        day_data['dn'] = st.text_input("저녁", value=day_data['dn'], key=f"d_{day_code}")
        
        eval_val = day_data['eval']
        day_data['eval'] = st.segmented_control(
            "평가", 
            ["😍", "🙂", "😅"], 
            selection_mode="single",
            default=eval_val if eval_val in ["😍", "🙂", "😅"] else None,
            key=f"e_{day_code}",
            label_visibility="collapsed"
        )

st.write("") 

cols_bottom = st.columns(3)
for idx, (day_code, label, icon) in enumerate(days_info[4:]):
    day_data = data['content'][day_code]
    with cols_bottom[idx]:
        st.subheader(f"{icon} {label}")
        day_data['weight'] = st.text_input("몸무게", value=day_data['weight'], key=f"w_{day_code}")
        day_data['bf'] = st.text_input("아침", value=day_data['bf'], key=f"b_{day_code}")
        day_data['lc'] = st.text_input("점심", value=day_data['lc'], key=f"l_{day_code}")
        day_data['sn'] = st.text_input("간식", value=day_data['sn'], key=f"s_{day_code}")
        day_data['dn'] = st.text_input("저녁", value=day_data['dn'], key=f"d_{day_code}")
        
        eval_val = day_data['eval']
        day_data['eval'] = st.segmented_control(
            "평가", 
            ["😍", "🙂", "😅"], 
            selection_mode="single",
            default=eval_val if eval_val in ["😍", "🙂", "😅"] else None,
            key=f"e_{day_code}",
            label_visibility="collapsed"
        )

st.divider()

# [저장 버튼 완벽 중앙 정렬]
# 컨테이너 div를 만들어서 그 안에 버튼을 넣는 방식
st.markdown('<div class="save-button-container">', unsafe_allow_html=True)

if st.button("💾 저장하기", type="primary"):
    existing_ids = [item['id'] for item in st.session_state.history]
    
    if data['id'] in existing_ids:
        index = existing_ids.index(data['id'])
        st.session_state.history[index] = data
    else:
        st.session_state.history.insert(0, data)
    
    save_data(st.session_state.history)
    st.success("저장 완료! 로미님 오늘도 파이팅! 🔥")
    time.sleep(1) 
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
