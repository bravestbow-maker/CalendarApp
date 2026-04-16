import streamlit as st
from supabase import create_client
import os

# --- 1. Supabaseへの接続 ---
@st.cache_resource
def init_connection():
    url = st.secrets["connections"]["supabase"]["url"]
    key = st.secrets["connections"]["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

st.title("土地家屋調査士 業務管理カレンダー")

# --- 2. データの取得 ---
response = supabase.table("tasks").select("*, clients(name)").execute()
data = response.data

# --- 3. カレンダー用のデータに変換 ---
events = []
for task in data:
    # due_date（日付）が入っているデータだけをカレンダーに登録
    if task.get("due_date"): 
        # clientsが紐付いている場合は名前を取得
        client_name = task["clients"]["name"] if task.get("clients") else "顧客未定"
        
        events.append({
            "title": f"{client_name}様: {task['task_type']}",
            "start": task["due_date"],
            # クリックした時に表示したい詳細データを extendedProps に入れておく
            "extendedProps": {
                "status": task.get("statas"), # スペル注意
                "id": task["id"]
            }
        })

# --- 4. カレンダーの表示 ---
from streamlit_calendar import calendar

# カレンダーの設定
calendar_options = {
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek" # 月表示と週表示の切り替え
    },
    "initialView": "dayGridMonth",
}

# カレンダーを描画し、ユーザーの操作（クリックなど）を受け取る
calendar_result = calendar(events=events, options=calendar_options)

# --- 5. 予定をクリックした時の詳細表示 ---
st.write("---")
if calendar_result.get("eventClick"):
    # クリックされたイベントの情報を取得
    clicked_event = calendar_result["eventClick"]["event"]
    props = clicked_event["extendedProps"]
    
    st.subheader("📋 案件詳細")
    st.info(f"**内容:** {clicked_event['title']}")
    st.write(f"**期日:** {clicked_event['start']}")
    st.write(f"**ステータス:** {props['status']}")
    st.write(f"**管理ID:** {props['id']}")
else:
    st.caption("※カレンダーの予定をクリックすると、ここに詳細が表示されます。")
