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

# --- 4. CSS 스타일 (디자인의 핵심!) ---
st.markdown("""
<style>
    /* [전체 폰트 및 컬러 변수] */
    :root {
        --primary-purple: #6c5ce7;
        --light-purple: #f0eeff;
    }

    /* [사이드바] 너비 및 스타일 */
    section[data-testid="stSidebar"] {
        min-width: 350px !important;
        max-width: 350px !important;
    }
    
    /* 사이드바 안의 버튼들 기본 스타일 (투명하게) */
    [data-testid="stSidebar"] .stButton button {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    /* [새 주간 시작하기 버튼] - 눈에 띄게 커스텀 */
    .new-week-btn button {
        background-color: var(--primary-purple) !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 12px !important;
        font-weight: bold !important;
        width: 100% !important;
        border: 1px solid var(--primary-purple) !important;
        margin-bottom: 20px !important;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .new-week-btn button:hover {
        background-color: #5b4cc4 !important;
    }

    /* [사이드바 카드 리스트] */
    .history-card {
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 8px;
        border: 1px solid #e0e0e0;
        background-color: white;
        transition: all 0.2s;
    }
    /* 선택된(Active) 카드 스타일 - 하이라이트 */
    .history-card-active {
        border: 2px solid var(--primary-purple);
        background-color: var(--light-purple);
    }

    /* 카드 내 텍스트 스타일 */
    .card-title {
        font-size: 16px;
        font-weight: bold;
        color: #333;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: block;
    }
    .card-goal {
        font-size: 12px;
        color: #888;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: block;
        margin-top: 2px;
    }

    /* 아이콘 버튼 (복사/삭제) 스타일 */
    .icon-action-btn button {
        font-size: 18px !important;
        color: #b2bec3 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 30px !important;
        height: 30px !important;
    }
    .icon-action-btn button:hover {
        background-color: rgba(0,0,0,0.05) !important;
        border-radius: 50% !important;
        color: var(--primary-purple) !important;
    }

    /* [메인 화면] 카드 디자인 */
    section[data-testid="stMain"] div[data-testid="stColumn"] {
        background-color: var(--secondary-background-color);
        padding: 15px;
        border-radius: 15px;
        border: 1px solid rgba(128, 128, 128, 0.1);
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }

    /* [평가 버튼 중앙 정렬] */
    div[data-testid="stSegmentedControl"] {
        display: flex;
        justify-content: center !important;
    }
    /* 평가 버튼 내부 정렬 */
    div[data-testid="stSegmentedControl"] > div {
        width: 100%;
        justify-content: center;
    }

    /* [하단 저장하기 버튼 - 중앙 정렬 & 보라색] */
    .save-btn-container {
        display: flex;
        justify-content: center;
        margin-top: 30px;
        margin-bottom: 50px;
    }
    .save-btn-container .stButton button {
        background-color: var(--primary-purple) !important;
        color: white !important;
        font-size: 18px !important;
        font-weight: bold !important;
        padding: 12px 40px !important;
        border-radius: 50px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(108, 92, 231, 0.3) !important;
        transition: transform 0.1s;
    }
    .save-btn-container .stButton button:hover {
        transform: scale(1.05);
        background-color: #5b4cc4 !important;
    }
    .save-btn-container .stButton button p {
        font-size: 18px !important; /* 텍스트 크기 강제 적용 */
    }

    /* 입력창 배경 투명 */
    .stTextInput input { background-color: transparent !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. 사이드바 (HTML 감성 카드 리스트) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #6c5ce7;'>📅 Romi's History</h2>", unsafe_allow_html=True)
    st.write("")

    # [새 주간 시작하기] 버튼 (커스텀 CSS 클래스 적용)
    st.markdown('<div class="new-week-btn">', unsafe_allow_html=True)
    if st.button("➕ 새 주간 시작하기", key="new_week"):
        st.session_state.current_data = None 
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("") # 여백

    # 현재 선택된 데이터의 ID 찾기 (하이라이트용)
    current_id = st.session_state.current_data['id'] if st.session_state.get('current_data') else None

    # 리스트 출력
    for i, item in enumerate(st.session_state.history):
        is_active = (item['id'] == current_id)
        
        # 카드 컨테이너 스타일 결정 (Active vs Normal)
        container_bg = "#f0eeff" if is_active else "#ffffff"
        container_border = "2px solid #6c5ce7" if is_active else "1px solid #e0e0e0"
        
        # HTML/CSS로 카드 모양 잡기 (버튼은 Streamlit 기능 사용해야 하므로 레이아웃 트릭 사용)
        # st.container에 border=False하고 CSS로 스타일링
        with st.container():
            # 카드 전체를 감싸는 div 느낌의 레이아웃
            # Streamlit 컬럼을 사용해 [ 텍스트영역 (클릭용 버튼) | 복사 | 삭제 ] 배치
            
            # CSS로 이 특정 컨테이너를 카드처럼 보이게 만듦
            # (Streamlit 컨테이너에 직접 스타일을 입히기 어려우므로, 
            #  버튼들을 감싸는 컬럼 구조를 만듦)
            
            # 레이아웃: [ 타이틀&목표 (70%) ] [ 복사 (15%) ] [ 삭제 (15%) ]
            c_text, c_copy, c_del = st.columns([0.7, 0.15, 0.15])
            
            # 1. 텍스트 영역 (타이틀 + 목표) -> 버튼으로 만들어서 클릭 가능하게 함
            with c_text:
                # 버튼 텍스트를 "타이틀\n목표" 형태로 만듦
                btn_label = f"{item['title']}\n{item.get('goal', '')}"
                
                # 활성화 상태에 따라 버튼 스타일이 달라보이게 CSS 주입은 어렵지만
                # 왼쪽에 색상 바(Bar)를 두거나 아이콘으로 표시 가능
                # 여기서는 심플하게 버튼 클릭 시 로드
                if st.button(item['title'], key=f"load_{i}", help=item.get('goal', ''), use_container_width=True):
                    st.session_state.current_data = item
                    st.rerun()
                # 목표는 작게 밑에 표시 (버튼 밑에)
                if item.get('goal'):
                    st.caption(f"{item['goal'][:15]}..." if len(item['goal'])>15 else item['goal'])

            # 2. 복사 버튼
            with c_copy:
                st.markdown('<div class="icon-action-btn">', unsafe_allow_html=True)
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

            # 3. 삭제 버튼
            with c_del:
                st.markdown('<div class="icon-action-btn">', unsafe_allow_html=True)
                if st.button("✕", key=f"del_{i}", help="삭제"):
                    del st.session_state.history[i]
                    save_data(st.session_state.history)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            # 항목 간 구분선 (카드 느낌을 위해 Active 상태면 박스처럼 보이게 CSS 적용 필요)
            # 여기서는 심플하게 구분선으로 처리하되, Active면 왼쪽에 보라색 마커 표시
            if is_active:
                st.markdown("<div style='height: 3px; background-color: #6c5ce7; border-radius: 2px; margin-top: -5px; margin-bottom: 10px;'></div>", unsafe_allow_html=True)
            else:
                st.markdown("<hr style='margin: 5px 0; opacity: 0.2;'>", unsafe_allow_html=True)


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

# 제목 및 목표 입력
c_title, c_goal = st.columns([1, 2])
with c_title:
    new_title = st.text_input("날짜/제목", value=data['title'])
    data['title'] = new_title
with c_goal:
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
        
        # 평가 버튼 (중앙 정렬 CSS 적용됨)
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

# [저장하기 버튼]
# CSS (.save-btn-container)로 완벽 중앙 정렬 + 보라색 스타일링
st.markdown('<div class="save-btn-container">', unsafe_allow_html=True)
if st.button("💾  저장하기", key="save_main"):
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
