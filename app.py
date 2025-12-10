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

# --- 3. CSS 스타일 (여기가 디자인의 핵심!) ---
st.markdown("""
<style>
    /* [메인 카드 디자인] 사이드바가 아닌 '메인 화면'의 컬럼만 카드처럼 꾸미기 */
    section[data-testid="stMain"] div[data-testid="stColumn"] {
        background-color: var(--secondary-background-color);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }

    /* [사이드바 초기화] 사이드바 안의 컬럼은 배경/테두리 없애기 (겹침 해결!) */
    section[data-testid="stSidebar"] div[data-testid="stColumn"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
    }

    /* [사이드바 말줄임표] 버튼 안의 텍스트가 길면 ... 으로 자르기 */
    section[data-testid="stSidebar"] .stButton button div p {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 150px;  /* 이 너비 넘어가면 ... 처리 */
    }

    /* [평가 버튼 디자인] 라디오 버튼 대신 깔끔한 칩(Chip) 스타일 */
    .stSegmentedControl {
        border: none !important;
    }
    
    /* [저장 버튼 중앙 정렬] 메인 화면의 버튼만 가운데로! */
    section[data-testid="stMain"] .stButton {
        display: flex;
        justify-content: center;
    }
    
    /* 저장 버튼 크기 및 스타일 */
    section[data-testid="stMain"] .stButton > button {
        width: 50%;
        min-width: 200px;
        border-radius: 20px;
        font-weight: bold;
    }

    /* 입력창 투명하게 */
    .stTextInput input {
        background-color: transparent !important;
    }
</style>
""", unsafe_allow_html=True)


# --- 4. 사이드바 (지난 기록) ---
with st.sidebar:
    st.title("📅 Romi's History")
    
    if st.button("➕ 새 주간 시작하기", use_container_width=True):
        st.session_state.current_data = None 
        st.rerun()

    st.divider()
    
    # 리스트 출력
    for i, item in enumerate(st.session_state.history):
        # gap="small"로 간격 좁힘
        col1, col2, col3 = st.columns([0.65, 0.2, 0.15], gap="small")
        
        # 제목 버튼 (길면 ... 처리됨)
        if col1.button(f"{item['title']}", key=f"load_{i}", use_container_width=True, help=item['title']):
            st.session_state.current_data = item
            st.rerun()
            
        # 복사 버튼 (아이콘만 깔끔하게)
        if col2.button("📋", key=f"copy_{i}", use_container_width=True, help="복사하기"):
            new_item = item.copy()
            new_item['id'] = str(datetime.datetime.now().timestamp())
            new_item['title'] = f"{datetime.date.today().month}월 {datetime.date.today().day}일 시작 (복사됨)"
            for day in new_item['content']:
                new_item['content'][day]['weight'] = ""
                new_item['content'][day]['eval'] = None
            
            st.session_state.history.insert(0, new_item)
            save_data(st.session_state.history)
            st.rerun()

        # 삭제 버튼
        if col3.button("❌", key=f"del_{i}", use_container_width=True, help="삭제하기"):
            del st.session_state.history[i]
            save_data(st.session_state.history)
            st.rerun()

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
        
        # [수정] 라디오 버튼 대신 'Segmented Control' (아이콘 버튼) 사용
        # 이게 바로 HTML처럼 누르면 선택되는 버튼이야!
        eval_val = day_data['eval']
        day_data['eval'] = st.segmented_control(
            "평가", 
            ["😍", "🙂", "😅"], 
            selection_mode="single",
            default=eval_val if eval_val in ["😍", "🙂", "😅"] else None,
            key=f"e_{day_code}",
            label_visibility="collapsed" # 라벨(글씨) 숨김
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

# 저장 버튼 (이름 변경 + 중앙 정렬)
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
