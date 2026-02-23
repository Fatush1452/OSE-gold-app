import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

# --- 1. 設定區 ---
LOGO_URL = "https://raw.githubusercontent.com/Fatush1452/OSE-gold-app/main/OSE.png"
st.set_page_config(page_title="黃金量化分析儀表板", layout="wide")

# --- 2. 顯示 Logo 與 標題 ---
t_col1, t_col2 = st.columns([1, 3])
with t_col1:
    try:
        st.image(LOGO_URL, width=250)
    except:
        st.write("🏮 [Logo]")
with t_col2:
    st.title("黃金多空因子量化儀表板")

# --- 3. 更新時間 (台北) ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz).strftime('%Y-%m-%d %H:%M:%S')
st.caption(f"🕒 頁面刷新時間 (台北)：{now_tw}")

# --- 4. 側邊欄設定 ---
st.sidebar.header("1. 設定因子權重 (%)")
w_dxy = st.sidebar.slider("美元指數 (DXY)", 0, 100, 25)
w_vix = st.sidebar.slider("避險情緒 (VIX)", 0, 100, 25)
w_rate = st.sidebar.slider("10Y美債收益率", 0, 100, 25)
w_ose = st.sidebar.slider("OSE 自評因子", 0, 100, 25)

st.sidebar.divider()
st.sidebar.header("2. OSE 買進需求評分")
ose_input = st.sidebar.number_input("OSE 需求強度 (1-5)", min_value=1, max_value=5, value=3, step=1)

total_w = w_dxy + w_vix + w_rate + w_ose
if total_w != 100:
    st.sidebar.error(f"⚠️ 權重總和：{total_w}% (須為 100%)")

# --- 5. 數據抓取 (加強防錯版本) ---
tickers = {"Gold": "GC=F", "DXY": "DX-Y.NYB", "VIX": "^VIX", "10Y_Bond": "^TNX"}

@st.cache_data(ttl=600)
def get_data():
    try:
        # 增加抓取天數到 2 個月，確保週末過後有足夠緩衝資料
        df = yf.download(list(tickers.values()), period="2mo")['Close']
        inv_tickers = {v: k for k, v in tickers.items()}
        df = df.rename(columns=inv_tickers)
        # 先前向填充缺失值，再刪除完全沒數據的行
        df = df.ffill().dropna()
        return df
    except:
        return None

df = get_data()

# --- 6. 核心判斷：檢查資料是否為空 ---
if df is not None and len(df) >= 2:
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # --- 區塊 A：即時數據指標 ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("當前金價 (期貨)", f"${curr['Gold']:.1f}", f"{(curr['Gold']-prev['Gold']):.1f}")
    m2.metric("美元指數 (DXY)", f"{curr['DXY']:.2f}", f"{(curr['DXY']-prev['DXY']):.2f}", delta_color="inverse")
    m3.metric("10Y美債收益率", f"{curr['10Y_Bond']:.2f}%", f"{(curr['10Y_Bond']-prev['10Y_Bond']):.2f}%", delta_color="inverse")
    m4.metric("VIX 恐慌指數", f"{curr['VIX']:.2f}", f"{(curr['VIX']-prev['VIX']):.2f}")

    # --- 區塊 B：因子解讀指南 ---
    with st.expander("📖 因子解讀指南"):
        g_col1, g_col2, g_col3 = st.columns(3)
        g_col1.write("**美元指數 (DXY)** \n與金價**反向**。")
        g_col2.write("**10Y美債收益率** \n與金價**反向**。")
        g_col3.write("**VIX 恐慌指數** \n與金價**正向**。")

    st.divider()

    # --- 區塊 C：四個外部因子的即時走勢圖 ---
    st.subheader("📈 外部因子走勢追蹤")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.caption("黃金現價趨勢")
        st.line_chart(df['Gold'], height=150)
    with c2:
        st.caption("美元指數 (DXY)")
        st.line_chart(df['DXY'], height=150)
    with c3:
        st.caption("10Y美債收益率")
        st.line_chart(df['10Y_Bond'], height=150)
    with c4:
        st.caption("VIX 恐慌指數")
        st.line_chart(df['VIX'], height=150)

    st.divider()

    # --- 區塊 D：綜合量化結論 ---
    s_dxy = 1 if curr['DXY'] < prev['DXY'] else -1
    s_vix = 1 if curr['VIX'] > prev['VIX'] else -1
    s_rate = 1 if curr['10Y_Bond'] < prev['10Y_Bond'] else -1
    s_ose = (ose_input - 3) / 2
    
    raw_score = (s_dxy * w_dxy + s_vix * w_vix + s_rate * w_rate + s_ose * w_ose)
    display_score = (raw_score + 100) / 2

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
        if display_score >= 75: st.success("🟢 **強力利多**：指標高度共振。")
        elif display_score > 50: st.info("🟡 **偏多觀望**：環境整體偏好。")
        elif display_score == 50: st.warning("⚪ **中性**：建議觀望。")
        else: st.error("🔴 **看空建議**：規避下行風險。")

else:
    # 當數據抓不到時，顯示友善提示而非 Error
    st.warning("📊 正在嘗試連線至金融資料源... 若持續出現此訊息，可能是因為目前處於開盤交替時段數據尚未產出，請稍後幾分鐘再重新整理頁面。")
    st.info("提示：您可以檢查側邊欄的 OSE 自評因子是否正確設定。")
