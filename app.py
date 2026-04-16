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

st.title("土地家屋調査士 業務管理システム")

# --- 2. データの準備（顧客リストと業務リスト） ---
# 顧客一覧を取得（名前を選択肢に出すため）
clients_res = supabase.table("clients").select("id, name").execute()
clients_data = clients_res.data
# 選択肢用の辞書を作成 { "佐藤 豪": 1, "田中 太郎": 2 }
client_options = {c["name"]: c["id"] for c in clients_data}

# 業務一覧を取得（顧客名も一緒に持ってくる）
tasks_res = supabase.table("tasks").select("*, clients(name)").execute()
tasks_data = tasks_res.data

# --- 3. 新規案件の登録フォーム（サイドバー） ---
st.sidebar.header("➕ 新規案件の登録")
with st.sidebar.form("new_task_form"):
    # 顧客名をリストから選択
    selected_client_name = st.selectbox("顧客名を選択", options=list(client_options.keys()))
    task_type = st.text_input("業務内容", placeholder="例: 滅失登記")
    due_date = st.date_input("期日")
    
    submit_btn = st.form_submit_button("予定を登録する")

    if submit_btn:
        new_task = {
            "client_id": client_options[selected_client_name], # 選んだ名前からIDに変換
            "task_type": task_type,
            "due_date": str(due_date),
            "statas": "未着手"
        }
        supabase.table("tasks").insert(new_task).execute()
        st.sidebar.success(f"{selected_client_name}様の案件を登録しました！")
        st.rerun() # 画面を更新してカレンダーに反映

# --- 4. カレンダー表示 ---
from streamlit_calendar import calendar

events = []
for task in tasks_data:
    if task.get("due_date"):
        # 顧客名を取得（紐付けがない場合は「不明」）
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
cal_result = calendar(events=events, options=calendar_options)

# --- 5. クリック詳細表示 ---
if cal_result.get("eventClick"):
    event = cal_result["eventClick"]["event"]
    st.write("---")
    st.subheader("📋 案件詳細")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**顧客名:** {event['extendedProps']['client']} 様")
        st.info(f"**内容:** {event['title'].split('/')[-1]}") # タイトルから業務名だけ抽出
    with col2:
        st.warning(f"**期日:** {event['start']}")
        st.success(f"**ステータス:** {event['extendedProps']['status']}")
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
# --- 予定追加フォーム（サイドバー） ---
st.sidebar.header("➕ 新規案件の登録")

with st.sidebar.form("new_task_form"):
    # フォームの入力項目
    task_type = st.text_input("業務内容 (例: 滅失登記, 表題登記)")
    due_date = st.date_input("期日")
    
    # 登録ボタン
    submit_btn = st.form_submit_button("予定を登録する")

    if submit_btn:
        # ボタンが押されたら、Supabaseにデータを送信する
        new_data = {
            "client_id": 1,  # ※今回はテストとしてID:1（佐藤様）で固定します
            "task_type": task_type,
            "due_date": str(due_date),
            "statas": "未着手"  # ※Supabaseの現在のカラム名(statas)に合わせています
        }
        
        # データベースに追加
        supabase.table("tasks").insert(new_data).execute()
        
        # 成功メッセージ
        st.sidebar.success("登録完了！画面右上の「⋮」から「Rerun」を押してカレンダーを更新してください。")
