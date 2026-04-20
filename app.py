import streamlit as st
from supabase import create_client

# --- デザインの最適化（無駄なUIを非表示にしてスマートに） ---
st.markdown("""
    <style>
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {padding-top: 2rem;}
    </style>
""", unsafe_allow_html=True)

# --- 1. Supabaseへの接続 ---
@st.cache_resource
def init_connection():
    url = st.secrets["connections"]["supabase"]["url"]
    key = st.secrets["connections"]["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

st.title("土地家屋調査士 業務管理")

# --- 2. データの準備（顧客リストと業務リスト） ---
clients_res = supabase.table("clients").select("id, name").execute()
clients_data = clients_res.data

if not clients_data:
    st.warning("⚠️ まずSupabaseの `clients` テーブルに顧客データを1件以上登録してください。")
    st.stop()

client_options = {c["name"]: c["id"] for c in clients_data}

tasks_res = supabase.table("tasks").select("*, clients(name)").execute()
tasks_data = tasks_res.data

# --- 3. 新規案件の登録フォーム（サイドバー） ---
st.sidebar.header("➕ 新規案件の登録")
with st.sidebar.form("new_task_form"):
    selected_client_name = st.selectbox("顧客名", options=list(client_options.keys()))
    task_type = st.text_input("業務内容", placeholder="例: 滅失登記")
    due_date = st.date_input("期日")
    submit_btn = st.form_submit_button("登録")

    if submit_btn:
        new_task = {
            "client_id": client_options[selected_client_name],
            "task_type": task_type,
            "due_date": str(due_date),
            "statas": "未着手"
        }
        supabase.table("tasks").insert(new_task).execute()
        st.sidebar.success("登録完了")
        st.rerun()

# --- 4. カレンダー表示 ---
from streamlit_calendar import calendar

events = []
if tasks_data:
    for task in tasks_data:
        if task.get("due_date"):
            c_name = task["clients"]["name"] if task.get("clients") else "不明"
            events.append({
                "title": f"{c_name}様 / {task['task_type']}",
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

st.subheader("🗓️ スケジュール")
cal_result = calendar(events=events, options=calendar_options, key="main_calendar")

# --- 5. クリック詳細表示 ---
if cal_result.get("eventClick"):
    event = cal_result["eventClick"]["event"]
    st.write("---")
    st.subheader("📋 案件詳細")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**顧客:** {event['extendedProps']['client']} 様")
        st.info(f"**内容:** {event['title'].split('/')[-1]}")
    with col2:
        st.warning(f"**期日:** {event['start']}")
        st.success(f"**ステータス:** {event['extendedProps']['status']}")        if task.get("due_date"):
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
