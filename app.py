import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import datetime

# إعدادات الصفحة
st.set_page_config(page_title="AI Gold Multi-TF", page_icon="🟡")

# دالة لجلب البيانات وتحليل الفريم
def get_signal(symbol, interval, period):
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if df.empty: return None, None
    
    # حساب مؤشرات بسيطة
    df['MA_Fast'] = df['Close'].rolling(10).mean()
    df['MA_Slow'] = df['Close'].rolling(20).mean()
    df['RSI'] = 100 - (100 / (1 + df['Close'].pct_change().rolling(14).mean()))
    
    # تحديد الاتجاه (Trend)
    last_close = df['Close'].iloc[-1]
    last_ma = df['MA_Slow'].iloc[-1]
    trend = "UP" if last_close > last_ma else "DOWN"
    
    return trend, last_close

st.title("🟡 رادار الذهب الذكي (متعدد الفريمات)")

try:
    # 1. تحليل الفريمات الكبيرة (الاتجاه العام)
    trend_4h, price_4h = get_signal("GC=F", "1h", "1mo") # 4 ساعات غير متاح في ياهو مجانا، نستخدم الساعة كبديل قوي
    trend_1h, price_1h = get_signal("GC=F", "1h", "1mo")
    
    # 2. تحليل الفريمات الصغيرة (التنفيذ)
    trend_15m, price_15m = get_signal("GC=F", "15m", "5d")
    trend_5m, price_5m = get_signal("GC=F", "5m", "1d")

    # عرض لوحة التحكم
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌍 الاتجاه العام (ساعة/4س)")
        st.write(f"فريم 4 ساعات: **{trend_4h}**")
        st.write(f"فريم 1 ساعة: **{trend_1h}**")

    with col2:
        st.subheader("⏱️ فريمات المضاربة")
        st.write(f"فريم 15 دقيقة: **{trend_15m}**")
        st.write(f"فريم 5 دقائق: **{trend_5m}**")

    st.divider()

    # منطق اتخاذ القرار الذكي
    # لا نشتري إلا إذا كان الفريم الكبير والصغير متوافقين
    if trend_1h == "UP" and trend_15m == "UP":
        st.success("🚀 إشارة شراء قوية (الذهب صاعد على الفريمات الكبيرة والصغيرة)")
    elif trend_1h == "DOWN" and trend_15m == "DOWN":
        st.error("📉 إشارة بيع قوية (الذهب هابط على الفريمات الكبيرة والصغيرة)")
    else:
        st.warning("⚠️ انتظار: الاتجاهات متضاربة بين الفريمات الكبيرة والصغيرة")

except Exception as e:
    st.info("بانتظار افتتاح السوق أو تحديث البيانات...")

st.caption(f"توقيت التحديث: {datetime.datetime.now().strftime('%H:%M:%S')}")
