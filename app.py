import streamlit as st
import datetime
import json
import os
import time
import gspread
from google.oauth2.service_account import Credentials

# --- 1. 기본 설정 ---
st.set_page_config(layout="wide", page_title="로미의 다이어트 매니저", page_icon="📅")

# --- 2. 유틸리티 함수 ---
def get_weekly_title():
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    weekdays = ["(월)", "(화)", "(수)", "(목)", "(금)", "(토)", "(일)"]
    start_str = f"{start_of_week.strftime('%Y-%m-%d')}{weekdays[start_of_week.weekday()]}"
    end_str = f"{end_of_week.strftime('%Y-%m-%d')}{weekdays[end_of_week.weekday()]}"
    return f"{start_str} ~ {end_str}"

@st.cache_resource
def get_google_sheet():
    try:
        key_dict = st.secrets["service_account"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open("diet_db")
        return sh.sheet1
    except Exception:
        st.error("🚨 연결 실패. Secrets 설정을 확인해주세요.")
        return None

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
    except:
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

# --- 3. CSS 스타일 (박스 제거 & 정렬 완벽화) ---
st.markdown("""
<style>
    :root { --primary: #6c5ce7; }
    
    /* 사이드바 너비 고정 */
    section[data-testid="stSidebar"] { min-width: 350px !important; max-width: 350px !important; }

    /* [새 주간 시작하기 버튼] */
    div.new-week-wrapper {
        display: flex;
        justify-content: center;
        width: 100%;
        margin-bottom: 20px;
    }
    div.new-week-wrapper button {
        background-color: var(--primary) !important;
        color: white !important;
        border: 2px solid #4834d4 !important;
        border-radius: 12px !important;
        width: 95% !important;
        padding: 0.8rem 0 !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    div.new-week-wrapper button:hover {
        background-color: #5b4cc4 !important;
        transform: translateY(-2px);
    }

    /* [타이틀 버튼] - 투명화, 좌측 정렬, 테두리 없음 */
    .invisible-btn button {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        color: #333 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        width: 100% !important;
        font-size: 15px !important;
    }
    .invisible-btn button:hover {
        color: var(--primary) !important;
    }
    .invisible-btn button p {
        text-align: left !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* [더보기(Popover) 버튼] - V 아이콘 제거 & 투명화 */
    [data-testid="stPopover"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    [data-testid="stPopover"] > button {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
        color: #333 !important;
        width: auto !important;
    }
    
    /* [핵심] V자 화살표(chevron) 숨기기 */
    [data-testid="stPopover"] > button span[data-testid="stIcon"] {
        display: none !important;
    }
    
    /* 호버 시 배경만 살짝 */
    [data-testid="stPopover"] > button:hover {
        background-color: rgba(0,0,0,0.05) !important;
        border-radius: 50% !important;
        color: var(--primary) !important;
    }

    /* 팝오버 내부 메뉴 */
    div[data-testid="stPopoverBody"] button {
        border: none !important;
        background: transparent !important;
        text-align: left !important;
        justify-content: flex-start !important;
        width: 100% !important;
    }
    div[data-testid="stPopoverBody"] button:hover {
        background-color: #f0eeff !important;
        color: var(--primary) !important;
    }

    /* 메인 화면 스타일 */
    section[data-testid="stMain"] div[data-testid="stColumn"] {
        background-color: var(--secondary-background-color); padding: 15px; border-radius: 15px; border: 1px solid rgba(128, 128, 128, 0.1); box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    div[data-testid="stSegmentedControl"] { display: flex; justify-content: center !important; }
    div[data-testid="stSegmentedControl"] > div { width: 100%; justify-content: center; }
    
    .save-btn-wrapper { display: flex; justify-content: center; margin-top: 30px; margin-bottom: 50px; }
    .save-btn-wrapper .stButton button {
        background-color: var(--primary) !important; color: white !important; font-size: 18px !important; font-weight: bold !important; padding: 12px 40px !important; border-radius: 50px !important; border: none !important; box-shadow: 0 4px 15px rgba(108, 92, 231, 0.3) !important;
    }
    .stTextInput input { background-color: transparent !important; }
</style>
""", unsafe_allow_html=True)

# --- 4. 사이드바 UI ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #6c5ce7;'>📅 Romi's History</h2>", unsafe_allow_html=True)
    st.write("")

    # [새 주간 시작하기]
    st.markdown('<div class="new-week-wrapper">', unsafe_allow_html=True)
    if st.button("➕  새 주간 시작하기", key="new_week"):
        new_data = {
            "id": str(datetime.datetime.now().timestamp()), 
            "title": get_weekly_title(),
            "goal": "",
            "content": {day: {"weight": "", "bf": "", "lc": "", "sn": "", "dn": "", "eval": None} for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
        }
        st.session_state.history.insert(0, new_data)
        st.session_state.current_data = new_data
        save_data(st.session_state.history)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("") 

    current_id = st.session_state.current_data['id'] if st.session_state.get('current_data') else None

    # [리스트 출력]
    for i, item in enumerate(st.session_state.history):
        is_active = (item['id'] == current_id)
        
        # 선택된 항목 하이라이트 (테두리 + 배경)
        if is_active:
            st.markdown(
                """
                <style>
                div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
                    border: 2px solid #6c5ce7 !important;
                    background-color: #f3f0ff !important;
                }
                </style>
                """, 
                unsafe_allow_html=True
            )

        # 큰 박스 (Container)
        with st.container(border=True):
            # [중요] 9:1 비율 + 수직 중앙 정렬 (vertical_alignment="center")
            c_title, c_more = st.columns([0.9, 0.1], vertical_alignment="center")
            
            # 1. 좌측: 날짜 타이틀 (테두리 없는 버튼)
            with c_title:
                st.markdown('<div class="invisible-btn">', unsafe_allow_html=True)
                if st.button(item['title'], key=f"load_{i}", help="불러오기"):
                    st.session_state.current_data = item
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # 2. 우측: 더보기 (점 3개 아이콘)
            with c_more:
                # :material/more_vert: 아이콘 사용, 라벨 없음 -> V 아이콘은 CSS로 숨김
                popover = st.popover(":material/more_vert:", help=None)
                with popover:
                    if st.button("📋 복사하기", key=f"copy_{i}"):
                        new_item = item.copy()
                        new_item['id'] = str(datetime.datetime.now().timestamp())
                        new_item['title'] = get_weekly_title() + " (복사됨)"
                        # 내용 초기화
                        for day in new_item['content']:
                            new_item['content'][day]['weight'] = ""
                            new_item['content'][day]['eval'] = None
                        st.session_state.history.insert(0, new_item)
                        save_data(st.session_state.history)
                        st.session_state.current_data = new_item
                        st.rerun()
                    
                    if st.button("🗑️ 삭제하기", key=f"del_{i}"):
                        del st.session_state.history[i]
                        if is_active:
                            st.session_state.current_data = None
                        save_data(st.session_state.history)
                        st.rerun()

# --- 5. 메인 UI ---
if "current_data" not in st.session_state or st.session_state.current_data is None:
    st.info("👈 왼쪽 사이드바에서 '+ 새 주간 시작하기'를 눌러주세요!")
    st.stop()

data = st.session_state.current_data
current_week_id = data['id'] 

days_info = [("Mon", "월요일", "🐻"), ("Tue", "화요일", "🔥"), ("Wed", "수요일", "🥗"), ("Thu", "목요일", "🥩"), ("Fri", "금요일", "🍷"), ("Sat", "토요일", "🛍️"), ("Sun", "일요일", "🛁")]

st.title("🏃‍♀️ 로미의 유지어터 매니저")
st.markdown(f"<h3 style='text-align: left;'>📅 {data['title']}</h3>", unsafe_allow_html=True)

data['goal'] = st.text_input("이번 주 목표를 입력해주세요!", value=data['goal'], placeholder="예: 평일 저녁 쉐이크, 물 2L 마시기", key=f"goal_{current_week_id}")

st.divider()

cols = st.columns(4)
for idx, (day_code, label, icon) in enumerate(days_info[:4]):
    day_data = data['content'][day_code]
    with cols[idx]:
        st.subheader(f"{icon} {label}")
        day_data['weight'] = st.text_input("몸무게", value=day_data['weight'], key=f"w_{day_code}_{current_week_id}")
        day_data['bf'] = st.text_input("아침", value=day_data['bf'], key=f"b_{day_code}_{current_week_id}")
        day_data['lc'] = st.text_input("점심", value=day_data['lc'], key=f"l_{day_code}_{current_week_id}")
        day_data['sn'] = st.text_input("간식", value=day_data['sn'], key=f"s_{day_code}_{current_week_id}")
        day_data['dn'] = st.text_input("저녁", value=day_data['dn'], key=f"d_{day_code}_{current_week_id}")
        eval_val = day_data['eval']
        day_data['eval'] = st.segmented_control("평가", ["😍", "🙂", "😅"], selection_mode="single", default=eval_val if eval_val in ["😍", "🙂", "😅"] else None, key=f"e_{day_code}_{current_week_id}", label_visibility="collapsed")

st.write("")
cols_bottom = st.columns(3)
for idx, (day_code, label, icon) in enumerate(days_info[4:]):
    day_data = data['content'][day_code]
    with cols_bottom[idx]:
        st.subheader(f"{icon} {label}")
        day_data['weight'] = st.text_input("몸무게", value=day_data['weight'], key=f"w_{day_code}_{current_week_id}")
        day_data['bf'] = st.text_input("아침", value=day_data['bf'], key=f"b_{day_code}_{current_week_id}")
        day_data['lc'] = st.text_input("점심", value=day_data['lc'], key=f"l_{day_code}_{current_week_id}")
        day_data['sn'] = st.text_input("간식", value=day_data['sn'], key=f"s_{day_code}_{current_week_id}")
        day_data['dn'] = st.text_input("저녁", value=day_data['dn'], key=f"d_{day_code}_{current_week_id}")
        eval_val = day_data['eval']
        day_data['eval'] = st.segmented_control("평가", ["😍", "🙂", "😅"], selection_mode="single", default=eval_val if eval_val in ["😍", "🙂", "😅"] else None, key=f"e_{day_code}_{current_week_id}", label_visibility="collapsed")

st.divider()

st.markdown('<div class="save-btn-wrapper">', unsafe_allow_html=True)
if st.button("💾  저장하기", key="save_main"):
    existing_ids = [item['id'] for item in st.session_state.history]
    if data['id'] in existing_ids:
        index = existing_ids.index(data['id'])
        st.session_state.history[index] = data
    save_data(st.session_state.history)
    st.success("저장 완료! 로미님 오늘도 파이팅! 🔥")
    time.sleep(1)
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
