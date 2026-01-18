import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات الحساب (Funded Pips - 5000$)
ACCOUNT_SIZE = 5000.0
DAILY_TARGET_PCT = 1.5  # هدف الربح اليومي المتوسط
DAILY_LOSS_LIMIT_PCT = 1.0 # حد الخسارة اليومي الأقصى
RISK_PER_TRADE_PCT = 0.5 # المخاطرة لكل صفقة (لضمان الجودة)

st.set_page_config(page_title="Funded Pips Pro", page_icon="🛡️", layout="wide")

# --- وظيفة الجلسات العالمية ---
def get_market_sessions():
    now = datetime.datetime.now(pytz.utc)
    sessions = {"لندن 🇬🇧": (8, 17), "نيويورك 🇺🇸": (13, 22)}
    status = {name: ("🟢 مفتوح" if (s <= now.hour < e if s < e else now.hour >= s or now.hour < e) else "🔴 مغلق") 
              for name, (s, e) in sessions.items()}
    return status, now

# --- تحليل القناص عالي الجودة ---
def analyze_funded_pro(df):
    if df is None or len(df) < 30: return None, None
    try:
        df['MA20'] = df['Close'].rolling(20).mean()
        # حساب RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        lp, lma, lrsi = df['Close'].iloc[-1], df['MA20'].iloc[-1], df['RSI'].iloc[-1]
        
        # شروط صارمة جداً للجودة (RSI + Trend)
        if lp > lma and lrsi > 60: return "شراء قوي (Premium Buy) 🚀", lp
        if lp < lma and lrsi < 40: return "بيع قوي (Premium Sell) 📉", lp
        return "تذبذب (No Trade) 🔄", lp
    except: return None, None

@st.cache_data(ttl=60)
def get_data(intv, per):
    try:
        d = yf.download("GC=F", period=per, interval=intv, progress=False)
        return d if not d.empty else None
    except: return None

# --- واجهة التطبيق ---
st.title("🛡️ نظام إدارة حساب التمويل (5000$)")

# لوحة معلومات المخاطر في القائمة الجانبية
st.sidebar.header("📋 خطة التداول اليومية")
st.sidebar.metric("رأس المال", f"${ACCOUNT_SIZE}")
st.sidebar.success(f"الربح المستهدف (1.5%): ${ACCOUNT_SIZE * (DAILY_TARGET_PCT/100)}")
st.sidebar.error(f"حد الخسارة (1.0%): ${ACCOUNT_SIZE * (DAILY_LOSS_LIMIT_PCT/100)}")

st.sidebar.divider()
st.sidebar.info("💡 نصيحة: صفقة واحدة ناجحة بهدف 65 نقطة ومخاطرة 0.5% تحقق لك هدفك اليومي.")

sessions, cur_time = get_market_sessions()
for n, s in sessions.items(): st.sidebar.write(f"{n}: {s}")

# جلب البيانات والتحليل
d1h = get_data("1h", "5d")
d15m = get_data("15m", "2d")
t1h, price = analyze_funded_pro(d1h)
t15m, _ = analyze_funded_pro(d15m)

if t1h and t15m:
    st.subheader(f"💰 سعر الذهب المباشر: ${price:,.2f}")
    
    # فلترة الصفقات (الجودة الفائقة)
    if "قوي" in t1h and "قوي" in t15m and t1h[:2] == t15m[:2]:
        st.success("✅ صفقة عالية الجودة مطابقة لشروط التمويل")
        
        # حساب إدارة المخاطر بدقة
        sl_pips = 4.0 # 40 نقطة وقف
        tp_pips = 7.0 # 70 نقطة هدف (لتحقيق أكثر من 1.5% ربح)
        
        risk_dollar = ACCOUNT_SIZE * (RISK_PER_TRADE_PCT / 100)
        # لوت الذهب: (المخاطرة بالدولار) / (نقاط الوقف * 10)
        suggested_lot = risk_dollar / (sl_pips * 10)
        
        col1, col2 = st.columns(2)
        if "شراء" in t1h:
            col1.markdown(f"### 🟢 الاتجاه: شراء (BUY)\n**السعر الحالي:** {price:.2f}")
            st.info(f"🎯 **الهدف (TP):** {price + tp_pips:.2f} | 🛑 **الوقف (SL):** {price - sl_pips:.2f}")
        else:
            col1.markdown(f"### 🔴 الاتجاه: بيع (SELL)\n**السعر الحالي:** {price:.2f}")
            st.info(f"🎯 **الهدف (TP):** {price - tp_pips:.2f} | 🛑 **الوقف (SL):** {price + sl_pips:.2f}")
            
        with col2:
            st.warning(f"📏 **حجم اللوت المقترح (Lot Size):**\n## {suggested_lot:.2f}")
            st.write(f"المخاطرة في هذه الصفقة: ${risk_dollar} (0.5%)")

    else:
        st.warning("🔄 **وضع المراقبة:** لا توجد صفقات 'Premium' حالياً. الحفاظ على الحساب هو الربح الحقيقي.")
else:
    st.info("📊 جاري تحليل البيانات.. الإشارات تظهر فور توافق الفريمات.")

st.caption(f"توقيت النظام: {cur_time.strftime('%H:%M:%S')} UTC")
