import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="黃金量化分析", layout="wide")
st.title("🏆 黃金多空因子量化儀表板")

# --- 側邊欄設定 ---
st.sidebar.header("1. 設定因子權重 (%)")
w_dxy = st.sidebar.slider("美元指數 (DXY)", 0, 100, 30)
w_vix = st.sidebar.slider("避險情緒 (VIX)", 0, 100, 20)
w_rate = st.sidebar.slider("10Y美債收益率", 0, 100, 50)

# --- 數據抓取 (改用更穩定的字典對應) ---
tickers = {
    "Gold": "GC=F", 
    "DXY": "DX-Y.NYB", 
    "VIX": "^VIX", 
    "10Y_Bond": "^TNX"
}

@st.cache_data(ttl=3600)
def get_clean_data():
    df = yf.download(list(tickers.values()), period="1mo")['Close']
    # 確保欄位名稱對應正確
    inv_tickers = {v: k for k, v in tickers.items()}
    df = df.rename(columns=inv_tickers)
    return df.dropna()

try:
    df = get_clean_data()
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # --- 計算得分邏輯 ---
    # 美元跌 = 金價利多(+1)
    s_dxy = 1 if curr['DXY'] < prev['DXY'] else -1
    # VIX 漲 = 金價利多(+1)
    s_vix = 1 if curr['VIX'] > prev['VIX'] else -1
    # 利率跌 = 金價利多(+1)
    s_rate = 1 if curr['10Y_Bond'] < prev['10Y_Bond'] else -1
    
    final_score = (s_dxy * w_dxy + s_vix * w_vix + s_rate * w_rate) / 100

    # --- 儀表板視覺化 ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("當前金價 (期貨)", f"${curr['Gold']:.1f}", f"{(curr['Gold']-prev['Gold']):.1f}")
    col2.metric("美元指數 (DXY)", f"{curr['DXY']:.2f}", f"{(curr['DXY']-prev['DXY']):.2f}", delta_color="inverse")
    col3.metric("10Y美債收益率", f"{curr['10Y_Bond']:.2f}%", f"{(curr['10Y_Bond']-prev['10Y_Bond']):.2f}%", delta_color="inverse")
    col4.metric("VIX 恐慌指數", f"{curr['VIX']:.2f}", f"{(curr['VIX']-prev['VIX']):.2f}")

    st.divider()

    # --- 決策區塊 ---
    st.subheader("💡 綜合量化建議")
    if final_score >= 0.2:
        st.success(f"綜合得分：{final_score:.2f} | 訊號：【偏多】各項指標有利於金價上漲。")
    elif final_score <= -0.2:
        st.error(f"綜合得分：{final_score:.2f} | 訊號：【偏空】環境不利於持有黃金。")
    else:
        st.warning(f"綜合得分：{final_score:.2f} | 訊號：【中性】指標互相抵銷，建議觀望。")

    # --- 圖表區 ---
    st.subheader("📈 因子走勢對照 (歸一化百分比)")
    # 為了方便在同一張圖比較，我們看變動百分比
    df_pct = (df / df.iloc[0] * 100)
    st.line_chart(df_pct)

except Exception as e:
    st.error(f"數據讀取中或發生錯誤: {e}")
    st.info("提示：請檢查網路連接，或稍後再試（市場關閉期間部分數據可能缺失）。")
