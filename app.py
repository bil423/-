import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات حساب التمويل (Funded Pips)
ACCOUNT_SIZE = 5000.0
DAILY_TARGET_PCT = 1.5  # هدفك اليومي (نطاق 1-2%)
MAX_DAILY_LOSS_PCT = 1.0 # حد الخسارة اليومي (نطاق 0.5-1%)
RISK_PER_TRADE_PCT = 0.5 # مخاطرة الصفقة الواحدة

st.set_page_config(page_title="Prop Firm Sniper", page_icon="🛡️", layout="wide")

# --- مراقبة الجلسات العالمية ---
def get_sessions():
    now = datetime.datetime.now(pytz.utc)
    sessions = {"لندن 🇬🇧": (8, 17), "نيويورك 🇺🇸": (13, 22)}
    status = {name: ("🟢 مفتوح" if (s <= now.hour < e if s < e else now.hour >= s or now.hour < e) else "🔴 مغلق") 
              for name, (s, e) in sessions.items()}
    return status, now

# --- فلتر الجودة العالية (High Probability Setup) ---
def analyze_funded_logic(df):
    if df is None or len(df) < 30: return None, None
    try:
        df['MA20'] = df['Close'].rolling(20).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        lp, lma, lrsi = df['Close'].iloc[-1], df['MA20'].iloc[-1], df['RSI'].iloc[-1]
        
        # لا دخول إلا بزخم قوي (RSI > 60 أو < 40)
        if lp > lma and lrsi > 60: return "شراء قوي 🚀", lp
        if lp < lma and lrsi < 40: return "بيع قوي 📉", lp
        return "تذبذب 🔄", lp
    except: return None, None

@st.cache_data(ttl=60)
def get_data(intv, per):
    try:
        d = yf.download("GC=F", period=per, interval=intv, progress=False)
        return d if not d.empty else None
    except: return None

# --- واجهة نظام التمويل ---
st.title("🛡️ نظام إدارة حساب التمويل ($5000)")

# لوحة الأهداف في القائمة الجانبية
st.sidebar.header("📊 خطة العمل (Funded Pips)")
st.sidebar.metric("رأس المال", f"${ACCOUNT_SIZE}")
st.sidebar.success(f"الهدف اليومي ($): {ACCOUNT_SIZE * (DAILY_TARGET_PCT/100)}")
st.sidebar.error(f"حد الخسارة ($): {ACCOUNT_SIZE * (MAX_DAILY_LOSS_PCT/100)}")

sessions, cur_time = get_sessions()
for n, s in sessions.items(): st.sidebar.write(f"{n}: {s}")

# التحليل الفني للفريمات
d1h = get_data("1h", "5d")
d15m = get_data("15m", "2d")
t1h, price = analyze_funded_logic(d1h)
t15m, _ = analyze_funded_logic(d15m)

if t1h and t15m:
    st.subheader(f"💵 السعر المباشر: ${price:,.2f}")
    
    # شرط الجودة: توافق فريم الساعة مع 15 دقيقة
    if "قوي" in t1h and "قوي" in t15m and t1h[:2] == t15m[:2]:
        st.success("🎯 فرصة 'Premium' مطابقة لشروط التمويل")
        
        sl_pips = 4.0 # 40 نقطة (SL)
        tp_pips = 7.0 # 70 نقطة (TP) لضمان عائد أكبر من المخاطرة
        
        risk_amount = ACCOUNT_SIZE * (RISK_PER_TRADE_PCT / 100)
        suggested_lot = risk_amount / (sl_pips * 10) # حاسبة لوت الذهب
        
        col1, col2 = st.columns(2)
        with col1:
            if "شراء" in t1h:
                st.info(f"🟢 **شراء (BUY)**\n\n🎯 الهدف: {price+tp_pips:.2f}\n\n🛑 الوقف: {price-sl_pips:.2f}")
            else:
                st.info(f"🔴 **بيع (SELL)**\n\n🎯 الهدف: {price-tp_pips:.2f}\n\n🛑 الوقف: {price+sl_pips:.2f}")
        
        with col2:
            st.warning(f"📏 **حجم اللوت المقترح:**\n## {suggested_lot:.2f}")
            st.write(f"المخاطرة: ${risk_amount} لكل صفقة")
    else:
        st.warning("🔄 لا يوجد توافق عالي الجودة. الصبر هو مفتاح النجاح في التمويل.")
else:
    st.info("📊 جاري تحليل البيانات.. الإشارات تظهر فور توافق الفريمات.")

st.caption(f"توقيت النظام: {cur_time.strftime('%H:%M:%S')} UTC")
