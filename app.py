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
