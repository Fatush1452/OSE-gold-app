import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# --- 1. 圖片網址設定 ---
# 請確保 logo.png 已上傳至您的 GitHub 儲存庫
LOGO_URL = "https://raw.githubusercontent.com/Fatush1452/OSE-gold-app/main/OSE.png"

st.set_page_config(page_title="黃金量化分析儀表板", layout="wide")

# --- 2. 顯示 Logo 與 標題 ---
t_col1, t_col2 = st.columns([1, 5])
with t_col1:
    # 使用 try-except 以防圖片連結失效時網頁仍能運作
    try:
        st.image(LOGO_URL, width=200)
    except:
        st.write("🏮 [Logo]")
with t_col2:
    st.title("黃金多空因子量化儀表板")

# --- 3. 更新時間顯示 (台北時間) ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz).strftime('%Y-%m-%d %H:%M:%S')
st.caption(f"🕒 數據最後更新時間 (台北)：{now_tw}")

# --- 4. 側邊欄權重設定 ---
st.sidebar.header("1. 設定因子權重 (%)")
w_dxy = st.sidebar.slider("美元指數 (DXY)", 0, 100, 30)
w_vix = st.sidebar.slider("避險情緒 (VIX)", 0, 100, 20)
w_rate = st.sidebar.slider("10Y美債收益率", 0, 100, 50)

if w_dxy + w_vix + w_rate != 100:
    st.sidebar.error("⚠️ 警告：權重總和不等於 100%。")

# --- 5. 數據抓取 ---
tickers = {"Gold": "GC=F", "DXY": "DX-Y.NYB", "VIX": "^VIX", "10Y_Bond": "^TNX"}

@st.cache_data(ttl=600)
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
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("當前金價 (期貨)", f"${curr['Gold']:.1f}", f"{(curr['Gold']-prev['Gold']):.1f}")
    m2.metric("美元指數 (DXY)", f"{curr['DXY']:.2f}", f"{(curr['DXY']-prev['DXY']):.2f}", delta_color="inverse")
    m3.metric("10Y美債收益率", f"{curr['10Y_Bond']:.2f}%", f"{(curr['10Y_Bond']-prev['10Y_Bond']):.2f}%", delta_color="inverse")
    m4.metric("VIX 恐慌指數", f"{curr['VIX']:.2f}", f"{(curr['VIX']-prev['VIX']):.2f}")

    # --- 區塊 B：因子解讀指南 (位置調整) ---
    with st.expander("📖 因子解讀指南：為什麼這些指標會影響金價？"):
        g_col1, g_col2, g_col3 = st.columns(3)
        g_col1.write("**美元指數 (DXY)** \n通常與金價**反向**。美元走強時，以美元計價的黃金對其他貨幣持有者來說變貴，導致需求與價格受壓。")
        g_col2.write("**10Y美債收益率** \n通常與金價**反向**。黃金不生利息，當債券收益率上升，持有黃金的機會成本增加，資金易流向債市。")
        g_col3.write("**VIX 恐慌指數** \n通常與金價**正向**。反映市場對未來波動的預期。當股市動盪或政治緊張時，黃金發揮避險功能吸引資金。")

    st.divider()

    # --- 6. 計算得分 (50分為基準) ---
    s_dxy = 1 if curr['DXY'] < prev['DXY'] else -1
    s_vix = 1 if curr['VIX'] > prev['VIX'] else -1
    s_rate = 1 if curr['10Y_Bond'] < prev['10Y_Bond'] else -1
    
    raw_score = (s_dxy * w_dxy + s_vix * w_vix + s_rate * w_rate) # -100 ~ 100
    display_score = (raw_score + 100) / 2  # 0 ~ 100

    # --- 區塊 C：綜合結論建議 ---
    st.subheader("💡 綜合量化結論")
    score_col, advice_col = st.columns([1, 2])
    
    with score_col:
        if display_score > 50:
            st.markdown(f"<h1 style='color: #2ecc71;'>{display_score:.0f} 分 (看多)</h1>", unsafe_allow_html=True)
        elif display_score < 50:
            st.markdown(f"<h1 style='color: #e74c3c;'>{display_score:.0f} 分 (看空)</h1>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h1 style='color: #f1c40f;'>50 分 (中性)</h1>", unsafe_allow_html=True)

    with advice_col:
        st.write("### 戰略建議")
        if display_score >= 75:
            st.success("🟢 **強力利多**：所有指標皆有利於金價，環境極其理想。")
        elif display_score > 50:
            st.info("🟡 **偏多觀望**：整體環境偏好，可留意分批佈局機會。")
        elif display_score == 50:
            st.warning("⚪ **中性**：多空因子互相抵銷，建議等待明確趨勢。")
        else:
            st.error("🔴 **看空/風險警告**：目前環境持有黃金風險較高，建議審慎。")

    st.divider()

    # --- 區塊 D：趨勢圖 ---
    st.subheader("📈 因子走勢對照 (歸一化 100%)")
    df_pct = (df / df.iloc[0] * 100)
    st.line_chart(df_pct)

except Exception as e:
    st.error(f"數據加載中或發生錯誤: {e}")
