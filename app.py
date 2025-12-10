import streamlit as st
import datetime
import json
import os
import time  # <--- [중요] 아까 이 친구가 빠져서 에러가 났던 거야!

# --- 1. 기본 설정 (페이지 제목, 디자인) ---
st.set_page_config(layout="wide", page_title="로미의 다이어트 매니저", page_icon="📅")

# 파일 저장소 이름
DB_FILE = "romi_data.json"

# --- 2. 데이터 불러오기/저장하기 함수 ---
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 초기 데이터 로드
if "history" not in st.session_state:
    st.session_state.history = load_data()

# --- 3. 사이드바 (지난 기록 목록) ---
with st.sidebar:
    st.title("📅 Romi's History")
    
    # 새 주간 시작 버튼
    if st.button("➕ 새 주간 시작하기", use_container_width=True):
        st.session_state.current_data = None 
        st.rerun()

    st.divider()
    
    # 저장된 기록 리스트 보여주기
    for i, item in enumerate(st.session_state.history):
        col1, col2, col3 = st.columns([0.6, 0.2, 0.2], gap="small")
        
        # 날짜 클릭하면 불러오기
        if col1.button(f"{item['title']}", key=f"load_{i}", use_container_width=True):
            st.session_state.current_data = item
            st.rerun()
            
        # 복사 버튼 (📋)
        if col2.button("📋", key=f"copy_{i}", help="이 식단 복사하기"):
            new_item = item.copy()
            new_item['id'] = str(datetime.datetime.now().timestamp())
            new_item['title'] = f"{datetime.date.today().month}월 {datetime.date.today().day}일 시작 (복사됨)"
            for day in new_item['content']:
                new_item['content'][day]['weight'] = ""
                new_item['content'][day]['eval'] = None
            
            st.session_state.history.insert(0, new_item)
            save_data(st.session_state.history)
            st.rerun()

        # 삭제 버튼 (X)
        if col3.button("❌", key=f"del_{i}"):
            del st.session_state.history[i]
            save_data(st.session_state.history)
            st.rerun()

# --- 4. 메인 화면 ---

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

# --- CSS 스타일 (다크모드 대응 + 버튼 중앙 정렬) ---
st.markdown("""
<style>
    /* 1. 카드 스타일 (다크모드 자동 대응) */
    div[data-testid="stColumn"] {
        background-color: var(--secondary-background-color);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    .stTextInput input {
        background-color: transparent !important;
    }
    
    /* 2. 저장 버튼 중앙 정렬 */
    div.stButton {
        display: flex;
        justify-content: center;
    }
    div.stButton > button {
        width: 60% !important;
        min-width: 300px;
        font-weight: bold;
        border-radius: 20px;
    }

    /* 3. [NEW] 사이드바 스타일 정리 (여기가 핵심!) */
    /* 사이드바 안의 버튼들 패딩 줄이기 */
    [data-testid="stSidebar"] button {
        padding: 0.3rem 0.5rem !important;
        font-size: 0.9rem !important;
    }
    
    /* 사이드바 안의 텍스트가 길면 ... 처리하기 */
    [data-testid="stSidebar"] button p {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 140px; /* 이 너비보다 길면 ... 으로 변함 */
        font-weight: normal !important;
    }
    
    /* 사이드바 컬럼 간격 좁히기 */
    [data-testid="stSidebar"] [data-testid="column"] {
        padding: 0 !important;
        gap: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# 요일별 카드 배치
cols = st.columns(4)
for idx, (day_code, label, icon) in enumerate(days_info[:4]):
    day_data = data['content'][day_code]
    with cols[idx]:
        st.subheader(f"{icon} {label}")
        day_data['weight'] = st.text_input("몸무게 (kg)", value=day_data['weight'], key=f"w_{day_code}")
        day_data['bf'] = st.text_input("아침", value=day_data['bf'], key=f"b_{day_code}")
        day_data['lc'] = st.text_input("점심", value=day_data['lc'], key=f"l_{day_code}")
        day_data['sn'] = st.text_input("간식", value=day_data['sn'], key=f"s_{day_code}")
        day_data['dn'] = st.text_input("저녁", value=day_data['dn'], key=f"d_{day_code}")
        day_data['eval'] = st.radio("평가", ["😍", "🙂", "😅"], horizontal=True, 
                                  index=["😍", "🙂", "😅"].index(day_data['eval']) if day_data['eval'] else 0,
                                  key=f"e_{day_code}")

st.write("") 

cols_bottom = st.columns(3)
for idx, (day_code, label, icon) in enumerate(days_info[4:]):
    day_data = data['content'][day_code]
    with cols_bottom[idx]:
        st.subheader(f"{icon} {label}")
        day_data['weight'] = st.text_input("몸무게 (kg)", value=day_data['weight'], key=f"w_{day_code}")
        day_data['bf'] = st.text_input("아침", value=day_data['bf'], key=f"b_{day_code}")
        day_data['lc'] = st.text_input("점심", value=day_data['lc'], key=f"l_{day_code}")
        day_data['sn'] = st.text_input("간식", value=day_data['sn'], key=f"s_{day_code}")
        day_data['dn'] = st.text_input("저녁", value=day_data['dn'], key=f"d_{day_code}")
        day_data['eval'] = st.radio("평가", ["😍", "🙂", "😅"], horizontal=True, 
                                  index=["😍", "🙂", "😅"].index(day_data['eval']) if day_data['eval'] else 0,
                                  key=f"e_{day_code}")

st.divider()

# 저장 버튼 (이제 빈 박스 없이 CSS로 자동 중앙 정렬됨!)
if st.button("💾 저장하기", type="primary"):
    existing_ids = [item['id'] for item in st.session_state.history]
    
    if data['id'] in existing_ids:
        index = existing_ids.index(data['id'])
        st.session_state.history[index] = data
    else:
        st.session_state.history.insert(0, data)
    
    save_data(st.session_state.history)
    st.success("저장 완료! 로미님 오늘도 파이팅! 🔥")
    time.sleep(1) # 이제 import time이 있어서 에러 안 남!
    st.rerun()

