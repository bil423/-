import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات حساب Funded Pips (5000$)
ACCOUNT_SIZE = 5000.0
RISK_PER_TRADE = 0.5  # مخاطرة 25$ فقط لكل صفقة
DAILY_GOAL_PCT = 1.5  # هدف الربح 75$ يومياً

st.set_page_config(page_title="Funded Sniper Elite", page_icon="🛡️", layout="wide")

# --- مراقبة الجلسات ---
def get_sessions():
    now = datetime.datetime.now(pytz.utc)
    london_start, london_end = 8, 17
    is_london = "🟢 مفتوح" if london_start <= now.hour < london_end else "🔴 مغلق"
    return is_london, now

# --- فلتر الجودة الفائقة (The Sniper Logic) ---
def analyze_market(df):
    if df is None or len(df) < 30: return None, None
    try:
        # حساب الاتجاه (MA20) والقوة (RSI)
        df['MA20'] = df['Close'].rolling(20).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        price = float(df['Close'].iloc[-1])
        ma = float(df['MA20'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        
        # شروط دخول صارمة: اتجاه + زخم قوي (RSI > 62 أو < 38)
        if price > ma and rsi > 62: return "Premium BUY 🚀", price
        if price < ma and rsi < 38: return "Premium SELL 📉", price
        return "صبر (No High Quality Setup) 🔄", price
    except: return None, None

@st.cache_data(ttl=60)
def fetch_data(inv, per):
    try:
        d = yf.download("GC=F", period=per, interval=inv, progress=False)
        return d if not d.empty else None
    except: return None

# --- واجهة المستخدم الاحترافية ---
st.title("🛡️ رادار حساب التمويل ($5000)")

# القائمة الجانبية لإدارة المخاطر
st.sidebar.header("📋 قوانين التمويل")
st.sidebar.metric("رأس المال", f"${ACCOUNT_SIZE}")
st.sidebar.success(f"الهدف اليومي المخطط: ${ACCOUNT_SIZE * (DAILY_GOAL_PCT/100)}")
st.sidebar.error(f"المخاطرة المسموحة: ${ACCOUNT_SIZE * (RISK_PER_TRADE/100)}")

london_status, cur_time = get_sessions()
st.sidebar.info(f"جلسة لندن 🇬🇧: {london_status}")

# التحليل الفني
d1h, d15m = fetch_data("1h", "5d"), fetch_data("15m", "2d")
t1h, price = analyze_market(d1h)
t15m, _ = analyze_market(d15m)

if t1h and t15m:
    st.subheader(f"💵 سعر الذهب الحالي: ${price:,.2f}")
    
    # التحقق من توافق الفريمات (جودة الصفقة)
    if "Premium" in t1h and "Premium" in t15m and t1h[:4] == t15m[:4]:
        st.success("🎯 فرصة 'قناص' متوافقة تماماً - جودة عالية")
        
        # إدارة الأهداف (طلبك: 50-80 نقطة)
        sl_pts, tp_pts = 4.0, 7.5  # الوقف 40 نقطة والهدف 75 نقطة
        risk_val = ACCOUNT_SIZE * (RISK_PER_TRADE / 100)
        lot_size = risk_val / (sl_pts * 10) # حجم اللوت المناسب
        
        c1, c2 = st.columns(2)
        with c1:
            color = "green" if "BUY" in t1h else "red"
            st.markdown(f"### <span style='color:{color}'>{t1h}</span>", unsafe_allow_html=True)
            tp = price + tp_pts if "BUY" in t1h else price - tp_pts
            sl = price - sl_pts if "BUY" in t1h else price + sl_pts
            st.info(f"📍 الدخول: {price:.2f} | ✅ الهدف: {tp:.2f} | ❌ الوقف: {sl:.2f}")
        
        with c2:
            st.warning(f"📏 لوت التداول المقترح:\n## {lot_size:.2f}")
            st.write(f"💰 ربح الصفقة المتوقع: ${risk_val * (tp_pts/sl_pts):.1f}")
    else:
        st.warning("🔄 حالياً الحفاظ على 'Premium' وضع الصبر: لا توجد صفقات متوافقة. الأولوية لحماية الحساب.")
else:
    st.info("⏳ بانتظار استقرار البيانات وتحليل الجلسة...")

st.caption(f"تحديث النظام: {cur_time.strftime('%H:%M:%S')} UTC")
