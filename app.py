import streamlit as st
from supabase import create_client

# --- ここから追加：無駄なUIを消し去るカスタムCSS ---
st.markdown("""
    <style>
        /* 右上のヘッダーメニュー（Deployボタンなど）を非表示 */
        header {visibility: hidden;}
        /* 一番下の「Made with Streamlit」フッターを非表示 */
        footer {visibility: hidden;}
        /* 上部の余白を削り、効率的に情報を表示 */
        .block-container {padding-top: 2rem;}
    </style>
""", unsafe_allow_html=True)
# --- ここまで追加 ---

# --- 1. Supabaseへの接続 ---
@st.cache_resource
def init_connection():    if submit_btn:
        new_task = {
            "client_id": client_options[selected_client_name],
            "task_type": task_type,
            "due_date": str(due_date),
            "statas": "未着手"
        }
        supabase.table("tasks").insert(new_task).execute()
        st.sidebar.success(f"{selected_client_name}様の案件を登録しました！")
        st.rerun()

# --- 4. カレンダー表示 ---
from streamlit_calendar import calendar

events = []
if tasks_data:
    for task in tasks_data:
        if task.get("due_date"):
            c_name = task["clients"]["name"] if task.get("clients") else "不明"
            events.append({
                "title": f"👤 {c_name}様 / {task['task_type']}",
                "start": task["due_date"],
                "extendedProps": {
                    "status": task.get("statas"),
                    "client": c_name
                }
            })

calendar_options = {
    "headerToolbar": {"left": "today prev,next", "center": "title", "right": "dayGridMonth,timeGridWeek"},
    "initialView": "dayGridMonth",
}

st.subheader("🗓️ 業務スケジュール")
# ★修正ポイント: key="main_calendar" という名札を付けて、重複エラーを完全に防ぎます
cal_result = calendar(events=events, options=calendar_options, key="main_calendar")

# --- 5. クリック詳細表示 ---
if cal_result.get("eventClick"):
    event = cal_result["eventClick"]["event"]
    st.write("---")
    st.subheader("📋 案件詳細")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**顧客名:** {event['extendedProps']['client']} 様")
        st.info(f"**内容:** {event['title'].split('/')[-1]}")
    with col2:
        st.warning(f"**期日:** {event['start']}")
        st.success(f"**ステータス:** {event['extendedProps']['status']}")
