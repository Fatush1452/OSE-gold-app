import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="黃金量化分析儀表板", layout="wide")

# --- 標題與簡介 ---
st.title("🏆 黃金多空因子量化儀表板")
st.markdown("""
本系統透過分析影響金價的**三大核心宏觀因子**（貨幣、利率、情緒），結合權重計算得出綜合得分。
* **數值越高（綠色）**：代表環境極度利多黃金。
* **數值越低（紅色）**：代表環境利空，持有黃金風險較高。
""")

# --- 側邊欄：設定權重 ---
st.sidebar.header("1. 設定因子權重 (%)")
st.sidebar.info("權重代表您認為該因子對金價的影響程度，總和須為 100%。")
w_dxy = st.sidebar.slider("美元指數 (DXY)", 0, 100, 30)
w_vix = st.sidebar.slider("避險情緒 (VIX)", 0, 100, 20)
w_rate = st.sidebar.slider("10Y美債收益率", 0, 100, 50)

if w_dxy + w_vix + w_rate != 100:
    st.sidebar.error("⚠️ 警告：權重總和不等於 100%，計算結果將會失真。")

# --- 數據抓取邏輯 ---
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

    # --- 計算得分 ---
    s_dxy = 1 if curr['DXY'] < prev['DXY'] else -1
    s_vix = 1 if curr['VIX'] > prev['VIX'] else -1
    s_rate = 1 if curr['10Y_Bond'] < prev['10Y_Bond'] else -1
    final_score = (s_dxy * w_dxy + s_vix * w_vix + s_rate * w_rate) / 100

    # --- 區塊 A：即時指標 ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("當前金價 (期貨)", f"${curr['Gold']:.1f}", f"{(curr['Gold']-prev['Gold']):.1f}")
    col2.metric("美元指數 (DXY)", f"{curr['DXY']:.2f}", f"{(curr['DXY']-prev['DXY']):.2f}", delta_color="inverse")
    col3.metric("10Y美債收益率", f"{curr['10Y_Bond']:.2f}%", f"{(curr['10Y_Bond']-prev['10Y_Bond']):.2f}%", delta_color="inverse")
    col4.metric("VIX 恐慌指數", f"{curr['VIX']:.2f}", f"{(curr['VIX']-prev['VIX']):.2f}")

    st.divider()

    # --- 區塊 B：綜合結論建議 ---
    st.subheader("💡 綜合量化結論與建議")
    
    # 建立一個醒目的顏色區塊
    score_col, advice_col = st.columns([1, 2])
    
    with score_col:
        st.write("### 綜合得分")
        if final_score >= 0.5:
            st.markdown(f"<h1 style='color: #2ecc71;'>{final_score:.2f} (強力看多)</h1>", unsafe_allow_html=True)
        elif final_score > 0:
            st.markdown(f"<h1 style='color: #f1c40f;'>{final_score:.2f} (偏多觀望)</h1>", unsafe_allow_html=True)
        elif final_score > -0.5:
            st.markdown(f"<h1 style='color: #e67e22;'>{final_score:.2f} (偏空觀望)</h1>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h1 style='color: #e74c3c;'>{final_score:.2f} (強力看空)</h1>", unsafe_allow_html=True)

    with advice_col:
        st.write("### 戰略建議")
        if final_score >= 0.5:
            st.write("目前宏觀環境對黃金極其有利（美元與利率雙降，或恐慌噴發）。建議可分批建立多單。")
        elif final_score > 0:
            st.write("指標互有矛盾，但多方略佔優勢。建議輕倉或等待美元進一步轉弱。")
        else:
            st.write("目前環境持有黃金的機會成本過高（利率上升或美元強勢）。建議暫時觀望或進行避險。")

    st.divider()

    # --- 區塊 C：趨勢對照圖 ---
    st.subheader("📈 因子走勢對照 (歸一化 100%)")
    st.info("此圖表將所有指標縮放至同一比例（起點為 100），方便觀察各因子與金價的連動性。")
    df_pct = (df / df.iloc[0] * 100)
    st.line_chart(df_pct)

    st.divider()

    # --- 區塊 D：新手教學 (影響說明) ---
    with st.expander("📖 為什麼這些因子會影響金價？(點擊展開)"):
        st.write("""
        1. **美元指數 (DXY)**：黃金以美元計價。當美元變強，對其他國家的人來說黃金變貴了，需求會下降。**（通常與金價反向）**
        2. **10Y美債收益率**：黃金是不會產生利息的資產。當美債利息變高，投資人會把錢移往債券。**（通常與金價反向）**
        3. **VIX 恐慌指數**：反映市場動盪程度。當股市大跌或地緣政治緊張，資金會湧入黃金避險。**（通常與金價正向）**
        """)

except Exception as e:
    st.error(f"數據加載失敗：{e}")
