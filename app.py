import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات الصفحة والواجهة
st.set_page_config(page_title="Gold AI Pro", page_icon="🟡", layout="wide")

# --- وظيفة توقيت الجلسات العالمية ---
def get_market_sessions():
    now = datetime.datetime.now(pytz.utc)
    sessions = {
        "سيدني 🇦🇺": (22, 7),
        "طوكيو 🇯🇵": (0, 9),
        "لندن 🇬🇧": (8, 17),
        "نيويورك 🇺🇸": (13, 22)
    }
    status = {}
    for name, (start, end) in sessions.items():
        if start < end:
            is_open = start <= now.hour < end
        else:
            is_open = now.hour >= start or now.hour < end
        status[name] = "🟢 مفتوح" if is_open else "🔴 مغلق"
    return status, now

# --- تحليل الاتجاه بأمان (معالجة الأخطاء) ---
def analyze_trend(df):
    if df is None or len(df) < 20: 
        return "في انتظار البيانات..."
    try:
        # حساب المتوسط المتحرك
        ma20 = df['Close'].rolling(window=20).mean()
        last_close = float(df['Close'].iloc[-1])
        last_ma = float(ma20.iloc[-1])
        
        if last_close > last_ma:
            return "صعود 📈"
        else:
            return "هبوط 📉"
    except Exception:
        return "جاري التحليل..."

@st.cache_data(ttl=60)
def get_gold_data(interval, period):
    try:
        data = yf.download("GC=F", period=period, interval=interval, progress=False)
        return data if not data.empty else None
    except:
        return None

# --- واجهة التطبيق ---
st.title("🟡 رادار الذهب الذكي + مواقيت الجلسات")

# قسم الجلسات في القائمة الجانبية
st.sidebar.header("🕒 الأسواق العالمية (UTC)")
session_status, current_time = get_market_sessions()
st.sidebar.write(f"الوقت الحالي: {current_time.strftime('%H:%M:%S')}")
for session, state in session_status.items():
    st.sidebar.write(f"{session}: {state}")

# عداد افتتاح السوق العالمي (يظهر يوم الأحد فقط)
if current_time.weekday() == 6: 
    opening_time = datetime.datetime.combine(current_time.date(), datetime.time(23, 0), pytz.utc)
    time_left = opening_time - current_time
    if time_left.total_seconds() > 0:
        st.warning(f"⏳ متبقي على افتتاح بورصة الذهب: {str(time_left).split('.')[0]}")
    else:
        st.success("🔓 السوق يفتتح الآن.. جاري جلب البيانات")

# --- جلب البيانات والتحليل للفريمات المطلوبة ---
st.subheader("🔍 تحليل الأطر الزمنية المتعددة")
col1, col2, col3 = st.columns(3)

# جلب البيانات للأطر الزمنية المختلفة
data_1h = get_gold_data("1h", "5d")
data_15m = get_gold_data("15m", "2d")
data_5m = get_gold_data("5m", "1d")

# إجراء التحليل
trend_1h = analyze_trend(data_1h)
trend_15m = analyze_trend(data_15m)
trend_5m = analyze_trend(data_5m)

with col1: st.metric("إطار الساعة (الترند العام)", trend_1h)
with col2: st.metric("إطار 15 دقيقة (المضاربة)", trend_15m)
with col3: st.metric("إطار 5 دقائق (الدخول)", trend_5m)

st.divider()

# --- القرار النهائي للذكاء الاصطناعي ---
st.subheader("🤖 قرار الروبوت النهائي")

if "انتظار" in trend_1h or data_1h is None:
    st.info("📊 السوق مغلق حالياً. الإشارات ستبدأ بالظهور فور تحرك الأسعار عند افتتاح البورصة.")
else:
    # منطق توافق الفريمات
    if trend_1h == trend_15m == trend_5m:
        if "صعود" in trend_1h:
            st.success("🚀 إشارة شراء قوية: جميع الفريمات متوافقة نحو الصعود")
        else:
            st.error("📉 إشارة بيع قوية: جميع الفريمات متوافقة نحو الهبوط")
    elif trend_1h != trend_15m:
        st.warning("⚠️ وضع الانتظار: الاتجاه العام (ساعة) يعاكس اتجاه المضاربة. لا تدخل صفقات الآن.")
    else:
        st.info("🔄 تذبذب: يوجد اختلاف بسيط في الفريمات، يفضل الانتظار.")

st.caption(f"تاريخ التحديث: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
