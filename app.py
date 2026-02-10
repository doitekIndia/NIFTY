# app.py (rename from niftycall.py) - Streamlit Cloud READY
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import threading
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="NIFTY50 Scanner", layout="wide")

# Session state
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = []
if 'backtest_running' not in st.session_state:
    st.session_state.backtest_running = False

email_recipients = ["xmlkeyserver@gmail.com", "nitinplus@gmail.com"]

@st.cache_data
def get_nifty_data():
    ticker = yf.Ticker('^NSEI')
    data = ticker.history(period="1mo").tail(25)
    data.index = data.index.tz_localize(None)
    return data.dropna()

def send_email(symbol, signals):
    try:
        sender = st.secrets["email"]["sender"]
        password = st.secrets["email"]["app_password"]
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        
        subject = f"🚨 NIFTY50: {symbol}"
        body = f"🔥 {symbol}\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M IST')}"
        if signals:
            body += f"\nBuy 50%: ₹{signals['buy_50']}\nSL: ₹{signals['sl']}\nT1: ₹{signals['target1']}"
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ", ".join(email_recipients)
        
        server.send_message(msg)
        server.quit()
        st.success("✅ Email sent!")
    except Exception as e:
        st.error(f"❌ {e}")

def run_backtest():
    if st.session_state.backtest_running:
        st.warning("⏳ Running...")
        return
        
    st.session_state.backtest_running = True
    st.session_state.backtest_results.clear()
    
    data = get_nifty_data()
    for i in range(len(data)-1, 0, -1):
        today_open = data['Open'].iloc[i]
        yest_low = data['Low'].iloc[i-1]
        yest_high = data['High'].iloc[i-1]
        
        range_size = today_open - yest_low
        if range_size <= 0: continue
            
        buy_50 = yest_low + 0.5 * range_size
        acceptance = "YES" if yest_low <= buy_50 <= yest_high else "NO"
        trigger = "TRIGGER" if today_open > yest_low and acceptance == "YES" else "NO TRADE"
        
        result = {
            'date': data.index[i].strftime('%m/%d'),
            'open': f"{today_open:.0f}",
            'buy_50': f"{buy_50:.0f}",
            'sl': f"{yest_low:.0f}",
            'trigger': trigger
        }
        st.session_state.backtest_results.append(result)
    
    st.session_state.backtest_running = False
    st.rerun()

# UI
st.title("🚀 NIFTY50 Fibonacci Scanner")

col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 Run Backtest"):
        threading.Thread(target=run_backtest, daemon=True).start()

with col2:
    if st.button("📧 Test Email"):
        send_email("TEST", {'buy_50': 25850, 'sl': 25750, 'target1': 25950})

if st.session_state.backtest_results:
    df = pd.DataFrame(st.session_state.backtest_results[-20:])
    st.dataframe(df, use_container_width=True)
    
    triggers = len(df[df.trigger == 'TRIGGER'])
    st.metric("🎯 Triggers", triggers, f"{triggers/len(df)*100:.1f}%")
