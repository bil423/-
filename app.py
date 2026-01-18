import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz

# إعدادات الحساب (Funded Pips - 5000$)
ACCOUNT_SIZE = 5000.0
DAILY_GOAL_PCT = 1.5   # هدف الربح اليومي
RISK_PER_TRADE = 0.5   # المخاطرة لكل صفقة (25$)

st.set_page_config(page_title="Prop Sniper 5K", page_icon="🛡️", layout="wide")

# --- إدارة الجلسات ---
def get_sessions():
    now = datetime.datetime.now(pytz.utc)
    # جلسة لندن هي هدفنا الرئيسي
    london_start, london_end = 8, 17 
    is_london = "🟢 مفتوح الآن" if london_start <= now.hour < london_end else "🔴 مغلق حالياً"
    return is_london, now

# --- تحليل الجودة الفائقة (Premium Filter) ---
def analyze_market(df):
    if df is None or len(df) < 30: return None, None
    try:
        # حساب المتوسط المتحرك MA20
        df['MA20'] = df['Close'].rolling(20).mean()
        # حساب RSI بطريقة مستقرة برمجياً
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        last_price = float(df['Close'].iloc[-1])
        last_ma = float(df['MA20'].iloc[-1])
        last_rsi = float(df['RSI'].iloc[-1])
        
        # شروط صارمة للجودة (Premium)
        if last_price > last_ma and last_rsi > 62: return "Premium BUY 🚀", last_price
        if last_price < last_ma and last_rsi < 38: return "Premium SELL 📉", last_price
        return "Waiting for Setup 🔄", last_price
    except:
        return None, None

@st.cache_data(ttl=60)
def fetch_gold_data(interval, period):
    try:
        data = yf.download("GC=F", period=period, interval=interval, progress=False)
        return data if not data.empty else None
    except: return None

# --- واجهة التطبيق ---
st.title("🛡️ رادار حساب التمويل ($5000)")

# لوحة المعلومات الجانبية
st.sidebar.header("📊 خطة التداول اليومية")
st.sidebar.metric("رأس المال", f"${ACCOUNT_SIZE}")
st.sidebar.success(f"الهدف اليومي: ${ACCOUNT_SIZE * (DAILY_GOAL_PCT/100)}")
st.sidebar.error(f"خسارة الصفقة: ${ACCOUNT_SIZE * (RISK_PER_TRADE/100)}")

london_status, cur_time = get_sessions()
st.sidebar.write(f"جلسة لندن 🇬🇧: {london_status}")

# التحليل
data_1h = fetch_gold_data("1h", "5d")
data_15m = fetch_gold_data("15m", "2d")
trend_1h, price = analyze_market(data_1h)
trend_15m, _ = analyze_market(data_15m)

if trend_1h and trend_15m:
    st.subheader(f"💵 سعر الذهب الحالي: ${price:,.2f}")
    
    # شرط "الجودة لا الكمية": توافق الساعة مع 15 دقيقة
    if "Premium" in trend_1h and "Premium" in trend_15m and trend_1h[:4] == trend_15m[:4]:
        st.success("🎯 فرصة عالية الجودة متوافقة مع شروط التمويل")
        
        # حساب إدارة المخاطر (TP 75 pts / SL 40 pts)
        sl_points = 4.0  # 40 نقطة
        tp_points = 7.5  # 75 نقطة
        risk_dollar = ACCOUNT_SIZE * (RISK_PER_TRADE / 100)
        lot_size = risk_dollar / (sl_points * 10) # لوت الذهب التقريبي
        
        col1, col2 = st.columns(2)
        with col1:
            trade_type = "شراء (BUY)" if "BUY" in trend_1h else "بيع (SELL)"
            st.info(f"### نوع الصفقة: {trade_type}")
            entry = price
            tp = price + tp_points if "BUY" in trend_1h else price - tp_points
            sl = price - sl_points if "BUY" in trend_1h else price + sl_points
            st.write(f"📍 الدخول: {entry:.2f}\n\n✅ الهدف: {tp:.2f}\n\n❌ الوقف: {sl:.2f}")
            
        with col2:
            st.warning(f"📏 حجم اللوت (Lot Size):\n## {lot_size:.2f}")
            st.write(f"المخاطرة: ${risk_dollar} (0.5%)")
            st.write(f"الربح المتوقع: ${risk_dollar * (tp_points/sl_points):.1f} (1.8%)")
    else:
        st.warning("🔄 **وضع الصبر:** لا توجد صفقات 'Premium' حالياً. الحفاظ على الحساب هو الأولوية.")
else:
    st.info("⏳ بانتظار تحديث البيانات عند افتتاح السوق...")

st.caption(f"تحديث النظام: {cur_time.strftime('%H:%M:%S')} UTC")
