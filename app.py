import streamlit as st
import yfinance as yf
import pandas as pd

# 網頁標題
st.set_page_config(page_title="黃金量化決策儀表板", layout="wide")
st.title("🏆 黃金多空因子量化分析網頁")

# --- 側邊欄：設定權重 ---
st.sidebar.header("1. 設定因子權重 (%)")
w_dxy = st.sidebar.slider("美元指數 (DXY)", 0, 100, 30)
w_vix = st.sidebar.slider("避險情緒 (VIX)", 0, 100, 20)
w_rate = st.sidebar.slider("美債收益率 (10Y)", 0, 100, 50)

if w_dxy + w_vix + w_rate != 100:
    st.sidebar.error("⚠️ 權重總和必須等於 100%")

# --- 數據抓取 ---
@st.cache_data(ttl=3600)
def fetch_data():
    # 抓取金價、美元、VIX、10年債
    tickers = {"Gold": "GC=F", "DXY": "DX-Y.NYB", "VIX": "^VIX", "10Y_Bond": "^TNX"}
    df = yf.download(list(tickers.values()), period="1mo", interval="1d")['Close']
    df.columns = tickers.keys()
    return df

data = fetch_data()
current = data.iloc[-1]
prev = data.iloc[-2]

# --- 評分邏輯 (歸一化範例) ---
def calculate_score():
    # 美元下跌為利多 (+), 上漲為利空 (-)
    s_dxy = 1 if current['DXY'] < prev['DXY'] else -1
    # VIX 上漲為利多 (+), 下跌為利空 (-)
    s_vix = 1 if current['VIX'] > prev['VIX'] else -1
    # 利率下跌為利多 (+), 上漲為利空 (-)
    s_rate = 1 if current['10Y_Bond'] < prev['10Y_Bond'] else -1
    
    total_score = (s_dxy * w_dxy + s_vix * w_vix + s_rate * w_rate) / 100
    return s_dxy, s_vix, s_rate, total_score

s_dxy, s_vix, s_rate, final_score = calculate_score()

# --- 儀表板顯示 ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("當前金價", f"${current['Gold']:.2f}", f"{(current['Gold']-prev['Gold']):.2f}")
col2.metric("美元指數", f"{current['DXY']:.2f}", f"{(current['DXY']-prev['DXY']):.2f}", delta_color="inverse")
col3.metric("10Y美債收益率", f"{current['10Y_Bond']:.2f}%", f"{(current['10Y_Bond']-prev['10Y_Bond']):.2f}%", delta_color="inverse")
col4.metric("VIX 恐慌指數", f"{current['VIX']:.2f}", f"{(current['VIX']-prev['VIX']):.2f}")

st.divider()

# --- 決策建議 ---
st.subheader("💡 量化決策建議")
if final_score > 0.2:
    st.success(f"綜合得分：{final_score:.2f} | 訊號：強力看多 (建議分批入場)")
elif final_score < -0.2:
    st.error(f"綜合得分：{final_score:.2f} | 訊號：強力看空 (建議減持或避險)")
else:
    st.warning(f"綜合得分：{final_score:.2f} | 訊號：震盪觀望 (方向不明)")

# --- 圖表分析 ---
st.subheader("📈 關鍵因子趨勢對照")
st.line_chart(data[['Gold', 'DXY', 'VIX']])
