import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات الحساب والأهداف (حساب 5000$)
ACCOUNT_SIZE = 5000.0
DAILY_TARGET_PCT = 1.5  # هدف الربح اليومي
RISK_PER_TRADE_PCT = 0.5 # المخاطرة لكل صفقة (للحفاظ على الحساب)

st.set_page_config(page_title="Funded Sniper Pro", page_icon="🛡️", layout="wide")

# --- وظيفة الجلسات ---
def get_sessions():
    now = datetime.datetime.now(pytz.utc)
    sessions = {"لندن 🇬🇧": (8, 17), "نيويورك 🇺🇸": (13, 22)}
    status = {name: ("🟢 مفتوح" if (s <= now.hour < e if s < e else now.hour >= s or now.hour < e) else "🔴 مغلق") 
              for name, (s, e) in sessions.items()}
    return status, now

# --- التحليل الفني فائق الجودة ---
def analyze_premium_signal(df):
    if df is None or len(df) < 30: return None, None, None
    try:
        # المتوسط المتحرك
        df['MA20'] = df['Close'].rolling(20).mean()
        # حساب RSI بدقة
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        lp, lma, lrsi = df['Close'].iloc[-1], df['MA20'].iloc[-1], df['RSI'].iloc[-1]
        
        # فلتر الجودة الصارم: RSI بين 40 و 60 منطقة حيادية
        if lp > lma and lrsi > 60: return "شراء قوي (Premium Buy) 🚀", lp, lrsi
        if lp < lma and lrsi < 40: return "بيع قوي (Premium Sell) 📉", lp, lrsi
        return "انتظار (No Setup) 🔄", lp, lrsi
    except:
        return None, None, None

@st.cache_data(ttl=60)
def get_data(intv, per):
    try:
        d = yf.download("GC=F", period=per, interval=intv, progress=False)
        return d if not d.empty else None
    except: return None

# --- واجهة المستخدم ---
st.title("🛡️ رادار حساب التمويل ($5000)")

# لوحة المعلومات الجانبية
st.sidebar.header("📊 خطة الإدارة")
st.sidebar.metric("رأس المال", f"${ACCOUNT_SIZE}")
st.sidebar.success(f"الهدف اليومي: ${ACCOUNT_SIZE * (DAILY_TARGET_PCT/100)}")
st.sidebar.error("🚨 أقصى خسارة للجلسة: 3 صفقات")

sessions, cur_time = get_sessions()
for n, s in sessions.items(): st.sidebar.write(f"{n}: {s}")

# جلب البيانات
d1h, d15m = get_data("1h", "5d"), get_data("15m", "2d")
t1h, price, rsi1h = analyze_premium_signal(d1h)
t15m, _, rsi15m = analyze_premium_signal(d15m)

if t1h and t15m:
    st.subheader(f"💵 سعر الذهب الآن: ${price:,.2f}")
    
    # التحقق من "الجودة قبل الكمية"
    if "قوي" in t1h and "قوي" in t15m and t1h[:2] == t15m[:2]:
        st.success("✅ صفقة 'قناص' متوافقة مع شروط التمويل")
        
        # حساب إدارة المخاطر (TP 70 pips / SL 40 pips)
        sl_points = 4.0 # 40 نقطة
        risk_dollar = ACCOUNT_SIZE * (RISK_PER_TRADE_PCT / 100) # 25$
        suggested_lot = risk_dollar / (sl_points * 10) # حاسبة لوت الذهب
        
        col1, col2 = st.columns(2)
        with col1:
            color = "green" if "شراء" in t1h else "red"
            st.markdown(f"### <span style='color:{color}'>نوع الصفقة: {t1h[:4]}</span>", unsafe_allow_html=True)
            target = price + 7.0 if "شراء" in t1h else price - 7.0
            stop = price - 4.0 if "شراء" in t1h else price + 4.0
            st.info(f"📍 الدخول: {price:.2f} | ✅ الهدف: {target:.2f} | ❌ الوقف: {stop:.2f}")
        
        with col2:
            st.warning(f"📏 حجم اللوت (Lot Size):\n## {suggested_lot:.2f}")
            st.write(f"المخاطرة: ${risk_dollar} (0.5%)")
    else:
        st.warning("🔄 بانتظار فرصة عالية الجودة (توافق فريم الساعة مع 15 دقيقة وزخم RSI).")
else:
    st.info("📊 جاري تحليل البيانات.. الإشارات تظهر فور افتتاح السوق وتوافق المؤشرات.")

st.caption(f"آخر تحديث: {cur_time.strftime('%H:%M:%S')} UTC")
