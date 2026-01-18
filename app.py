import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import datetime

# إعدادات واجهة الجوال
st.set_page_config(page_title="AI Gold Signal", page_icon="🟡", layout="centered")

# تصميم الواجهة (CSS) لجعلها تبدو كالتطبيقات
st.markdown("""
    <style>
    .main { text-align: center; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #f0c040; color: black; }
    .signal-box { padding: 20px; border-radius: 15px; text-align: center; font-size: 25px; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🟡 رادار الذهب الذكي")
st.write("تحليل لحظي لزوج XAU/USD")

# وظيفة جلب وتحليل البيانات
@st.cache_data(ttl=300) # تحديث كل 5 دقائق
def get_ai_prediction():
    # جلب بيانات الذهب
    df = yf.download("GC=F", period="5d", interval="15m") # فريم 15 دقيقة للمضاربة
    
    # هندسة الميزات (الذكاء الاصطناعي يقرأ هذه المؤشرات)
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['RSI'] = 100 - (100 / (1 + df['Close'].pct_change().rolling(14).mean()))
    
    # هدف التعلم (هل الشمعة القادمة صاعدة؟)
    df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df.dropna(inplace=True)
    
    # تدريب النموذج
    features = ['Open', 'High', 'Low', 'Close', 'MA10', 'MA20', 'RSI']
    X = df[features]
    y = df['Target']
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # التوقع لأحدث نقطة
    last_point = X.tail(1)
    prob = model.predict_proba(last_point)[0] # نسبة التأكد
    pred = model.predict(last_point)[0]
    
    return pred, prob, df['Close'].iloc[-1]

# تنفيذ التحليل
try:
    prediction, probability, current_price = get_ai_prediction()

    # عرض السعر الحالي
    st.metric(label="سعر الذهب الحالي (Ounces)", value=f"${current_price:,.2f}")

    # عرض الإشارة بشكل جذاب
    if prediction == 1:
        st.markdown(f'<div class="signal-box" style="background-color: #d4edda; color: #155724; border: 2px solid #c3e6cb;">🚀 إشارة شراء (BUY)<br><small>نسبة التوقع: {max(probability)*100:.1f}%</small></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="signal-box" style="background-color: #f8d7da; color: #721c24; border: 2px solid #f5c6cb;">📉 إشارة بيع (SELL)<br><small>نسبة التوقع: {max(probability)*100:.1f}%</small></div>', unsafe_allow_html=True)

    # معلومات إضافية
    with st.expander("🔍 تفاصيل التحليل الفني"):
        st.write("النموذج المستخدم: Random Forest Classifier")
        st.write("الفريم الزمني: 15 دقيقة (مضاربة)")
        st.info("الذكاء الاصطناعي يحلل الآن المتوسطات المتحركة (MA) وقوة الزخم (RSI) لاتخاذ القرار.")

except Exception as e:
    st.error("عذراً، هناك مشكلة في جلب بيانات السوق حالياً. حاول لاحقاً.")

st.caption(f"آخر تحديث: {datetime.datetime.now().strftime('%H:%M:%S')}")
