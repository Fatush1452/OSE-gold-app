import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz
import feedparser

# --- 1. 設定區 ---
# 請確認此連結在瀏覽器能直接看到圖片
LOGO_URL = "https://raw.githubusercontent.com/Fatush1452/OSE-gold-app/main/OSE.png"

st.set_page_config(page_title="黃金量化分析儀表板", layout="wide")

# --- 2. 數據與新聞抓取函數 (提升穩定性) ---

@st.cache_data(ttl=3600) # 改為 1 小時更新一次新聞，避免被封鎖
def get_gold_news():
    # 改用 CNBC 財經新聞，連結較穩定
    rss_url = "https://www.cnbc.com/id/15839072/device/rss/rss.html" 
    try:
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            return [{"title": "目前無新標題，請稍後刷新", "link": "#"}]
        
        news_list = []
        for entry in feed.entries[:5]:
            news_list.append({"title": entry.title, "link": entry.link})
        return news_list
    except Exception as e:
        return [{"title": f"新聞抓取異常: {str(e)}", "link": "#"}]

@st.cache_data(ttl=600)
def get_market_data():
    tickers = {"Gold": "GC=F", "DXY": "DX-Y.NYB", "VIX": "^VIX", "10Y_Bond": "^TNX"}
    try:
        df = yf.download(list(tickers.values()), period="2mo")['Close']
        df = df.rename(columns={v: k for k, v in tickers.items()}).ffill().dropna()
        return df
    except:
        return None

# --- 3. 顯示 Logo 與 標題 (垂直置中) ---
t_col1, t_col2 = st.columns([1, 4], vertical_alignment="center")
with t_col1:
    st.image(LOGO_URL, width=220)
with t_col2:
    st.markdown("<h1 style='margin:0;'>黃金多空因子量化儀表板</h1>", unsafe_allow_html=True)

# 更新時間
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

# --- 5. 畫面顯示邏輯 ---

# 新聞區塊
news_data = get_gold_news()
st.subheader("📰 即時黃金與大宗商品新聞 (CNBC)")
if news_data:
    for news in news_data:
        st.markdown(f"● [{news['title']}]({news['link']})")

st.divider()

# 數據區塊
df = get_market_data()
if df is not None and len(df) >= 2:
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    # 即時數據指標
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("當前金價 (期貨)", f"${curr['Gold']:.1f}", f"{(curr['Gold']-prev['Gold']):.1f}")
    m2.metric("美元指數 (DXY)", f"{curr['DXY']:.2f}", f"{(curr['DXY']-prev['DXY']):.2f}", delta_color="inverse")
    m3.metric("10Y美債收益率", f"{curr['10Y_Bond']:.2f}%", f"{(curr['10Y_Bond']-prev['10Y_Bond']):.2f}%", delta_color="inverse")
    m4.metric("VIX 恐慌指數", f"{curr['VIX']:.2f}", f"{(curr['VIX']-prev['VIX']):.2f}")

    # 指數走勢圖
    st.subheader("📈 外部因子走勢追蹤")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.line_chart(df['Gold'], height=150)
    with c2: st.line_chart(df['DXY'], height=150)
    with c3: st.line_chart(df['10Y_Bond'], height=150)
    with c4: st.line_chart(df['VIX'], height=150)

    st.divider()

    # 綜合結論計算
    s_dxy = 1 if curr['DXY'] < prev['DXY'] else -1
    s_vix = 1 if curr['VIX'] > prev['VIX'] else -1
    s_rate = 1 if curr['10Y_Bond'] < prev['10Y_Bond'] else -1
    s_ose = (ose_input - 3) / 2
    
    raw_score = (s_dxy * w_dxy + s_vix * w_vix + s_rate * w_rate + s_ose * w_ose)
    display_score = (raw_score + 100) / 2

    st.subheader("💡 綜合量化結論")
    score_col, advice_col = st.columns([1, 2])
    with score_col:
        color = "#2ecc71" if display_score > 50 else "#e74c3c" if display_score < 50 else "#f1c40f"
        st.markdown(f"<h1 style='color: {color};'>{display_score:.0f} 分</h1>", unsafe_allow_html=True)
    with advice_col:
        if display_score > 50: st.success("🟢 建議：環境利多。")
        elif display_score < 50: st.error("🔴 建議：避險看空。")
        else: st.warning("⚪ 建議：中性觀望。")
else:
    st.warning("數據抓取中，請稍候並確認連線狀態...")
