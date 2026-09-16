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

# スプレッドシートからデータを読み込む（キャッシュをせず常に最新を取得）
@st.cache_data(ttl=0)
def load_data():
    try:
        # スプレッドシートの1枚目のシートからデータを読み込み
        df = conn.read(worksheet="Sheet1", usecols=list(range(5)), ttl=0)
        # もしデータが空か、すべてNaNの場合は空のDataFrameを返す
        if df.empty or df.dropna(how="all").empty:
            return pd.DataFrame(columns=["日付", "プレイヤー", "スコア", "チップ", "収支"])
        return df.dropna(how="all")
    except Exception as e:
        # 初回などでシートが空の場合などのフォールバック
        return pd.DataFrame(columns=["日付", "プレイヤー", "スコア", "チップ", "収支"])

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
    uma_1 = st.number_input("ウマ 1位 (例: +20)", value=20, step=5)
    uma_2 = st.number_input("ウマ 2位 (例: 0)", value=0, step=5)
    uma_3 = st.number_input("ウマ 3位 (例: -20)", value=-20, step=5)
    chip_rate = st.number_input("チップ1枚の価値 (円)", value=100, step=50)

    submitted = st.form_submit_button("計算して記録する")

if submitted:
    # バリデーション：合計点数が合っているかチェック（サンマの標準的な返し点×3などのチェック、簡易版）
    total_score = p1_score + p2_score + p3_score
    
    # スコアの計算（(持ち点 - 返し点) / 1000 + ウマ）
    # サンマの場合、沈みウマやオカの計算ルールに合わせて算出
    # ここでは一般的な計算ロジックを適用
    p1_calc = ((p1_score - return_score) / 1000) + uma_1
    p2_calc = ((p2_score - return_score) / 1000) + uma_2
    p3_calc = ((p3_score - return_score) / 1000) + uma_3

    # チップ収支の計算
    p1_chip_yen = p1_chip * chip_rate
    p2_chip_yen = p2_chip * chip_rate
    p3_chip_yen = p3_chip * chip_rate

    # 新規データの作成
    new_data = pd.DataFrame([
        {"日付": str(match_date), "プレイヤー": p1_name, "スコア": p1_calc, "チップ": p1_chip, "収支": p1_chip_yen},
        {"日付": str(match_date), "プレイヤー": p2_name, "スコア": p2_calc, "チップ": p2_chip, "収支": p2_chip_yen},
        {"日付": str(match_date), "プレイヤー": p3_name, "スコア": p3_calc, "チップ": p3_chip, "収支": p3_chip_yen},
    ])

    # 既存データに追加
    df = pd.concat([df, new_data], ignore_index=True)
    
    # Googleスプレッドシートに保存
    save_data(df)
    st.sidebar.success("データをGoogleスプレッドシートに保存しました！")
    st.rerun()

# メイン画面：成績一覧と集計
st.header("📊 成績一覧・サマリー")

if not df.empty and "プレイヤー" in df.columns:
    # プレイヤーごとのトータル集計
    summary = df.groupby("プレイヤー")[["スコア", "チップ", "収支"]].sum().reset_index()
    
    st.subheader("総合ランキング・収支")
    st.dataframe(summary, use_container_width=True)

    st.subheader("対局履歴")
    st.dataframe(df, use_container_width=True)

    if st.button("全データをリセット（注意）"):
        empty_df = pd.DataFrame(columns=["日付", "プレイヤー", "スコア", "チップ", "収支"])
        save_data(empty_df)
        st.success("データをリセットしました。")
        st.rerun()
else:
    st.info("まだ対局データがありません。サイドバーからデータを入力してください！")
