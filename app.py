import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات الصفحة
st.set_page_config(page_title="London Gold Sniper", page_icon="🎯", layout="wide")

# --- إدارة الجلسات العالمية ---
def get_market_sessions():
    now = datetime.datetime.now(pytz.utc)
    sessions = {
        "سيدني 🇦🇺": (22, 7),
        "طوكيو 🇯🇵": (0, 9),
        "لندن 🇬🇧 (هدفك الرئيسي)": (8, 17),
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

# --- تحليل ذكي للقناص (الجودة العالية) ---
def analyze_sniper(df):
    if df is None or len(df) < 30: return None
    # حساب المتوسطات ومؤشر القوة
    df['MA20'] = df['Close'].rolling(20).mean()
    df['RSI'] = 100 - (100 / (1 + df['Close'].diff().apply(lambda x: x if x > 0 else 0).rolling(14).mean() / 
                             df['Close'].diff().apply(lambda x: -x if x < 0 else 0).rolling(14).mean()))
    
    last_price = float(df['Close'].iloc[-1])
    last_ma = float(df['MA20'].iloc[-1])
    last_rsi = float(df['RSI'].iloc[-1])
    
    # فلتر الجودة: اتجاه واضح + زخم (RSI)
    if last_price > last_ma and last_rsi > 55:
        return "صعود قوي 🚀", last_price
    elif last_price < last_ma and last_rsi < 45:
        return "هبوط قوي 📉", last_price
    return "تذبذب/انتظار 🔄", last_price

@st.cache_data(ttl=60)
def get_gold_data(interval, period):
    try:
        data = yf.download("GC=F", period=period, interval=interval, progress=False)
        return data if not data.empty else None
    except: return None

# --- واجهة التطبيق ---
st.title("🎯 قناص الذهب - تركيز جلسة لندن")

# الشريط الجانبي: القواعد الصارمة
st.sidebar.header("🛡️ قوانين الانضباط")
st.sidebar.warning("1. التداول في جلسة لندن فقط.")
st.sidebar.error("2. أقصى خسارة: 3 صفقات/جلسة.")
st.sidebar.info("3. الجودة قبل الكمية.")

session_status, current_time = get_market_sessions()
for s, stt in session_status.items():
    st.sidebar.write(f"{s}: {stt}")

# جلب بيانات الفريمات (ساعة للترند، 15 دقيقة للدخول)
data_1h = get_gold_data("1h", "5d")
data_15m = get_gold_data("15m", "2d")

res_1h = analyze_sniper(data_1h)
res_15m = analyze_sniper(data_15m)

if res_1h and res_15m:
    trend_1h, price = res_1h
    trend_15m, _ = res_15m
    
    st.subheader(f"💰 السعر الحالي: ${price:,.2f}")
    
    col1, col2 = st.columns(2)
    col1.metric("الاتجاه العام (1H)", trend_1h)
    col2.metric("تأكيد الدخول (15M)", trend_15m)

    st.divider()

    # --- منطق الدخول الصارم ---
    if "قوي" in trend_1h and "قوي" in trend_15m and trend_1h[:2] == trend_15m[:2]:
        st.success("🔥 فرصة عالية الجودة متوفرة الآن!")
        
        if "صعود" in trend_1h:
            tp = price + 6.5 # متوسط 65 نقطة
            sl = price - 4.0 # متوسط 40 نقطة
            st.write(f"### 🟢 نوع الصفقة: شراء (BUY)")
        else:
            tp = price - 6.5
            sl = price + 4.0
            st.write(f"### 🔴 نوع الصفقة: بيع (SELL)")
            
        st.info(f"📍 الدخول: {price:.2f} | ✅ الهدف (TP): {tp:.2f} | ❌ الوقف (SL): {sl:.2f}")
    else:
        st.warning("⏳ لا توجد صفقات مطابقة للمعايير حالياً. انتظر توافق الفريمات وقوة الزخم.")
else:
    st.info("📊 جاري مراقبة السوق لجلسة لندن...")

st.caption(f"توقيت النظام: {current_time.strftime('%H:%M:%S')} UTC")
