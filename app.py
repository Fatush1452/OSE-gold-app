import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# --- 1. 請在此替換您的圖片網址 ---
LOGO_URL = "https://raw.githubusercontent.com/Fatush1452/OSE-gold-app/main/OSE.png"

st.set_page_config(page_title="黃金量化分析儀表板", layout="wide")

# --- 2. 顯示圖片與標題 ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image(LOGO_URL, width=150) # 顯示您的圖片
with col_title:
    st.title("黃金多空因子量化儀表板")

# --- 3. 獲取當前時間 (台北時間) ---
tw_time = datetime.now(pytz.timezone('Asia/Taipei')).strftime('%Y-%m-%d %H:%M:%S')
st.caption(f"🕒 數據最後更新時間 (台北)：{tw_time}")

# --- 4. 側邊欄權重設定 ---
st.sidebar.header("1. 設定因子權重 (%)")
w_dxy = st.sidebar.slider("美元指數 (DXY)", 0, 100, 30)
w_vix = st.sidebar.slider("避險情緒 (VIX)", 0, 100, 20)
w_rate = st.sidebar.slider("10Y美債收益率", 0, 100, 50)

# --- 5. 數據抓取與計算 (維持原有邏輯) ---
tickers = {"Gold": "GC=F", "DXY": "DX-Y.NYB", "VIX": "^VIX", "10Y_Bond": "^TNX"}

@st.cache_data(ttl=600) # 設定 10 分鐘更新一次
def get_data():
    df = yf.download(list(tickers.values()), period="1mo")['Close']
    inv_tickers = {v: k for k, v in tickers.items()}
    df = df.rename(columns=inv_tickers).dropna()
    return df

try:
    df = get_data()
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # 即時指標顯示
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("當前金價", f"${curr['Gold']:.1f}", f"{(curr['Gold']-prev['Gold']):.1f}")
    col2.metric("美元指數", f"{curr['DXY']:.2f}", f"{(curr['DXY']-prev['DXY']):.2f}", delta_color="inverse")
    col3.metric("10Y美債", f"{curr['10Y_Bond']:.2f}%", f"{(curr['10Y_Bond']-prev['10Y_Bond']):.2f}%", delta_color="inverse")
    col4.metric("VIX 恐慌", f"{curr['VIX']:.2f}", f"{(curr['VIX']-prev['VIX']):.2f}")

    # 因子解讀指南
    with st.expander("📖 因子解讀指南"):
        st.write("這裡是各指數對金價影響的說明...")

    st.divider()

    # --- 6. 綜合評分 (50分為基準) ---
    s_dxy = 1 if curr['DXY'] < prev['DXY'] else -1
    s_vix = 1 if curr['VIX'] > prev['VIX'] else -1
    s_rate = 1 if curr['10Y_Bond'] < prev['10Y_Bond'] else -1
    
    raw_score = (s_dxy * w_dxy + s_vix * w_vix + s_rate * w_rate)
    display_score = (raw_score + 100) / 2 

    st.subheader("💡 綜合量化結論")
    s_col, a_col = st.columns([1, 2])
    with s_col:
        if display_score > 50:
            st.markdown(f"<h1 style='color: #2ecc71;'>{display_score:.0f} 分 (看多)</h1>", unsafe_allow_html=True)
        elif display_score < 50:
            st.markdown(f"<h1 style='color: #e74c3c;'>{display_score:.0f} 分 (看空)</h1>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h1 style='color: #f1c40f;'>50 分 (中性)</h1>", unsafe_allow_html=True)

    with a_col:
        st.write("### 戰略建議")
        # 根據分數顯示建議... (代碼同前)

    st.line_chart(df / df.iloc[0] * 100)

except Exception as e:
    st.error(f"數據更新中: {e}")
