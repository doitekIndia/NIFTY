# app.py - NIFTY50 Fibonacci Scanner for Streamlit Cloud
import streamlit as st
import yfinance as yf
import pandas as pd
import threading
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Page config
st.set_page_config(page_title="NIFTY50 Fibonacci Scanner", layout="wide")

# Global state
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = []
if 'backtest_running' not in st.session_state:
    st.session_state.backtest_running = False
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False

email_recipients = ["xmlkeyserver@gmail.com", "nitinplus@gmail.com"]

def safe_float(value):
    try:
        if pd.isna(value) or value is None: return None
        if hasattr(value, 'iloc'): return float(value.iloc[0]) if len(value) > 0 else None
        return float(value)
    except: return None

@st.cache_data
def get_nifty_daily_data():
    ticker = yf.Ticker('^NSEI')
    data = ticker.history(period="1mo")
    data.index = data.index.tz_localize(None)
    data = data.dropna()
    st.info(f"✅ Loaded {len(data)} days | Latest: {data.index[-1].strftime('%Y-%m-%d')}")
    return data.tail(25)

def send_email(recipients, symbol, signals):
    sender_email = st.secrets["email"]["sender"]
    sender_password = st.secrets["email"]["app_password"]
    
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        
        subject = f"🚨 NIFTY50 FIBONACCI: {symbol}"
        
        if symbol == "BACKTEST-REPORT":
            triggers = [r for r in st.session_state.backtest_results if r['trigger'] == 'TRIGGER']
            total_days = len(st.session_state.backtest_results)
            hit_rate = (len(triggers) / total_days * 100) if total_days > 0 else 0
            
            body = f"""🔥 NIFTY50 FIBONACCI BACKTEST REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}
📊 Period: {st.session_state.backtest_results[0]['date']} → {st.session_state.backtest_results[-1]['date']}
🎯 Triggers: {len(triggers)} / {total_days} days
📈 Hit Rate: {hit_rate:.1f}%"""
            
            for trigger in triggers[-5:]:
                body += f"\n🔔 {trigger['date']} | Buy 50%: ₹{trigger['buy_50']} | SL: ₹{trigger['sl']}"
                
        else:
            body = f"""🔥 NIFTY50 LIVE TRADING ALERT
📅 {datetime.now().strftime('%Y-%m-%d %H:%M IST')}
📈 Buy 50%: ₹{signals.get('buy_50', 0):,.0f}
🛑 SL: ₹{signals.get('sl', 0):,.0f}
🎯 T1: ₹{signals.get('target1', 0):,.0f}"""
        
        for recipient in recipients:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = recipient
            server.send_message(msg)
        
        server.quit()
        st.success(f"✅ Email sent to {len(recipients)} recipients")
        return True
    except Exception as e:
        st.error(f"❌ Email error: {str(e)}")
        return False

def run_historical_backtest():
    if st.session_state.backtest_running:
        st.warning("⏳ Backtest already running...")
        return
    
    st.session_state.backtest_running = True
    st.session_state.backtest_results.clear()
    
    with st.spinner("🔥 Running NIFTY50 Backtest..."):
        data = get_nifty_daily_data()
        
        if len(data) < 10:
            st.error("❌ Insufficient data")
            st.session_state.backtest_running = False
            return
        
        signals_found = 0
        for i in range(len(data)-1, 0, -1):
            today_date = data.index[i].strftime('%m/%d')
            today_open = safe_float(data['Open'].iloc[i])
            yest_low = safe_float(data['Low'].iloc[i-1])
            yest_high = safe_float(data['High'].iloc[i-1])
            
            if today_open is None or yest_low is None or yest_high is None:
                continue
            
            case1 = "YES" if today_open > yest_low else "NO"
            range_size = today_open - yest_low
            
            if range_size <= 0:
                result = {
                    'date': today_date, 'today_open': f"{today_open:.0f}",
                    'yest_low': f"{yest_low:.0f}", 'yest_high': f"{yest_high:.0f}",
                    'case1': case1, 'acceptance': 'NO', 'trigger': 'NO TRADE'
                }
                st.session_state.backtest_results.append(result)
                continue
            
            buy_618 = yest_low + 0.618 * range_size
            buy_50 = yest_low + 0.5 * range_size
            buy_382 = yest_low + 0.382 * range_size
            
            acceptance = "YES" if (yest_low <= buy_618 <= yest_high and yest_low <= buy_50 <= yest_high) else "NO"
            trigger = "TRIGGER" if case1 == "YES" and acceptance == "YES" else "NO TRADE"
            
            result = {
                'date': today_date, 'today_open': f"{today_open:.2f}",
                'yest_low': f"{yest_low:.1f}", 'yest_high': f"{yest_high:.1f}",
                'case1': case1, 'acceptance': acceptance, 'trigger': trigger,
                'buy_50': f"{buy_50:.3f}", 'sl': f"{yest_low:.1f}", 'target1': f"{today_open + 0.382 * range_size:.2f}"
            }
            
            st.session_state.backtest_results.append(result)
            if trigger == "TRIGGER":
                signals_found += 1
        
        st.session_state.backtest_running = False
        st.success(f"✅ Backtest complete: {signals_found} triggers found!")

# --- DASHBOARD ---
st.title("🚀 NIFTY50 Fibonacci Scanner")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🔄 Run Backtest", use_container_width=True):
        threading.Thread(target=run_historical_backtest, daemon=True).start()

with col2:
    if st.button("📧 Test Email", use_container_width=True):
        signals = {'buy_50': 25850, 'sl': 25750, 'target1': 25950}
        threading.Thread(target=send_email, args=(email_recipients, 'LIVE-TEST', signals), daemon=True).start()

with col3:
    if st.button("📊 Send Report", use_container_width=True) and st.session_state.backtest_results:
        threading.Thread(target=send_email, args=(email_recipients, "BACKTEST-REPORT", {}), daemon=True).start()

# Results table
if st.session_state.backtest_results:
    df = pd.DataFrame(st.session_state.backtest_results[-20:])
    st.subheader("📈 Backtest Results (Last 20 Days)")
    st.dataframe(df[['date', 'today_open', 'yest_low', 'case1', 'trigger', 'buy_50', 'sl', 'target1']], 
                use_container_width=True, hide_index=True)
    
    # Metrics
    triggers = len([r for r in st.session_state.backtest_results if r['trigger'] == 'TRIGGER'])
    hit_rate = (triggers / len(st.session_state.backtest_results)) * 100
    col1, col2, col3 = st.columns(3)
    col1.metric("🎯 Triggers", triggers)
    col2.metric("📊 Hit Rate", f"{hit_rate:.1f}%")
    col3.metric("📅 Days Analyzed", len(st.session_state.backtest_results))
else:
    st.info("👆 Click **Run Backtest** to start analysis")
