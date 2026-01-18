import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات الصفحة
st.set_page_config(page_title="AI Gold Multi-TF & Sessions", page_icon="🟡", layout="wide")

# --- وظيفة توقيت الجلسات ---
def get_market_sessions():
    now = datetime.datetime.now(pytz.utc)
    sessions = {
        "سيدني (Sydney)": (22, 7),
        "طوكيو (Tokyo)": (0, 9),
        "لندن (London)": (8, 17),
        "نيويورك (New York)": (13, 22)
    }
    status = {}
    for name, (start, end) in sessions.items():
        if start < end:
            is_open = start <= now.hour < end
        else:  # للجلسات التي تبدأ قبل منتصف الليل وتنتهي بعده
            is_open = now.hour >= start or now.hour < end
        status[name] = "🟢 مفتوح" if is_open else "🔴 مغلق"
    return status, now

# --- وظائف تحليل الذهب ---
def analyze_trend(df):
    if df is None or df.empty: return "بيانات غير متوفرة"
    df['MA20'] = df['Close'].rolling(20).mean()
    last_close = df['Close'].iloc[-1]
    last_ma = df['MA20'].iloc[-1]
    return "صعود 📈" if last_close > last_ma else "هبوط 📉"

@st.cache_data(ttl=60)
def get_gold_data(interval, period):
    try:
        data = yf.download("GC=F", period=period, interval=interval, progress=False)
        return data
    except: return None

# --- واجهة التطبيق ---
st.title("🟡 رادار الذهب الذكي + مواقيت الجلسات")

# قسم الجلسات العالمية
st.sidebar.header("🕒 حالة الأسواق العالمية (UTC)")
session_status, current_time = get_market_sessions()
st.sidebar.write(f"التوقيت العالمي: {current_time.strftime('%H:%M:%S')}")
for session, state in session_status.items():
    st.sidebar.write(f"{session}: {state}")

# عداد افتتاح السوق العالمي (فجر الإثنين)
if current_time.weekday() == 6: # إذا كان اليوم الأحد
    opening_time = datetime.datetime.combine(current_time.date(), datetime.time(23, 0), pytz.utc)
    time_left = opening_time - current_time
    if time_left.total_seconds() > 0:
        st.warning(f"⏳ متبقي على افتتاح السوق العالمي: {str(time_left).split('.')[0]}")

# --- التحليل الفني ---
st.subheader("🔍 تحليل الأطر الزمنية المتعددة")
col1, col2, col3 = st.columns(3)

data_1h = get_gold_data("1h", "5d")
data_15m = get_gold_data("15m", "2d")
data_5m = get_gold_data("5m", "1d")

trend_1h = analyze_trend(data_1h)
trend_15m = analyze_trend(data_15m)
trend_5m = analyze_trend(data_5m)

with col1: st.metric("إطار الساعة", trend_1h)
with col2: st.metric("إطار 15 دقيقة", trend_15m)
with col3: st.metric("إطار 5 دقائق", trend_5m)

st.divider()

# --- القرار النهائي ---
if "بيانات غير متوفرة" in [trend_1h, trend_15m]:
    st.info("📊 بانتظار سيولة السوق لعرض الإشارة النهائية...")
else:
    if trend_1h == trend_15m == trend_5m:
        if "صعود" in trend_1h:
            st.success("🚀 إشارة شراء قوية: توافق تام بين جميع الفريمات")
        else:
            st.error("📉 إشارة بيع قوية: توافق تام بين جميع الفريمات")
    elif trend_1h != trend_15m:
        st.warning("⚠️ حالة انتظار: الاتجاه العام يعاكس اتجاه المضاربة")
    else:
        st.info("🔄 تذبذب: السوق يبحث عن اتجاه واضح")

st.caption(f"تاريخ التحديث: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
