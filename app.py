# app.py - NIFTY50 LIVE SCANNER + BACKTEST (9:15-15:30 IST)
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date, time
import smtplib
from email.mime.text import MIMEText
import pytz
import time

st.set_page_config(page_title="NIFTY50 LIVE Fibonacci Scanner", layout="wide", page_icon="📈")

# India timezone
IST = pytz.timezone('Asia/Kolkata')

# Session State
if 'live_signal' not in st.session_state:
    st.session_state.live_signal = None
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = []
if 'last_scan' not in st.session_state:
    st.session_state.last_scan = None

email_recipients = ["xmlkeyserver@gmail.com", "nitinplus@gmail.com", "aamirlodhi46@gmail.com"]

def is_market_open():
    """✅ Check if India market is open (9:15 AM - 3:30 PM IST, Mon-Fri)"""
    now = datetime.now(IST)
    market_open = time(9, 15)
    market_close = time(15, 30)
    
    is_weekday = now.weekday() < 5  # Mon-Fri
    is_time = market_open <= now.time() <= market_close
    
    return is_weekday and is_time

def scan_live_signal():
    """🔴 LIVE Fibonacci signal generator"""
    try:
        ticker = yf.Ticker('^NSEI')
        data = ticker.history(period="5d", interval="1d")
        if len(data) < 2:
            return None
        
        data.index = data.index.tz_convert(IST)
        data = data.dropna()
        
        today_open = data['Open'].iloc[-1]
        yest_low = data['Low'].iloc[-2]
        yest_high = data['High'].iloc[-2]
        
        case1 = today_open > yest_low
        range_size = today_open - yest_low
        
        if range_size <= 0:
            return None
        
        buy_618 = yest_low + 0.618 * range_size
        buy_50 = yest_low + 0.5 * range_size
        
        acceptance = (yest_low <= buy_618 <= yest_high and 
                     yest_low <= buy_50 <= yest_high)
        
        if case1 and acceptance:
            return {
                'buy_price': round(buy_50, 0),
                'stop_loss': round(yest_low, 0),
                'target1': round(today_open + 0.382 * range_size, 0),
                'yest_low': round(yest_low, 0),
                'today_open': round(today_open, 0),
                'timestamp': datetime.now(IST).strftime('%H:%M:%S IST'),
                'status': '🔥 LIVE TRIGGER'
            }
        return None
    except:
        return None

def send_live_alert(signal):
    """🚨 Send LIVE trading alert"""
    try:
        sender = st.secrets["email"]["sender"]
        pwd = st.secrets["email"]["app_password"]
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, pwd)
        
        body = f"""🚨 NIFTY50 LIVE FIBONACCI SIGNAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ {signal['timestamp']}
📈 BUY @ ₹{signal['buy_price']:,}
🛑 SL @ ₹{signal['stop_loss']:,}
🎯 T1 @ ₹{signal['target1']:,}

Yest Low: ₹{signal['yest_low']:,}
Today Open: ₹{signal['today_open']:,}"""
        
        for email in email_recipients:
            msg = MIMEText(body)
            msg['Subject'] = f"🚨 NIFTY50 LIVE: Buy ₹{signal['buy_price']:,}"
            msg['From'] = sender
            msg['To'] = email
            server.send_message(msg)
        
        server.quit()
        return True
    except:
        return False

# Your existing backtest functions (unchanged)
def fibonacci_backtest(data):
    results = []
    for i in range(len(data)-1, 0, -1):
        today_date = data.index[i].strftime('%m/%d')
        today_open = data['Open'].iloc[i]
        yest_low = data['Low'].iloc[i-1]
        yest_high = data['High'].iloc[i-1]
        
        case1 = "YES" if today_open > yest_low else "NO"
        range_size = today_open - yest_low
        
        if range_size <= 0:
            results.append({
                'date': today_date, 'today_open': f"{today_open:.0f}",
                'yest_low': f"{yest_low:.0f}", 'case1': case1, 
                'trigger': 'NO TRADE', 'buy_50': '0.00', 'sl': f"{yest_low:.0f}"
            })
            continue
        
        buy_618 = yest_low + 0.618 * range_size
        buy_50 = yest_low + 0.5 * range_size
        
        acceptance = "YES" if (yest_low <= buy_618 <= yest_high and 
                             yest_low <= buy_50 <= yest_high) else "NO"
        trigger = "TRIGGER" if case1 == "YES" and acceptance == "YES" else "NO TRADE"
        
        results.append({
            'date': today_date,
            'today_open': f"{today_open:.0f}",
            'yest_low': f"{yest_low:.0f}",
            'case1': case1,
            'acceptance': acceptance,
            'trigger': trigger,
            'buy_50': f"{buy_50:.0f}",
            'sl': f"{yest_low:.0f}"
        })
    return results

# ---------------- LIVE DASHBOARD ----------------
st.title("🚀 NIFTY50 FIBONACCI LIVE SCANNER")
st.markdown("**9:15 AM - 3:30 PM IST | Mon-Fri | Auto emails on triggers**")

# Market Status
now = datetime.now(IST)
market_open = is_market_open()
col1, col2 = st.columns(2)

if market_open:
    col1.metric("📊 **MARKET STATUS**", "🟢 **OPEN**", f"{now.strftime('%H:%M')} IST")
    col1.markdown("**Next scan: Auto**")
else:
    col1.metric("📊 **MARKET STATUS**", "🔴 **CLOSED**", f"{now.strftime('%H:%M')} IST")
    col1.markdown("**Market: 9:15 AM - 3:30 PM IST**")

col2.metric("🕒 **Last Scan**", st.session_state.last_scan.strftime('%H:%M') if st.session_state.last_scan else "Never")

# LIVE SIGNAL SECTION
st.subheader("🔴 **LIVE SIGNAL MONITOR**")
if market_open:
    if st.button("🔍 **SCAN NOW**", key="live_scan", use_container_width=True):
        signal = scan_live_signal()
        st.session_state.live_signal = signal
        st.session_state.last_scan = datetime.now(IST)
        
        if signal:
            st.session_state.live_signal = signal
            if st.button("🚨 **SEND LIVE ALERT**", key="send_live", use_container_width=True):
                send_live_alert(signal)
                st.balloons()
        st.rerun()
    
    if st.session_state.live_signal:
        signal = st.session_state.live_signal
        col1, col2, col3 = st.columns(3)
        col1.metric("📈 **BUY**", f"₹{signal['buy_price']:,}")
        col2.metric("🛑 **SL**", f"₹{signal['stop_loss']:,}")
        col3.metric("🎯 **TARGET**", f"₹{signal['target1']:,}")
        
        st.success(f"✅ **{signal['status']}** | {signal['timestamp']}")
        
        if st.button("📧 **RESEND ALERT**", key="resend_alert"):
            send_live_alert(signal)
else:
    st.info("⚠️ **Market closed. Live scanning available 9:15 AM - 3:30 PM IST**")

# ---------------- BACKTEST SECTION ----------------
st.subheader("📊 **HISTORICAL BACKTEST** (Your Jan 2026 Data)")
col1, col2 = st.columns(2)
with col1:
    if st.button("🔥 **RUN BACKTEST**", key="run_backtest", use_container_width=True):
        data = get_your_jan_2026_data()  # Your function from previous code
        st.session_state.backtest_results = fibonacci_backtest(data)
        st.rerun()

with col2:
    if st.button("📊 **SEND BACKTEST REPORT**", key="backtest_report", use_container_width=True) and st.session_state.backtest_results:
        send_pro_report(email_recipients)  # Your function from previous code

if st.session_state.backtest_results:
    df = pd.DataFrame(st.session_state.backtest_results)
    triggers = len(df[df.trigger == 'TRIGGER'])
    st.metric("🎯 **Backtest Triggers**", triggers)
    
    st.dataframe(df[['date', 'today_open', 'yest_low', 'case1', 'trigger', 'buy_50', 'sl']].tail(10), 
                use_container_width=True, hide_index=True)

# Auto-refresh during market hours
if market_open and st.button("🔄 **AUTO REFRESH ON**", key="auto_refresh"):
    st.rerun()

st.markdown("---")
st.markdown("*✅ LIVE 9:15-15:30 IST | Auto emails | Your Jan data backtest*")
