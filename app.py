import streamlit as st
import datetime
import json
import os
import time
import gspread
from google.oauth2.service_account import Credentials

# --- 1. 기본 설정 ---
st.set_page_config(layout="wide", page_title="로미의 다이어트 매니저", page_icon="📅")

# --- 2. [NEW] 날짜 자동 계산 함수 ---
def get_weekly_title():
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    weekdays = ["(월)", "(화)", "(수)", "(목)", "(금)", "(토)", "(일)"]
    start_str = f"{start_of_week.strftime('%Y-%m-%d')}{weekdays[start_of_week.weekday()]}"
    end_str = f"{end_of_week.strftime('%Y-%m-%d')}{weekdays[end_of_week.weekday()]}"
    return f"{start_str} ~ {end_str}"

# --- 3. 구글 시트 연결 함수 ---
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

# --- 4. 데이터 함수 ---
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

# --- 5. CSS 스타일 ---
st.markdown("""
<style>
    :root { --primary-purple: #6c5ce7; }
    
    /* 사이드바 너비 고정 */
    section[data-testid="stSidebar"] { min-width: 350px !important; max-width: 350px !important; }

    /* [새 주간 시작하기 버튼 꾸미기] */
    /* div.new-week-btn 안에 있는 버튼을 타겟팅 */
    div.new-week-btn button {
        background-color: var(--primary-purple) !important;
        color: white !important;
        border: 1px solid white !important;
        border-radius: 10px !important;
        padding: 15px 10px !important;
        font-size: 16px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        transition: transform 0.1s;
    }
    div.new-week-btn button:hover {
        transform: scale(1.02);
        background-color: #5b4cc4 !important;
    }
    div.new-week-btn button p {
        font-size: 16px !important;
    }

    /* 사이드바 안의 일반 버튼들 초기화 */
    [data-testid="stSidebar"] .stButton:not(.new-week-btn button) button {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    /* 타이틀 버튼 스타일 */
    .title-btn button {
        text-align: left !important;
        font-weight: bold !important;
        font-size: 16px !important;
        color: #333 !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: block;
        width: 100%;
    }
    .title-btn button:hover { color: var(--primary-purple) !important; }

    /* 아이콘 버튼 스타일 */
    .icon-action-btn button {
        font-size: 18px !important; color: #b2bec3 !important; display: flex; align-items: center; justify-content: center; width: 30px !important; height: 30px !important;
    }
    .icon-action-btn button:hover { background-color: rgba(0,0,0,0.05) !important; border-radius: 50% !important; color: var(--primary-purple) !important; }
    
    /* 메인 카드 스타일 */
    section[data-testid="stMain"] div[data-testid="stColumn"] {
        background-color: var(--secondary-background-color); padding: 15px; border-radius: 15px; border: 1px solid rgba(128, 128, 128, 0.1); box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    
    /* 평가/저장 버튼 정렬 */
    div[data-testid="stSegmentedControl"] { display: flex; justify-content: center !important; }
    div[data-testid="stSegmentedControl"] > div { width: 100%; justify-content: center; }
    .save-btn-container { display: flex; justify-content: center; margin-top: 30px; margin-bottom: 50px; }
    .save-btn-container .stButton button {
        background-color: var(--primary-purple) !important; color: white !important; font-size: 18px !important; font-weight: bold !important; padding: 12px 40px !important; border-radius: 50px !important; border: none !important; box-shadow: 0 4px 15px rgba(108, 92, 231, 0.3) !important;
    }
    .stTextInput input { background-color: transparent !important; }
</style>
""", unsafe_allow_html=True)

# --- 6. 사이드바 ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #6c5ce7;'>📅 Romi's History</h2>", unsafe_allow_html=True)
    st.write("")

    # [수정됨] 새 주간 시작하기 로직 변경 (누르자마자 생성 및 저장)
    st.markdown('<div class="new-week-btn">', unsafe_allow_html=True)
    if st.button("➕  새 주간 시작하기", key="new_week", use_container_width=True):
        # 1. 새로운 데이터 객체 생성
        new_data = {
            "id": str(datetime.datetime.now().timestamp()),
            "title": get_weekly_title(),
            "goal": "",
            "content": {day: {"weight": "", "bf": "", "lc": "", "sn": "", "dn": "", "eval": None} for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
        }
        # 2. 히스토리 맨 앞에 추가
        st.session_state.history.insert(0, new_data)
        # 3. 현재 보고 있는 데이터로 설정
        st.session_state.current_data = new_data
        # 4. 즉시 저장
        save_data(st.session_state.history)
        # 5. 새로고침 (즉시 사이드바에 반영됨)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("") 

    # 현재 선택된 데이터 ID (없으면 None)
    current_id = st.session_state.current_data['id'] if st.session_state.get('current_data') else None

    # 리스트 출력
    for i, item in enumerate(st.session_state.history):
        is_active = (item['id'] == current_id)
        
        # 확실한 테두리 박스 (Active 상태면 보라색 테두리)
        with st.container(border=True):
            if is_active:
                st.markdown("""<style>div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] { border-color: #6c5ce7 !important; background-color: #f0eeff !important; }</style>""", unsafe_allow_html=True)
            
            c_text, c_copy, c_del = st.columns([0.7, 0.15, 0.15])
            
            with c_text:
                st.markdown('<div class="title-btn">', unsafe_allow_html=True)
                if st.button(item['title'], key=f"load_{i}", help="이 기록 불러오기"):
                    st.session_state.current_data = item
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                if item.get('goal'):
                    st.caption(f"{item['goal'][:20]}..." if len(item['goal'])>20 else item['goal'])

            with c_copy:
                st.markdown('<div class="icon-action-btn">', unsafe_allow_html=True)
                if st.button("📋", key=f"copy_{i}", help="복사"):
                    new_item = item.copy()
                    new_item['id'] = str(datetime.datetime.now().timestamp())
                    new_item['title'] = get_weekly_title() + " (복사됨)"
                    for day in new_item['content']:
                        new_item['content'][day]['weight'] = ""
                        new_item['content'][day]['eval'] = None
                    st.session_state.history.insert(0, new_item)
                    save_data(st.session_state.history)
                    st.session_state.current_data = new_item # 복사된 항목으로 바로 이동
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            with c_del:
                st.markdown('<div class="icon-action-btn">', unsafe_allow_html=True)
                if st.button("✕", key=f"del_{i}", help="삭제"):
                    del st.session_state.history[i]
                    # 삭제 후 현재 데이터가 삭제된 데이터라면 초기화
                    if is_active:
                        st.session_state.current_data = None
                    save_data(st.session_state.history)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# --- 7. 메인 화면 ---
if "current_data" not in st.session_state or st.session_state.current_data is None:
    # 데이터가 하나도 없거나 선택 안 된 경우 -> 안내 메시지 표시
    st.info("👈 왼쪽에서 '새 주간 시작하기'를 눌러 기록을 시작해보세요!")
    st.stop() # 아래 코드 실행 안 함

data = st.session_state.current_data
days_info = [("Mon", "월요일", "🐻"), ("Tue", "화요일", "🔥"), ("Wed", "수요일", "🥗"), ("Thu", "목요일", "🥩"), ("Fri", "금요일", "🍷"), ("Sat", "토요일", "🛍️"), ("Sun", "일요일", "🛁")]

st.title("🏃‍♀️ 로미의 유지어터 매니저")
st.subheader(f"📅 {data['title']}") 
data['goal'] = st.text_input("이번 주 목표를 입력해주세요!", value=data['goal'], placeholder="예: 평일 저녁 쉐이크, 물 2L 마시기")

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
        eval_val = day_data['eval']
        day_data['eval'] = st.segmented_control("평가", ["😍", "🙂", "😅"], selection_mode="single", default=eval_val if eval_val in ["😍", "🙂", "😅"] else None, key=f"e_{day_code}", label_visibility="collapsed")

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
        day_data['eval'] = st.segmented_control("평가", ["😍", "🙂", "😅"], selection_mode="single", default=eval_val if eval_val in ["😍", "🙂", "😅"] else None, key=f"e_{day_code}", label_visibility="collapsed")

st.divider()

st.markdown('<div class="save-btn-container">', unsafe_allow_html=True)
if st.button("💾  저장하기", key="save_main"):
    # 현재 수정 중인 데이터를 히스토리에서 찾아서 업데이트
    existing_ids = [item['id'] for item in st.session_state.history]
    if data['id'] in existing_ids:
        index = existing_ids.index(data['id'])
        st.session_state.history[index] = data
    
    save_data(st.session_state.history)
    st.success("저장 완료! 로미님 오늘도 파이팅! 🔥")
    time.sleep(1)
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
