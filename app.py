import streamlit as st
import datetime
import json
import time
import gspread
from google.oauth2.service_account import Credentials

# --- 1. 기본 설정 ---
st.set_page_config(layout="wide", page_title="로미의 다이어트 매니저", page_icon="📅")

# --- 2. 구글 시트 연결 함수 (Secrets 사용) ---
# 이 함수는 캐시를 사용해서 매번 로그인하지 않게 함
@st.cache_resource
def get_google_sheet():
    # Streamlit Secrets에서 열쇠 정보 가져오기
    key_dict = st.secrets["service_account"]
    
    # 구글 인증 범위 설정
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 시트 열기 (시트 이름이 'diet_db'인지 꼭 확인!)
    sh = client.open("diet_db")
    return sh.sheet1

# --- 3. 데이터 불러오기/저장하기 (구글 시트용) ---
def load_data():
    try:
        sheet = get_google_sheet()
        # 시트의 모든 데이터를 가져옴 (A열에 JSON 문자열로 저장할 예정)
        raw_data = sheet.col_values(1) # 1번째 컬럼(A열) 데이터 읽기
        
        history = []
        for item in raw_data:
            if item.strip(): # 빈 줄이 아니면
                history.append(json.loads(item)) # JSON 문자열을 딕셔너리로 변환
        return history
    except Exception as e:
        st.error(f"데이터 불러오기 실패: {e}")
        return []

def save_data(data):
    try:
        sheet = get_google_sheet()
        sheet.clear() # 기존 데이터 싹 지우고
        
        # 데이터를 JSON 문자열 리스트로 변환 (한 줄에 하나씩)
        # gspread는 2차원 리스트([[행1], [행2]])를 원함
        rows = [[json.dumps(item, ensure_ascii=False)] for item in data]
        
        if rows:
            sheet.update(range_name='A1', values=rows)
    except Exception as e:
        st.error(f"데이터 저장 실패: {e}")

# 초기 데이터 로드 (세션 상태에 없으면 구글 시트에서 가져옴)
if "history" not in st.session_state:
    st.session_state.history = load_data()

# --- 4. CSS 스타일 (디자인 유지) ---
st.markdown("""
<style>
    section[data-testid="stSidebar"] { min-width: 350px !important; max-width: 350px !important; }
    section[data-testid="stMain"] div[data-testid="stColumn"] {
        background-color: var(--secondary-background-color); padding: 15px; border-radius: 10px; border: 1px solid rgba(128, 128, 128, 0.2);
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] [data-testid="stContainer"] { padding: 0.5rem 0.2rem !important; gap: 0 !important; }
    [data-testid="stSidebar"] [data-testid="stContainer"] [data-testid="column"] { padding: 0 !important; }
    [data-testid="stSidebar"] .stButton button {
        background-color: transparent !important; border: none !important; color: inherit !important; padding: 0px !important; height: 2.5rem !important;
        display: flex; align-items: center; justify-content: center;
    }
    [data-testid="stSidebar"] .stButton button p {
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 160px; font-weight: normal; font-size: 14px; text-align: left; margin-bottom: 0px;
    }
    .delete-btn button { color: #ff7675 !important; font-weight: bold !important; font-size: 1.2rem !important; }
    .copy-btn button span { font-size: 1.2rem !important; color: #74b9ff !important; }
    .save-button-container { display: flex; justify-content: center; align-items: center; width: 100%; margin-top: 20px; }
    .save-button-container .stButton > button { width: 300px !important; border-radius: 50px; font-weight: bold; padding: 10px 20px; }
    .stTextInput input { background-color: transparent !important; }
</style>
""", unsafe_allow_html=True)

# --- 5. 사이드바 ---
with st.sidebar:
    st.title("📅 Romi's History")
    if st.button("➕ 새 주간 시작하기", use_container_width=True, type="primary"):
        st.session_state.current_data = None 
        st.rerun()
    st.write("")
    for i, item in enumerate(st.session_state.history):
        with st.container(border=True):
            col1, col2, col3 = st.columns([0.15, 0.7, 0.15])
            with col1:
                st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                if st.button(":material/close:", key=f"del_{i}", help="삭제"):
                    del st.session_state.history[i]
                    save_data(st.session_state.history) # 구글 시트에 저장
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                st.markdown("""<style>div[data-testid="stVerticalBlock"] > div:nth-child(2) .stButton button { justify-content: flex-start !important; }</style>""", unsafe_allow_html=True)
                if st.button(f"{item['title']}", key=f"load_{i}"):
                    st.session_state.current_data = item
                    st.rerun()
            with col3:
                st.markdown('<div class="copy-btn">', unsafe_allow_html=True)
                if st.button(":material/content_copy:", key=f"copy_{i}", help="복사"):
                    new_item = item.copy()
                    new_item['id'] = str(datetime.datetime.now().timestamp())
                    new_item['title'] = f"{datetime.date.today().month}월 {datetime.date.today().day}일 시작 (복사됨)"
                    for day in new_item['content']:
                        new_item['content'][day]['weight'] = ""
                        new_item['content'][day]['eval'] = None
                    st.session_state.history.insert(0, new_item)
                    save_data(st.session_state.history) # 구글 시트에 저장
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

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

st.markdown('<div class="save-button-container">', unsafe_allow_html=True)
if st.button("💾 저장하기", type="primary"):
    existing_ids = [item['id'] for item in st.session_state.history]
    if data['id'] in existing_ids:
        index = existing_ids.index(data['id'])
        st.session_state.history[index] = data
    else:
        st.session_state.history.insert(0, data)
    
    save_data(st.session_state.history) # 구글 시트에 저장
    st.success("저장 완료! 로미님 오늘도 파이팅! 🔥")
    time.sleep(1)
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
