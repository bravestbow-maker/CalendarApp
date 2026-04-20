import streamlit as st
from supabase import create_client
from streamlit_calendar import calendar

# --- お父様仕様：徹底的なUIのノイズ除去 ---
st.set_page_config(page_title="土地家屋調査士 業務管理", layout="wide")
st.markdown("""
    <style>
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {padding-top: 1rem;}
        /* タブのフォントをスマートに */
        .stTabs [data-baseweb="tab-list"] {gap: 24px;}
        .stTabs [data-baseweb="tab"] {height: 50px; font-weight: 600;}
    </style>
""", unsafe_allow_html=True)

# --- 1. 接続設定 ---
@st.cache_resource
def init_connection():
    url = st.secrets["connections"]["supabase"]["url"]
    key = st.secrets["connections"]["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

# --- 2. データ取得関数（効率化のため関数化） ---
def get_all_data():
    clients = supabase.table("clients").select("id, name, address").execute().data
    tasks = supabase.table("tasks").select("*, clients(name)").execute().data
    return clients, tasks

clients, tasks = get_all_data()

# --- 3. メイン画面：タブによる機能分離 ---
tab1, tab2, tab3 = st.tabs(["🗓 業務スケジュール", "👤 顧客カルテ登録", "📈 案件管理・分析"])

# --- タブ1：業務スケジュール（部下も確認する画面） ---
with tab1:
    st.subheader("全体スケジュール")
    events = []
    for task in tasks:
        if task.get("due_date"):
            c_name = task["clients"]["name"] if task.get("clients") else "不明"
            events.append({
                "title": f"{c_name}様 / {task['task_type']}",
                "start": task["due_date"],
                "extendedProps": {"status": task.get("statas"), "client": c_name}
            })
    
    cal_options = {
        "headerToolbar": {"left": "today prev,next", "center": "title", "right": "dayGridMonth,timeGridWeek"},
        "initialView": "dayGridMonth",
    }
    cal_result = calendar(events=events, options=cal_options, key="biz_calendar")
    
    if cal_result.get("eventClick"):
        event = cal_result["eventClick"]["event"]
        st.info(f"**詳細:** {event['extendedProps']['client']}様 - {event['title']}（状態: {event['extendedProps']['status']}）")

# --- タブ2：顧客・案件登録（情報を蓄積する画面） ---
with tab2:
    st.subheader("新規登録・情報蓄積")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write("▼ 新規顧客の登録")
        with st.form("client_form"):
            c_name = st.text_input("顧客氏名")
            c_address = st.text_input("住所/現場所在地")
            if st.form_submit_button("顧客をDBに保存"):
                supabase.table("clients").insert({"name": c_name, "address": c_address}).execute()
                st.success("顧客情報を蓄積しました。")
                st.rerun()

    with col_b:
        st.write("▼ 案件（タスク）の割り当て")
        with st.form("task_form"):
            client_options = {c["name"]: c["id"] for c in clients}
            target_client = st.selectbox("顧客を選択", options=list(client_options.keys()))
            t_type = st.text_input("業務内容", placeholder="滅失登記 など")
            t_date = st.date_input("期日")
            if st.form_submit_button("スケジュールに反映"):
                supabase.table("tasks").insert({
                    "client_id": client_options[target_client],
                    "task_type": t_type,
                    "due_date": str(t_date),
                    "statas": "未着手"
                }).execute()
                st.success("案件を登録しました。")
                st.rerun()

# --- タブ3：案件分析（効率化のための統計） ---
with tab3:
    st.subheader("業務効率の確認")
    if tasks:
        # 簡易的な表形式での一覧表示
        import pandas as pd
        df = pd.DataFrame(tasks)
        st.table(df[['task_type', 'due_date', 'statas']])
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
        st.success(f"**ステータス:** {event['extendedProps']['status']}")
