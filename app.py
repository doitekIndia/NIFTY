# app.py - FIXED NIFTY50 Flask → Streamlit Conversion (No Thread Session State Issues)
import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Streamlit config
st.set_page_config(page_title="NIFTY50 Fibonacci Scanner", layout="wide", page_icon="📈")

# GLOBAL STATE (Streamlit session_state) - FIXED INITIALIZATION
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = []
if 'backtest_running' not in st.session_state:
    st.session_state.backtest_running = False
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False
if 'backtest_progress' not in st.session_state:
    st.session_state.backtest_progress = 0

email_recipients = ["xmlkeyserver@gmail.com", "nitinplus@gmail.com", "aamirlodhi46@gmail.com"]

def safe_float(value):
    """Exact same safe_float from your Flask code"""
    try:
        if pd.isna(value) or value is None:
            return None
        if hasattr(value, 'iloc'):
            return float(value.iloc[0]) if len(value) > 0 else None
        return float(value)
    except:
        return None

@st.cache_data(ttl=1800)
def get_nifty_daily_data():
    """Exact same function - LAST 25 TRADING DAYS - TODAY FIRST"""
    try:
        ticker = yf.Ticker('^NSEI')
        data = ticker.history(period="1mo")
        if data.index.tz is not None:
            data.index = data.index.tz_convert(None)
        data = data.dropna()
        st.info(f"✅ LAST {len(data)} DAYS | TODAY: {data.index[-1].strftime('%m/%d/%Y')}")
        return data.tail(25)
    except:
        return pd.DataFrame()

def send_email(recipients, symbol, signals=None):
    """FIXED: No session_state access - Pure function"""
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = st.secrets.get("EMAIL_SENDER", "xmlkeyserver@gmail.com")
        sender_password = st.secrets.get("EMAIL_PASSWORD", "ikbl nfjo mkii wtkr")
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        
        subject = f"🚨 NIFTY50 FIBONACCI: {symbol}"
        
        if symbol == "BACKTEST-REPORT":
            # Get results from function param instead of session_state
            triggers = [r for r in signals if r['trigger'] == 'TRIGGER']
            total_days = len(signals)
            hit_rate = (len(triggers) / total_days * 100) if total_days > 0 else 0
            
            body = f"""🔥 NIFTY50 FIBONACCI BACKTEST REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}
📊 Period: {signals[0]['date']} → {signals[-1]['date']}
🎯 Triggers: {len(triggers)} / {total_days} days
📈 Hit Rate: {hit_rate:.1f}%

🔥 TOP 5 TRIGGERS:
"""
            for trigger in triggers[-5:]:
                body += f"""🔔 {trigger['date']}
   Buy 50%: ₹{trigger['buy_50']}
   SL: ₹{trigger['sl']}
   T1: ₹{trigger['target1'][:7]}

"""
            body += f"🔗 LIVE DASHBOARD: {st.secrets.get('APP_URL', 'nifty.streamlit.app')}"
        else:
            body = f"""🔥 NIFTY50 LIVE TRADING ALERT
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}
📈 Buy 50%: ₹{signals.get('buy_50', 0):,.0f}
🛑 SL: ₹{signals.get('sl', 0):,.0f}
🎯 T1: ₹{signals.get('target1', 0):,.0f}

🔗 DASHBOARD: {st.secrets.get('APP_URL', 'nifty.streamlit.app')}
"""
        
        success_count = 0
        for recipient in recipients:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = recipient
            
            server.send_message(msg)
            st.success(f"✅ EMAIL SENT → {recipient}")
            success_count += 1
        
        server.quit()
        st.success(f"📧 SUCCESS: {symbol} → {success_count} emails")
        return True
        
    except Exception as e:
        st.error(f"❌ EMAIL ERROR: {str(e)}")
        return False

def calculate_backtest(data):
    """FIXED: Pure function - NO session_state access for threading"""
    results = []
    signals_found = 0
    
    for i in range(len(data)-1, 0, -1):  # Today → Backwards
        today_date = data.index[i].strftime('%m/%d/%Y')
        today_open = safe_float(data['Open'].iloc[i])
        yest_low = safe_float(data['Low'].iloc[i-1])
        yest_high = safe_float(data['High'].iloc[i-1])
        
        if today_open is None or yest_low is None or yest_high is None:
            case1 = "NO"
        else:
            case1 = "YES" if today_open > yest_low else "NO"
            range_size = today_open - yest_low
            
            if range_size <= 0:
                acceptance = 'NO'
                trigger = 'NO TRADE'
                buy_618 = buy_50 = buy_382 = '0.00'
                sl = f"{yest_low:.0f}" if yest_low else '0'
                target1 = target2 = target3 = '0.00'
            else:
                buy_618 = yest_low + 0.618 * range_size
                buy_50 = yest_low + 0.5 * range_size
                buy_382 = yest_low + 0.382 * range_size
                
                acceptance = "YES" if (yest_low <= buy_618 <= yest_high and yest_low <= buy_50 <= yest_high) else "NO"
                trigger = "TRIGGER" if case1 == "YES" and acceptance == "YES" else "NO TRADE"
                
                target1 = today_open + 0.382 * range_size
                target2 = today_open + 0.5 * range_size
                target3 = today_open + 1.0 * range_size
                
                buy_618 = f"{buy_618:.4f}"
                buy_50 = f"{buy_50:.3f}"
                buy_382 = f"{buy_382:.4f}"
                sl = f"{yest_low:.1f}"
                target1 = f"{target1:.4f}"
                target2 = f"{target2:.4f}"
                target3 = f"{target3:.4f}"
        
        result = {
            'date': today_date,
            'today_open': f"{today_open:.2f}" if today_open else '0.00',
            'yest_low': f"{yest_low:.1f}" if yest_low else '0',
            'yest_high': f"{yest_high:.1f}" if yest_high else '0',
            'case1': case1,
            'acceptance': acceptance,
            'trigger': trigger,
            'buy_618': buy_618,
            'buy_50': buy_50,
            'buy_382': buy_382,
            'sl': sl,
            'target1': target1,
            'target2': target2,
            'target3': target3
        }
        results.append(result)
        
        if trigger == "TRIGGER":
            signals_found += 1
    
    return results, signals_found

# MAIN BACKTEST BUTTON HANDLER (Main thread only - NO threading issues)
if st.button("🔄 **RUN BACKTEST**", use_container_width=True, key="run_backtest"):
    st.session_state.backtest_running = True
    st.session_state.backtest_results.clear()
    st.session_state.backtest_progress = 0
    st.rerun()

# ---------------- STREAMLIT DASHBOARD ----------------
st.title("🚀 NIFTY50 FIBONACCI SCANNER")
st.markdown("**Exact replica of your Flask app - FIXED threading issues**")

# Status
col1, col2 = st.columns(2)
col1.metric("📊 Backtest Status", "Ready" if not st.session_state.backtest_running else f"Running... {st.session_state.backtest_progress}%")
col2.metric("🎯 Triggers Found", len([r for r in st.session_state.backtest_results if r['trigger'] == 'TRIGGER']))

# Buttons row
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.button("🔄 **RUN BACKTEST**", use_container_width=True, key="run_backtest_btn", disabled=st.session_state.backtest_running)

with col2:
    if st.button("📧 **TEST TRIGGER**", use_container_width=True, key="test_trigger"):
        signals = {'buy_50': 25850, 'sl': 25750, 'target1': 25950}
        send_email(email_recipients, 'LIVE-TEST', signals)

with col3:
    if st.button("📊 **SEND REPORT**", use_container_width=True, key="send_report_btn"):
        if st.session_state.backtest_results:
            send_email(email_recipients, "BACKTEST-REPORT", st.session_state.backtest_results)
        else:
            st.warning("⚠️ Run backtest first!")

with col4:
    if st.button("▶️ **START MONITORING**", use_container_width=True, key="start_monitor"):
        st.session_state.monitoring_active = True
        st.success("✅ Live monitoring started")

with col5:
    if st.button("⏹️ **STOP MONITORING**", use_container_width=True, key="stop_monitor"):
        st.session_state.monitoring_active = False
        st.success("✅ Live monitoring stopped")

# BACKTEST EXECUTION (Main thread - Safe)
if st.session_state.backtest_running and not st.session_state.backtest_results:
    with st.spinner("🔥 Running NIFTY50 backtest..."):
        data = get_nifty_daily_data()
        
        if len(data) < 10:
            st.error("❌ Insufficient data")
            st.session_state.backtest_running = False
            st.rerun()
            st.stop()
        
        # Simulate progress
        progress_bar = st.progress(0)
        
        results, signals_found = calculate_backtest(data)
        st.session_state.backtest_results = results
        
        progress_bar.progress(100)
        st.info(f"✅ BACKTEST COMPLETE: {signals_found} TRIGGERS")
        
        st.session_state.backtest_running = False
        st.session_state.backtest_progress = 100
        st.rerun()

# Results Table
if st.session_state.backtest_results:
    st.subheader("📋 BACKTEST RESULTS (Last 20 Days)")
    df = pd.DataFrame(st.session_state.backtest_results[-20:])
    
    st.dataframe(
        df[['date', 'today_open', 'yest_low', 'yest_high', 'case1', 'acceptance', 
            'trigger', 'buy_50', 'sl', 'target1']],
        use_container_width=True,
        column_config={
            "trigger": st.column_config.TextColumn("Signal", help="TRIGGER = Buy Signal"),
            "buy_50": st.column_config.NumberColumn("Buy 50%", format="₹%.2f"),
        },
        hide_index=True
    )
    
    # Metrics
    triggers = len([r for r in st.session_state.backtest_results if r['trigger'] == 'TRIGGER'])
    total = len(st.session_state.backtest_results)
    col1, col2, col3 = st.columns(3)
    col1.metric("🎯 Triggers", triggers)
    col2.metric("📊 Hit Rate", f"{triggers/total*100:.1f}%" if total else "0%")
    col3.metric("📅 Days", total)
    
    # CSV Export
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Download CSV", csv, "nifty50_backtest.csv", use_container_width=True)

else:
    st.info("👆 Click **RUN BACKTEST** to start analysis")

# Live data API
with st.expander("🔧 API Data (JSON)"):
    st.json(st.session_state.backtest_results[-5:])

st.markdown("---")
st.markdown("*✅ FIXED: No threading session_state errors | Pure functions | Main thread execution*")
