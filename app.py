import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="黃金量化分析儀表板", layout="wide")

# --- 標題與簡介 ---
st.title("🏆 黃金多空因子量化儀表板")
st.markdown("""
本系統透過分析影響金價的**三大核心宏觀因子**，結合權重計算得出綜合得分。
* **50 分以上**：代表環境偏向**利多**黃金。
* **50 分以下**：代表環境偏向**利空**黃金。
""")

# --- 側邊欄：設定權重 ---
st.sidebar.header("1. 設定因子權重 (%)")
w_dxy = st.sidebar.slider("美元指數 (DXY)", 0, 100, 30)
w_vix = st.sidebar.slider("避險情緒 (VIX)", 0, 100, 20)
w_rate = st.sidebar.slider("10Y美債收益率", 0, 100, 50)

if w_dxy + w_vix + w_rate != 100:
    st.sidebar.error("⚠️ 警告：權重總和不等於 100%。")

# --- 數據抓取 ---
tickers = {"Gold": "GC=F", "DXY": "DX-Y.NYB", "VIX": "^VIX", "10Y_Bond": "^TNX"}

@st.cache_data(ttl=3600)
def get_data():
    df = yf.download(list(tickers.values()), period="1mo")['Close']
    inv_tickers = {v: k for k, v in tickers.items()}
    df = df.rename(columns=inv_tickers).dropna()
    return df

try:
    df = get_data()
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # --- 區塊 A：即時指標 ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("當前金價 (期貨)", f"${curr['Gold']:.1f}", f"{(curr['Gold']-prev['Gold']):.1f}")
    col2.metric("美元指數 (DXY)", f"{curr['DXY']:.2f}", f"{(curr['DXY']-prev['DXY']):.2f}", delta_color="inverse")
    col3.metric("10Y美債收益率", f"{curr['10Y_Bond']:.2f}%", f"{(curr['10Y_Bond']-prev['10Y_Bond']):.2f}%", delta_color="inverse")
    col4.metric("VIX 恐慌指數", f"{curr['VIX']:.2f}", f"{(curr['VIX']-prev['VIX']):.2f}")

    # --- 區塊 B：新手教學 (位置更換到指標下方) ---
    with st.expander("📖 因子解讀指南：為什麼這些指標會影響金價？"):
        g_col1, g_col2, g_col3 = st.columns(3)
        g_col1.write("**美元指數 (DXY)** \n黃金以美元計價。當美元變強，黃金相對變貴，需求下降。  \n👉 *通常與金價反向*")
        g_col2.write("**10Y美債收益率** \n黃金不孳息。當美債利息變高，持有黃金的機會成本增加。  \n👉 *通常與金價反向*")
        g_col3.write("**VIX 恐慌指數** \n反映市場恐慌。股市動盪或地緣政治緊張時，資金湧入黃金。  \n👉 *通常與金價正向*")

    st.divider()

    # --- 計算得分 (以 50 分為中性基準) ---
    # 原始得分為 -100 ~ 100，我們將其轉換為 0 ~ 100 區間
    s_dxy = 1 if curr['DXY'] < prev['DXY'] else -1
    s_vix = 1 if curr['VIX'] > prev['VIX'] else -1
    s_rate = 1 if curr['10Y_Bond'] < prev['10Y_Bond'] else -1
    
    raw_score = (s_dxy * w_dxy + s_vix * w_vix + s_rate * w_rate) # 範圍 -100 ~ 100
    display_score = (raw_score + 100) / 2  # 轉換為 0 ~ 100，50分為中性

    # --- 區塊 C：綜合結論建議 ---
    st.subheader("💡 綜合量化結論")
    score
