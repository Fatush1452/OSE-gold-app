import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# --- 1. 設定區：圖片與參數 ---
# 請確保 logo.png 已上傳至您的 GitHub 儲存庫
LOGO_URL = "https://raw.githubusercontent.com/Fatush1452/OSE-gold-app/main/OSE.png"

st.set_page_config(page_title="黃金量化分析儀表板", layout="wide")

# --- 2. 顯示 Logo 與 標題 (比例調整為 1:3 讓 Logo 有空間放大) ---
t_col1, t_col2 = st.columns([1, 3])
with t_col1:
    try:
        # width=250 讓圖片更大，您也可以根據需求調整為 200 或 300
        st.image(LOGO_URL, width=250)
    except:
        st.write("🏮 [請檢查 Logo 連結]")
with t_col2:
    st.title("黃金多空因子量化儀表板")

# --- 3. 更新時間顯示 (台北時間) ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz).strftime('%Y-%m-%d %H:%M:%S')
st.caption(f"🕒 數據最後更新時間 (台北)：{now_tw}")

# --- 4. 側邊欄：權重設定與 OSE 自評輸入 ---
st.sidebar.header("1. 設定因子權重 (%)")
w_dxy = st.sidebar.slider("美元指數 (DXY)", 0, 100, 25)
w_vix = st.sidebar.slider("避險情緒 (VIX)", 0, 100, 25)
w_rate = st.sidebar.slider("10Y美債收益率", 0, 100, 25)
w_ose = st.sidebar.slider("OSE 自評因子", 0, 100, 25)

st.sidebar.divider()
st.sidebar.header("2. OSE 買進需求評分")
# 手填數字欄位 1-5
ose_input = st.sidebar.number_input("OSE 需求強度 (1-5)", min_value=1, max_value=5, value=3, step=1)
st.sidebar.caption("說明：5 代表強烈需求(利多)，1 代表無需求(利空)。")

# 檢查權重總和
total_w = w_dxy + w_vix + w_rate + w_ose
if total_w != 100:
    st.sidebar.error(f"⚠️ 權重總和：{total_w}% (須調整為 100%)")

# --- 5. 數據抓取 ---
tickers = {"Gold": "GC=F", "DXY": "DX-Y.NYB", "VIX": "^VIX", "10Y_Bond": "^TNX"}

@st.cache_data(ttl=600)
def get_data():
    try:
        df = yf.download(list(tickers.values()), period="1mo")['Close']
        inv_tickers = {v: k for k, v in tickers.items()}
        df = df.rename(columns=inv_tickers).dropna()
        return df
    except Exception as e:
        st.error(f"數據抓取失敗: {e}")
        return None

# --- 6. 主要邏輯判斷 ---
df = get_data()

if df is not None:
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # --- 區塊 A：即時數據儀表板 ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("當前金價 (期貨)", f"${curr['Gold']:.1f}", f"{(curr['Gold']-prev['Gold']):.1f}")
    m2.metric("美元指數 (DXY)", f"{curr['DXY']:.2f}", f"{(curr['DXY']-prev['DXY']):.2f}", delta_color="inverse")
    m3.metric("10Y美債收益率", f"{curr['10Y_Bond']:.2f}%", f"{(curr['10Y_Bond']-prev['10Y_Bond']):.2f}%", delta_color="inverse")
    m4.metric("VIX 恐慌指數", f"{curr['VIX']:.2f}", f"{(curr['VIX']-prev['VIX']):.2f}")

    # --- 區塊 B：因子解讀指南 ---
    with st.expander("📖 因子解讀指南：為什麼這些指標會影響金價？"):
        g_col1, g_col2, g_col3 = st.columns(3)
        g_col1.write("**美元指數 (DXY)** \n通常與金價**反向**。美元走強，黃金相對變貴，需求下降。")
        g_col2.write("**10Y美債收益率** \n通常與金價**反向**。利率高則持有黃金的「機會成本」增加。")
        g_col3.write("**VIX 恐慌指數** \n通常與金價**正向**。市場動盪時，避險資金會流入黃金。")
        st.info(f"💡 **OSE 自評因子 (當前輸入: {ose_input})**: 由 OSE 內部評估。5分代表需求旺盛(利多)，1分代表需求疲軟(利空)。")

    st.divider()

    # --- 7. 加權得分計算 (以 50 分為中性分界) ---
    # 客觀指標得分 (-1 或 1)
    s_dxy = 1 if curr['DXY'] < prev['DXY'] else -1
    s_vix = 1 if curr['VIX'] > prev['VIX'] else -1
    s_rate = 1 if curr['10Y_Bond'] < prev['10Y_Bond'] else -1
    
    # OSE 分數映射：1->-1, 2->-0.5, 3->0, 4->0.5, 5->1
    s_ose = (ose_input - 3) / 2
    
    # 原始加權分數 (-100 ~ 100)
    raw_score = (s_dxy * w_dxy + s_vix * w_vix + s_rate * w_rate + s_ose * w_ose)
    # 映射到 0 ~ 100 分 (50 為中性)
    display_score = (raw_score + 100) / 2

    # --- 區塊 C：結論建議 ---
    st.subheader("💡 綜合量化結論")
    score_col, advice_col = st.columns([1, 2])
    
    with score_col:
        if display_score > 5
