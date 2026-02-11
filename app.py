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

    # --- 區塊 B：新手教學 (位置調整至指標下方) ---
    with st.expander("📖 因子解讀指南：為什麼這些指標會影響金價？"):
        g_col1, g_col2, g_col3 = st.columns(3)
        g_col1.write("**美元指數 (DXY)** \n通常與金價**反向**。美元強則金價受壓。")
        g_col2.write("**10Y美債收益率** \n通常與金價**反向**。利率高則持有黃金成本變高。")
        g_col3.write("**VIX 恐慌指數** \n通常與金價**正向**。市場恐慌時避險資金湧入黃金。")

    st.divider()

    # --- 計算得分 (以 50 分為基準) ---
    s_dxy = 1 if curr['DXY'] < prev['DXY'] else -1
    s_vix = 1 if curr['VIX'] > prev['VIX'] else -1
    s_rate = 1 if curr['10Y_Bond'] < prev['10Y_Bond'] else -1
    
    raw_score = (s_dxy * w_dxy + s_vix * w_vix + s_rate * w_rate) # -100 ~ 100
    display_score = (raw_score + 100) / 2  # 映射到 0 ~ 100

    # --- 區塊 C：綜合結論建議 ---
    st.subheader("💡 綜合量化結論")
    score_col, advice_col = st.columns([1, 2])
    
    with score_col:
        st.write("### 綜合評分")
        if display_score > 50:
            st.markdown(f"<h1 style='color: #2ecc71;'>{display_score:.0f} 分 (看多)</h1>", unsafe_allow_html=True)
        elif display_score < 50:
            st.markdown(f"<h1 style='color: #e74c3c;'>{display_score:.0f} 分 (看空)</h1>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h1 style='color: #f1c40f;'>50 分 (中性)</h1>", unsafe_allow_html=True)

    with advice_col:
        st.write("### 戰略建議")
        if display_score >= 75:
            st.success("🟢 **強力利多**：環境極其有利。")
        elif display_score > 50:
            st.info("🟡 **偏多觀望**：環境整體偏好，但需留意個別指標波動。")
        elif display_score == 50:
            st.warning("⚪ **中性**：多空因子互相抵銷，方向不明。")
        else:
            st.error("🔴 **看空建議**：目前持有黃金機會成本過高或風險較大。")

    st.divider()

    # --- 區塊 D：趨勢圖 ---
    st.subheader("📈 因子走勢對照 (歸一化 100%)")
    df_pct = (df / df.iloc[0] * 100)
    st.line_chart(df_pct)

except Exception as e:
    st.error(f"發生錯誤: {e}")
