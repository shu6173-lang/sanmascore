import streamlit as st
import pandas as pd
from st_gsheets_connection import GSheetsConnection

# ページの設定
st.set_page_config(
    page_title="サンマ（3人麻雀）スコア＆チップ計算",
    page_icon="🀄",
    layout="centered"
)

# Google Sheets Connection の初期化
conn = st.connection("gsheets", type=GSheetsConnection)

# スプレッドシートからデータを読み込む（A〜K列の11列）
@st.cache_data(ttl=0)
def load_data():
    try:
        df = conn.read(worksheet="Sheet1", usecols=list(range(11)), ttl=0)
        columns = ["日付", "半荘", "P1名", "P1_Pt", "P1_チップ", "P2名", "P2_Pt", "P2_チップ", "P3名", "P3_Pt", "P3_チップ"]
        if df.empty or df.dropna(how="all").empty:
            return pd.DataFrame(columns=columns)
        # 列名がズレないように整える
        df.columns = columns[:len(df.columns)]
        return df.dropna(how="all")
    except Exception as e:
        columns = ["日付", "半荘", "P1名", "P1_Pt", "P1_チップ", "P2名", "P2_Pt", "P2_チップ", "P3名", "P3_Pt", "P3_チップ"]
        return pd.DataFrame(columns=columns)

# データの保存関数
def save_data(df):
    conn.update(worksheet="Sheet1", data=df)

# アプリのタイトル
st.title("🀄 サンマ（3人麻雀）スコア＆チップ計算")

# データのロード
df = load_data()

# サイドバー：対局結果の入力
st.sidebar.header("📝 対局結果の入力")

with st.sidebar.form("score_form"):
    match_date = st.date_input("対局日")
    match_count = st.text_input("半荘（例: 1回戦）", "1回戦")
    
    # 3人分のプレイヤー名とスコア・チップの入力
    st.subheader("プレイヤー1")
    p1_name = st.text_input("名前 (1)", "プレイヤーA")
    p1_score = st.number_input("持ち点 (1)", value=35000, step=1000)
    p1_chip = st.number_input("チップ数 (1)", value=0, step=1)

    st.subheader("プレイヤー2")
    p2_name = st.text_input("名前 (2)", "プレイヤーB")
    p2_score = st.number_input("持ち点 (2)", value=35000, step=1000)
    p2_chip = st.number_input("チップ数 (2)", value=0, step=1)

    st.subheader("プレイヤー3")
    p3_name = st.text_input("名前 (3)", "プレイヤーC")
    p3_score = st.number_input("持ち点 (3)", value=30000, step=1000)
    p3_chip = st.number_input("チップ数 (3)", value=0, step=1)

    # 設定（レートやウマなど）
    st.subheader("⚙️ ルール設定")
    return_score = st.number_input("返し点（基準点）", value=40000, step=1000)
    uma_1 = st.number_input("ウマ 1位", value=20, step=5)
    uma_2 = st.number_input("ウマ 2位", value=0, step=5)
    uma_3 = st.number_input("ウマ 3位", value=-20, step=5)

    submitted = st.form_submit_button("計算して記録する")

if submitted:
    # スコアの計算（(持ち点 - 返し点) / 1000 + ウマ）
    p1_pt = ((p1_score - return_score) / 1000) + uma_1
    p2_pt = ((p2_score - return_score) / 1000) + uma_2
    p3_pt = ((p3_score - return_score) / 1000) + uma_3

    # 1行分のデータを作成
    new_row = pd.DataFrame([{
        "日付": str(match_date),
        "半荘": match_count,
        "P1名": p1_name, "P1_Pt": p1_pt, "P1_チップ": p1_chip,
        "P2名": p2_name, "P2_Pt": p2_pt, "P2_チップ": p2_chip,
        "P3名": p3_name, "P3_Pt": p3_pt, "P3_チップ": p3_チップ,
    }])

    # 既存データに追加して保存
    df = pd.concat([df, new_row], ignore_index=True)
    save_data(df)
    
    st.sidebar.success("スプレッドシートに保存しました！")
    st.rerun()

# メイン画面：成績一覧
st.header("📊 対局履歴一覧")

if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    if st.button("全データをリセット（注意）"):
        columns = ["日付", "半荘", "P1名", "P1_Pt", "P1_チップ", "P2名", "P2_Pt", "P2_チップ", "P3名", "P3_Pt", "P3_チップ"]
        empty_df = pd.DataFrame(columns=columns)
        save_data(empty_df)
        st.success("データをリセットしました。")
        st.rerun()
else:
    st.info("まだ対局データがありません。サイドバーからデータを入力してください！")
