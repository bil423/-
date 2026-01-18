import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات حساب التمويل ($5000)
ACCOUNT_SIZE = 5000.0
DAILY_TARGET_PCT = 1.5  # هدف الربح اليومي
RISK_PER_TRADE = 0.5   # المخاطرة للصفقة الواحدة (25$)

st.set_page_config(page_title="Funded Sniper Pro", page_icon="📈", layout="wide")

# --- إدارة الجلسات ---
def get_sessions():
    now = datetime.datetime.now(pytz.utc)
    london = "🟢 مفتوحة" if 8 <= now.hour < 17 else "🔴 مغلقة"
    return london, now

# --- تحليل الصفقات عالية الجودة ---
def analyze_market(df):
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
        return "صبر 🔄", lp
    except: return None, None

@st.cache_data(ttl=60)
def fetch_data(inv, per):
    try:
        d = yf.download("GC=F", period=per, interval=inv, progress=False)
        return d if not d.empty else None
    except: return None

# --- واجهة المستخدم وسجل الأرباح ---
st.title("🛡️ رادار التمويل الذكي ($5000)")

# لوحة تتبع الأرباح في الشريط الجانبي
st.sidebar.header("📝 سجل أرباح التحدي")
if 'total_profit' not in st.session_state:
    st.session_state.total_profit = 0.0

st.sidebar.metric("إجمالي الربح المحقق", f"${st.session_state.total_profit:.2f}")
progress = min(st.session_state.total_profit / (ACCOUNT_SIZE * 0.10), 1.0) # افتراض هدف التحدي 10%
st.sidebar.write(f"التقدم نحو هدف التحدي (10%):")
st.sidebar.progress(progress)

if st.sidebar.button("➕ إضافة ربح صفقة ($25)"):
    st.session_state.total_profit += 25.0
if st.sidebar.button("➖ تسجيل خسارة صفقة ($25)"):
    st.session_state.total_profit -= 25.0
if st.sidebar.button("🔄 تصفير السجل"):
    st.session_state.total_profit = 0.0

# التحليل المباشر
london_st, cur_time = get_sessions()
st.sidebar.write(f"توقيت النظام: {cur_time.strftime('%H:%M:%S')} UTC")

d1h, d15m = fetch_data("1h", "5d"), fetch_data("15m", "2d")
t1h, price = analyze_market(d1h)
t15m, _ = analyze_market(d15m)

if t1h and t15m:
    st.subheader(f"💵 سعر الذهب الحالي: ${price:,.2f}")
    if "Premium" in t1h and "Premium" in t15m and t1h[:4] == t15m[:4]:
        st.success("✅ فرصة 'قناص' متوافقة - جودة عالية")
        sl_pts, tp_pts = 4.0, 7.5
        risk_val = 25.0
        lot_size = risk_val / (sl_pts * 10)
        
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"### الاتجاه: {t1h}\n🎯 الهدف: {price+(tp_pts if 'BUY' in t1h else -tp_pts):.2f}\n🛑 الوقف: {price-(sl_pts if 'BUY' in t1h else -sl_pts):.2f}")
        with c2:
            st.warning(f"📏 لوت التداول: {lot_size:.2f}\n💰 الربح المتوقع: ${risk_val * (tp_pts/sl_pts):.1f}")
    else:
        st.warning("🔄 وضع الصبر: بانتظار توافق الفريمات لضمان الجودة.")
else:
    st.info("📊 جاري تحديث البيانات...")
