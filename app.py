import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات حساب التمويل الصارمة (Funded Pips - 5000$)
ACCOUNT_SIZE = 5000.0
DAILY_TARGET_MIN = 1.0  # ربح 1% ($50)
DAILY_TARGET_MAX = 2.0  # ربح 2% ($100)
RISK_PER_TRADE = 0.5   # مخاطرة 0.5% ($25)

st.set_page_config(page_title="Funded Sniper Pro", page_icon="🛡️", layout="wide")

# --- إدارة الجلسات ---
def get_sessions():
    now = datetime.datetime.now(pytz.utc)
    sessions = {"لندن 🇬🇧 (هدفك)": (8, 17), "نيويورك 🇺🇸": (13, 22)}
    status = {name: ("🟢 مفتوح" if (s <= now.hour < e if s < e else now.hour >= s or now.hour < e) else "🔴 مغلق") 
              for name, (s, e) in sessions.items()}
    return status, now

# --- فلتر الجودة الفائقة (Premium Entry) ---
def analyze_premium(df):
    if df is None or len(df) < 30: return None, None
    try:
        # المتوسطات والزخم
        df['MA20'] = df['Close'].rolling(20).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        lp, lma, lrsi = df['Close'].iloc[-1], df['MA20'].iloc[-1], df['RSI'].iloc[-1]
        
        # شروط دخول "صفوة الصفقات"
        if lp > lma and lrsi > 62: return "Premium BUY 🚀", lp
        if lp < lma and lrsi < 38: return "Premium SELL 📉", lp
        return "Waiting for Quality 🔄", lp
    except: return None, None

@st.cache_data(ttl=60)
def get_data(intv, per):
    try:
        d = yf.download("GC=F", period=per, interval=intv, progress=False)
        return d if not d.empty else None
    except: return None

# --- واجهة المستخدم ---
st.title("🛡️ رادار حساب التمويل ($5000)")

# لوحة التحكم الجانبية
st.sidebar.header("📊 أهداف الجلسة")
st.sidebar.metric("رأس المال", f"${ACCOUNT_SIZE}")
st.sidebar.success(f"هدف الربح: ${ACCOUNT_SIZE*(DAILY_TARGET_MIN/100)} - ${ACCOUNT_SIZE*(DAILY_TARGET_MAX/100)}")
st.sidebar.error(f"خسارة الصفقة: ${ACCOUNT_SIZE*(RISK_PER_TRADE/100)}")

sessions, cur_time = get_sessions()
for n, s in sessions.items(): st.sidebar.write(f"{n}: {s}")

# جلب البيانات والتحليل
d1h = get_data("1h", "5d")
d15m = get_data("15m", "2d")
t1h, price = analyze_premium(d1h)
t15m, _ = analyze_premium(d15m)

if t1h and t15m:
    st.subheader(f"💵 سعر الذهب الحالي: ${price:,.2f}")
    
    # شرط الجودة: توافق فريم الساعة مع 15 دقيقة وقوة RSI
    if "Premium" in t1h and "Premium" in t15m and t1h[:4] == t15m[:4]:
        st.success("🔥 إشارة عالية الجودة: توافق تام بين الفريمات")
        
        # حساب إدارة المخاطر (TP 75 pts / SL 40 pts)
        sl_points = 4.0 # 40 نقطة
        risk_amount = ACCOUNT_SIZE * (RISK_PER_TRADE / 100) # 25$
        lot_size = risk_amount / (sl_points * 10) 
        
        col1, col2 = st.columns(2)
        with col1:
            color = "green" if "BUY" in t1h else "red"
            st.markdown(f"### <span style='color:{color}'>{t1h}</span>", unsafe_allow_html=True)
            tp_val = price + 7.5 if "BUY" in t1h else price - 7.5
            sl_val = price - 4.0 if "BUY" in t1h else price + 4.0
            st.info(f"📍 الدخول: {price:.2f} | ✅ الهدف: {tp_val:.2f} | ❌ الوقف: {sl_val:.2f}")
        
        with col2:
            st.warning(f"📏 حجم اللوت (Lot Size):\n## {lot_size:.2f}")
            st.write(f"المخاطرة: ${risk_amount} (0.5%)")
            st.write(f"الربح المتوقع: ${risk_amount * (7.5/4.0):.1f} (1.8% تقريباً)")
    else:
        st.warning("🔄 **وضع الصبر:** لا توجد صفقات مطابقة لمعاييرك الصارمة حالياً. انتظر افتتاح لندن وتوافق الاتجاه.")
else:
    st.info("📊 جاري مراقبة السوق.. ستظهر الإشارة فور توفر " "جودة عالية " " في البيانات.")

st.caption(f"توقيت النظام: {cur_time.strftime('%H:%M:%S')} UTC")
