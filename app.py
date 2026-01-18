import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات الصفحة
st.set_page_config(page_title="London Sniper Gold", page_icon="🎯", layout="wide")

# --- وظيفة الجلسات العالمية ---
def get_market_sessions():
    now = datetime.datetime.now(pytz.utc)
    sessions = {
        "سيدني 🇦🇺": (22, 7),
        "طوكيو 🇯🇵": (0, 9),
        "لندن 🇬🇧 (هدفك)": (8, 17),
        "نيويورك 🇺🇸": (13, 22)
    }
    status = {}
    for name, (start, end) in sessions.items():
        is_open = start <= now.hour < end if start < end else now.hour >= start or now.hour < end
        status[name] = "🟢 مفتوح" if is_open else "🔴 مغلق"
    return status, now

# --- تحليل القناص عالي الجودة ---
def analyze_sniper(df):
    if df is None or len(df) < 30: return None, None, None
    try:
        df['MA20'] = df['Close'].rolling(20).mean()
        # حساب RSI بطريقة آمنة
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        last_price = float(df['Close'].iloc[-1])
        last_ma = float(df['MA20'].iloc[-1])
        last_rsi = float(df['RSI'].iloc[-1])
        
        if last_price > last_ma and last_rsi > 55: return "صعود قوي 🚀", last_price, last_rsi
        if last_price < last_ma and last_rsi < 45: return "هبوط قوي 📉", last_price, last_rsi
        return "تذبذب 🔄", last_price, last_rsi
    except: return None, None, None

@st.cache_data(ttl=60)
def get_gold_data(interval, period):
    try:
        data = yf.download("GC=F", period=period, interval=interval, progress=False)
        return data if not data.empty else None
    except: return None

# --- واجهة المستخدم ---
st.title("🎯 قناص الذهب - تركيز جلسة لندن")

# الشريط الجانبي لإدارة المخاطر
st.sidebar.header("🛡️ إدارة المخاطر (الصرامة)")
st.sidebar.error("🚨 حد الجلسة: 3 خسائر كحد أقصى")
st.sidebar.info("🎯 الأهداف: 50-80 نقطة | 🛑 الوقف: 30-50 نقطة")
session_status, current_time = get_market_sessions()
for s, stt in session_status.items(): st.sidebar.write(f"{s}: {stt}")

# عداد افتتاح السوق
if current_time.weekday() == 6 and current_time.hour < 23:
    opening_time = datetime.datetime.combine(current_time.date(), datetime.time(23, 0), pytz.utc)
    st.warning(f"⏳ متبقي على افتتاح السوق: {str(opening_time - current_time).split('.')[0]}")

# التحليل الفني
data_1h = get_gold_data("1h", "5d")
data_15m = get_gold_data("15m", "2d")
trend_1h, price, rsi_1h = analyze_sniper(data_1h)
trend_15m, _, rsi_15m = analyze_sniper(data_15m)

if trend_1h and trend_15m:
    st.subheader(f"💰 سعر الذهب الآن: ${price:,.2f}")
    c1, c2 = st.columns(2)
    c1.metric("الاتجاه العام (1H)", trend_1h)
    c2.metric("زخم المضاربة (15M)", trend_15m)

    st.divider()

    # شروط دخول الصفقات المدروسة (الجودة)
    if "قوي" in trend_1h and "قوي" in trend_15m and trend_1h[:2] == trend_15m[:2]:
        st.success("🔥 فرصة ذهبية عالية الجودة مطابقة للشروط!")
        tp_dist, sl_dist = 6.5, 4.0 # 65 نقطة هدف و 40 نقطة وقف
        
        if "صعود" in trend_1h:
            st.write("### 🟢 نوع الصفقة: شراء (BUY)")
            st.info(f"📍 الدخول: {price:.2f} | ✅ الهدف (TP): {price + tp_dist:.2f} | ❌ الوقف (SL): {price - sl_dist:.2f}")
        else:
            st.write("### 🔴 نوع الصفقة: بيع (SELL)")
            st.info(f"📍 الدخول: {price:.2f} | ✅ الهدف (TP): {price - tp_dist:.2f} | ❌ الوقف (SL): {price + sl_dist:.2f}")
    else:
        st.warning("🔄 حالة السوق: لا توجد صفقة متوافقة مع معايير الجودة حالياً.")
else:
    st.info("📊 بانتظار تحرك الأسعار عند افتتاح الجلسة لعرض الصفقات...")

st.caption(f"تحديث: {current_time.strftime('%H:%M:%S')} UTC")
