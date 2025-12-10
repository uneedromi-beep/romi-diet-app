import streamlit as st
import datetime
import json
import os
import time
import gspread
from google.oauth2.service_account import Credentials

# --- 1. 기본 설정 ---
st.set_page_config(layout="wide", page_title="로미의 다이어트 매니저", page_icon="📅")

# --- 2. 구글 시트 연결 함수 ---
@st.cache_resource
def get_google_sheet():
    try:
        key_dict = st.secrets["service_account"]
    except Exception:
        st.error("🚨 Secrets 설정 오류")
        return None

    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    try:
        sh = client.open("diet_db")
        return sh.sheet1
    except Exception as e:
        st.error(f"🚨 연결 실패: {e}")
        return None

# --- 3. 데이터 함수 ---
def load_data():
    sheet = get_google_sheet()
    if sheet is None: return []

    try:
        raw_data = sheet.col_values(1)
        history = []
        for item in raw_data:
            if item.strip():
                try:
                    history.append(json.loads(item))
                except json.JSONDecodeError:
                    continue
        return history
    except Exception:
        return []

def save_data(data):
    sheet = get_google_sheet()
    if sheet is None: return

    try:
        sheet.clear()
        rows = [[json.dumps(item, ensure_ascii=False)] for item in data]
        if rows:
            sheet.update('A1', rows)
    except Exception as e:
        st.error(f"저장 실패: {e}")

# 초기 데이터 로드
if "history" not in st.session_state:
    st.session_state.history = load_data()

# --- 4. CSS 스타일 (플로팅 버튼 & 깔끔한 사이드바) ---
st.markdown("""
<style>
    /* [1. 메인 화면 카드 디자인] */
    section[data-testid="stMain"] div[data-testid="stColumn"] {
        background-color: var(--secondary-background-color);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    
    /* [2. 사이드바 디자인 - HTML 감성] */
    /* 사이드바 너비: PC에서는 좀 넓게, 모바일은 자동 */
    @media (min-width: 992px) {
        section[data-testid="stSidebar"] {
            min-width: 300px !important;
            max-width: 350px !important;
        }
    }
    
    /* 사이드바 안의 버튼들 투명하고 깔끔하게 (테두리 제거) */
    [data-testid="stSidebar"] .stButton button {
        background-color: transparent !important;
        border: none !important;
        color: inherit !important;
        text-align: left !important;
        padding: 0px !important;
        box-shadow: none !important;
    }
    
    /* 사이드바 제목 텍스트 스타일 */
    [data-testid="stSidebar"] .stButton button p {
        font-size: 15px !important;
        font-weight: 500 !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 150px;
    }

    /* 리스트 간격 조정 */
    [data-testid="stSidebar"] hr {
        margin: 0.5rem 0 !important;
    }

    /* 아이콘 버튼들 (삭제, 복사) 크기 키움 */
    .icon-btn button span {
        font-size: 1.2rem !important;
    }
    .delete-btn button span { color: #ff7675; }
    .copy-btn button span { color: #74b9ff; }

    /* [3. 플로팅 저장 버튼 (우측 하단 고정)] */
    .floating-save-btn {
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 9999;
    }
    
    /* 플로팅 버튼 실제 모양 */
    .floating-save-btn .stButton button {
        background-color: #6c5ce7 !important;
        color: white !important;
        border-radius: 50px !important;
        width: 60px !important;
        height: 60px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
        border: none !important;
        font-size: 24px !important;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 !important;
    }
    .floating-save-btn .stButton button:hover {
        transform: scale(1.1);
        background-color: #5f4dd0 !important;
    }
    
    /* 입력창 배경 투명 */
    .stTextInput input { background-color: transparent !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. 사이드바 (HTML 감성 리스트) ---
with st.sidebar:
    st.title("📅 Romi's History")
    if st.button("➕ 새 주간 시작하기", use_container_width=True, type="primary"):
        st.session_state.current_data = None 
        st.rerun()
    
    st.markdown("---") # 구분선
    
    # 리스트 출력 (HTML처럼 깔끔한 한 줄)
    for i, item in enumerate(st.session_state.history):
        # 테두리 없는 깔끔한 레이아웃
        c1, c2, c3 = st.columns([0.15, 0.7, 0.15])
        
        with c1: # 삭제 (X)
            st.markdown('<div class="icon-btn delete-btn">', unsafe_allow_html=True)
            if st.button("✕", key=f"del_{i}", help="삭제"):
                del st.session_state.history[i]
                save_data(st.session_state.history)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c2: # 제목 (클릭 시 로드)
            if st.button(f"{item['title']}", key=f"load_{i}"):
                st.session_state.current_data = item
                st.rerun()
                
        with c3: # 복사 (아이콘)
            st.markdown('<div class="icon-btn copy-btn">', unsafe_allow_html=True)
            if st.button("📋", key=f"copy_{i}", help="복사"):
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
        
        # 항목 사이 얇은 구분선
        st.markdown("<hr style='margin: 0.2rem 0; opacity: 0.3;'>", unsafe_allow_html=True)


# --- 6. 메인 화면 ---
if "current_data" not in st.session_state or st.session_state.current_data is None:
    today_str = f"{datetime.date.today().month}월 {datetime.date.today().day}일 시작 주간"
    st.session_state.current_data = {
        "id": str(datetime.datetime.now().timestamp()),
        "title": today_str, "goal": "",
        "content": {day: {"weight": "", "bf": "", "lc": "", "sn": "", "dn": "", "eval": None} for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
    }
data = st.session_state.current_data
days_info = [("Mon", "월요일", "🐻"), ("Tue", "화요일", "🔥"), ("Wed", "수요일", "🥗"), ("Thu", "목요일", "🥩"), ("Fri", "금요일", "🍷"), ("Sat", "토요일", "🛍️"), ("Sun", "일요일", "🛁")]

st.title("🏃‍♀️ 로미의 유지어터 매니저")
new_title = st.text_input("날짜/제목", value=data['title'])
data['title'] = new_title
data['goal'] = st.text_input("이번 주 목표", value=data['goal'], placeholder="예: 평일 저녁 쉐이크, 물 2L 마시기")
st.divider()

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
        day_data['eval'] = st.segmented_control("평가", ["😍", "🙂", "😅"], selection_mode="single", default=day_data['eval'] if day_data['eval'] in ["😍", "🙂", "😅"] else None, key=f"e_{day_code}", label_visibility="collapsed")
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
        day_data['eval'] = st.segmented_control("평가", ["😍", "🙂", "😅"], selection_mode="single", default=day_data['eval'] if day_data['eval'] in ["😍", "🙂", "😅"] else None, key=f"e_{day_code}", label_visibility="collapsed")
st.divider()

# --- [대망의 플로팅 저장 버튼] ---
# 화면 맨 아래 우측에 '💾' 아이콘만 떠있는 버튼!
st.markdown('<div class="floating-save-btn">', unsafe_allow_html=True)
if st.button("💾", type="primary", help="저장하기"):
    existing_ids = [item['id'] for item in st.session_state.history]
    if data['id'] in existing_ids:
        index = existing_ids.index(data['id'])
        st.session_state.history[index] = data
    else:
        st.session_state.history.insert(0, data)
    
    save_data(st.session_state.history)
    st.toast("저장 완료! 🎉", icon="🔥") # 토스트 메시지로 가볍게 알림
    time.sleep(1)
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
