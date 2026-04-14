import streamlit as st
from supabase import create_client

def init_connection():
    url = st.secrets["connections"]["supabase"]["url"]
    key = st.secrets["connections"]["supabase"]["key"]
    return create_client(url, key)

def get_all_tasks():
    supabase = init_connection()
    # 業務種別や期日、顧客名を結合して取得する処理など
    return supabase.table("tasks").select("*, clients(name)").execute()
