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

# --- 2. データ取得関数 ---
def get_all_data():
    clients_res = supabase.table("clients").select("id, name, address").execute()
    tasks_res = supabase.table("tasks").select("*, clients(name)").execute()
    return clients_res.data, tasks_res.data

# 変数名を統一（エラー回避）
clients_data, tasks_data = get_all_data()

# --- 3. メイン画面：タブによる機能分離 ---
tab1, tab2, tab3 = st.tabs(["🗓 業務スケジュール", "👤 顧客・案件登録", "📈 案件リスト・分析"])

# --- タブ1：業務スケジュール（部下も確認する画面） ---
with tab1:
    st.subheader("全体スケジュール")
    events = []
    if tasks_data:
        for task in tasks_data:
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
        st.info(f"**詳細:** {event['extendedProps']['client']}様 - {event['title'].split('/')[-1]} （状態: {event['extendedProps']['status']}）")

# --- タブ2：顧客・案件登録（情報を蓄積する画面） ---
with tab2:
    st.subheader("新規登録・情報蓄積")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write("▼ 新規顧客の登録（カルテ作成）")
        with st.form("client_form"):
            c_name = st.text_input("顧客氏名")
            c_address = st.text_input("住所/現場所在地")
            if st.form_submit_button("顧客をDBに保存"):
                if c_name:
                    supabase.table("clients").insert({"name": c_name, "address": c_address}).execute()
                    st.success("顧客情報を蓄積しました。")
                    st.rerun()
                else:
                    st.error("氏名を入力してください。")

    with col_b:
        st.write("▼ 新規案件の割り当て")
        with st.form("task_form"):
            if clients_data:
                client_options = {c["name"]: c["id"] for c in clients_data}
                target_client = st.selectbox("顧客を選択", options=list(client_options.keys()))
                t_type = st.text_input("業務内容", placeholder="例: 滅失登記")
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
            else:
                st.warning("先に左側のフォームで顧客を登録してください。")
                st.form_submit_button("スケジュールに反映", disabled=True)

# --- タブ3：案件分析（効率化のためのリスト） ---
with tab3:
    st.subheader("現在の案件一覧")
    if tasks_data:
        import pandas as pd
        df = pd.DataFrame(tasks_data)
        # 必要な列だけを綺麗に表示
        cols = [c for c in ['task_type', 'due_date', 'statas'] if c in df.columns]
        if cols:
            st.dataframe(df[cols], use_container_width=True)
