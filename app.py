import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات حساب التمويل (5000$)
ACCOUNT_SIZE = 5000.0
DAILY_GOAL_PCT = 1.5  # هدف الربح اليومي (75$)
RISK_PER_TRADE = 0.5  # المخاطرة للصفقة (25$)

st.set_page_config(page_title="Funded Sniper Pro", page_icon="🛡️", layout="wide")

# --- 1. إدارة سجل الأرباح (Sidebar) ---
if 'total_pnl' not in st.session_state:
    st.session_state.total_pnl = 0.0

st.sidebar.header("📝 سجل أداء الحساب")
st.sidebar.metric("إجمالي الربح/الخسارة", f"${st.session_state.total_pnl:.2f}")

# أزرار سريعة لتسجيل النتائج
col_p1, col_p2 = st.sidebar.columns(2)
if col_p1.button("✅ ربح صفقة"):
    st.session_state.total_pnl += 25.0
if col_p2.button("❌ خسارة صفقة"):
    st.session_state.total_pnl -= 25.0

if st.sidebar.button("🔄 تصفير السجل اليومي"):
    st.session_state.total_pnl = 0.0

st.sidebar.markdown("---")
st.sidebar.write(f"🎯 هدف التحدي (10%): $500")
progress = min(max(st.session_state.total_pnl / 500.0, 0.0), 1.0)
st.sidebar.progress(progress)

# --- 2. تحليل السوق (Logic) ---
def analyze_premium(df):
    if df is None or len(df) < 30: return None, None
    try:
        df['MA20'] = df['Close'].rolling(20).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        lp, lma, lrsi = df['Close'].iloc[-1], df['MA20'].iloc[-1], df['RSI'].iloc[-1]
        
        if lp > lma and lrsi > 62: return "Premium BUY 🚀", lp
        if lp < lma and lrsi < 38: return "Premium SELL 📉", lp
        return "صبر (انتظار الجودة) 🔄", lp
    except: return None, None

@st.cache_data(ttl=60)
def get_data(inv, per):
    try:
        d = yf.download("GC=F", period=per, interval=inv, progress=False)
        return d if not d.empty else None
    except: return None

# --- 3. الواجهة الرئيسية ---
st.title("🛡️ رادار التمويل الذكي ($5000)")

d1h, d15m = get_data("1h", "5d"), get_data("15m", "2d")
t1h, price = analyze_premium(d1h)
t15m, _ = analyze_premium(d15m)

if t1h and t15m:
    st.subheader(f"💵 سعر الذهب الحالي: ${price:,.2f}")
    
    # شرط الجودة: توافق الفريمات
    if "Premium" in t1h and "Premium" in t15m and t1h[:4] == t15m[:4]:
        st.success("🔥 إشارة ذهبية: توافق تام بين فريم الساعة والـ 15 دقيقة")
        
        sl_pts, tp_pts = 4.0, 7.5
        lot_size = 25.0 / (sl_pts * 10)
        
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"### الاتجاه: {t1h}\n\n📍 الدخول: {price:.2f}\n\n✅ الهدف: {price+(tp_pts if 'BUY' in t1h else -tp_pts):.2f}\n\n🛑 الوقف: {price-(sl_pts if 'BUY' in t1h else -sl_pts):.2f}")
        with c2:
            st.warning(f"📏 حجم اللوت المقترح:\n## {lot_size:.2f}")
            st.write(f"المخاطرة: $25 (0.5%) | الربح المتوقع: $47 (0.9%)")
    else:
        st.warning("🔄 وضع الصبر: الاتجاهات غير متوافقة حالياً. لا تخاطر بحساب التمويل.")
else:
    st.info("📊 جاري تحديث البيانات...")
