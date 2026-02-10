# app.py - FIXED NIFTY50 Fibonacci Scanner (No DuplicateWidgetID)
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

st.set_page_config(page_title="NIFTY50 Fibonacci Scanner", layout="wide", page_icon="📈")

# Initialize session state
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = []
if 'backtest_running' not in st.session_state:
    st.session_state.backtest_running = False

email_recipients = ["xmlkeyserver@gmail.com", "nitinplus@gmail.com", "aamirlodhi46@gmail.com"]

def safe_float(value):
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
    try:
        ticker = yf.Ticker('^NSEI')
        data = ticker.history(period="1mo")
        if data.index.tz is not None:
            data.index = data.index.tz_convert(None)
        data = data.dropna()
        return data.tail(25)
    except:
        return pd.DataFrame()

def send_email(recipients, symbol, signals):
    try:
        sender_email = st.secrets.get("EMAIL_SENDER", "xmlkeyserver@gmail.com")
        sender_password = st.secrets.get("EMAIL_PASSWORD", "")
        
        server = smtplib.SMTP("smtp.gmail.com", 587)
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
                body += f"\n🔔 {trigger['date']}\n   Buy 50%: ₹{trigger['buy_50']}\n   SL: ₹{trigger['sl']}"
        else:
            body = f"""🔥 NIFTY50 LIVE TRADING ALERT
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}
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
        st.success(f"✅ {symbol} emails sent!")
        return True
    except Exception as e:
        st.error(f"❌ Email error: {str(e)}")
        return False

def run_historical_backtest():
    if st.session_state.backtest_running:
        st.warning("⏳ Backtest running...")
        return
    
    st.session_state.backtest_running = True
    st.session_state.backtest_results.clear()
    
    with st.spinner("🔥 Running NIFTY50 backtest..."):
        data = get_nifty_daily_data()
        
        if len(data) < 10:
            st.error("❌ Insufficient data")
            st.session_state.backtest_running = False
            st.rerun()
            return
        
        signals_found = 0
        for i in range(len(data)-1, 0, -1):
            today_date = data.index[i].strftime('%m/%d/%Y')
            today_open = safe_float(data['Open'].iloc[i])
            yest_low = safe_float(data['Low'].iloc[i-1])
            yest_high = safe_float(data['High'].iloc[i-1])
            
            if today_open is None or yest_low is None or yest_high is None:
                continue
            
            case1 = "YES" if today_open > yest_low else "NO"
            range_size = today_open - yest_low
            
            if range_size <= 0:
                st.session_state.backtest_results.append({
                    'date': today_date, 'today_open': f"{today_open:.0f}",
                    'yest_low': f"{yest_low:.0f}", 'case1': case1, 
                    'trigger': 'NO TRADE', 'buy_50': '0.00', 'sl': f"{yest_low:.0f}"
                })
                continue
            
            buy_618 = yest_low + 0.618 * range_size
            buy_50 = yest_low + 0.5 * range_size
            
            acceptance = "YES" if (yest_low <= buy_618 <= yest_high and yest_low <= buy_50 <= yest_high) else "NO"
            trigger = "TRIGGER" if case1 == "YES" and acceptance == "YES" else "NO TRADE"
            
            target1 = today_open + 0.382 * range_size
            
            result = {
                'date': today_date,
                'today_open': f"{today_open:.2f}",
                'yest_low': f"{yest_low:.1f}",
                'case1': case1,
                'acceptance': acceptance,
                'trigger': trigger,
                'buy_50': f"{buy_50:.2f}",
                'sl': f"{yest_low:.1f}",
                'target1': f"{target1:.2f}"
            }
            
            st.session_state.backtest_results.append(result)
            if trigger == "TRIGGER":
                signals_found += 1
        
        st.session_state.backtest_running = False
        st.success(f"✅ Backtest complete! {signals_found} triggers found")
        st.rerun()

# ---------------- DASHBOARD ----------------
st.title("🚀 NIFTY50 FIBONACCI SCANNER")

# Status metrics
col1, col2 = st.columns(2)
triggers = len([r for r in st.session_state.backtest_results if r['trigger'] == 'TRIGGER'])
col1.metric("🎯 Triggers", triggers)
col2.metric("📊 Status", "Ready" if not st.session_state.backtest_running else "Running")

# FIXED BUTTONS - UNIQUE KEYS
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🔄 RUN BACKTEST", key="btn_backtest", use_container_width=True):
        threading.Thread(target=run_historical_backtest, daemon=True).start()

with col2:
    if st.button("📧 TEST TRIGGER", key="btn_test_trigger", use_container_width=True):
        signals = {'buy_50': 25850, 'sl': 25750, 'target1': 25950}
        threading.Thread(target=send_email, args=(email_recipients, 'LIVE-TEST', signals), daemon=True).start()

with col3:
    if st.button("📊 SEND REPORT", key="btn_send_report", use_container_width=True) and st.session_state.backtest_results:
        threading.Thread(target=send_email, args=(email_recipients, "BACKTEST-REPORT", {}), daemon=True).start()
    elif st.button("📊 SEND REPORT", key="btn_send_report_disabled", use_container_width=True):
        st.warning("⚠️ Run backtest first!")

with col4:
    if st.button("▶️ MONITOR ON", key="btn_monitor_on", use_container_width=True):
        st.session_state.monitoring_active = True
        st.success("✅ Monitoring started")

with col5:
    if st.button("⏹️ MONITOR OFF", key="btn_monitor_off", use_container_width=True):
        st.session_state.monitoring_active = False
        st.success("✅ Monitoring stopped")

# Results
if st.session_state.backtest_results:
    st.subheader("📋 BACKTEST RESULTS (Last 20 Days)")
    df = pd.DataFrame(st.session_state.backtest_results[-20:])
    
    st.dataframe(
        df[['date', 'today_open', 'yest_low', 'case1', 'acceptance', 
            'trigger', 'buy_50', 'sl', 'target1']],
        use_container_width=True,
        column_config={
            "trigger": st.column_config.SelectboxColumn("Signal"),
            "buy_50": st.column_config.NumberColumn("Buy 50%", format="₹%.0f"),
            "sl": st.column_config.NumberColumn("Stop Loss", format="₹%.0f"),
        },
        hide_index=True
    )
    
    # Metrics
    total = len(st.session_state.backtest_results)
    hit_rate = triggers/total*100 if total else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("📊 Days Analyzed", total)
    col2.metric("📈 Hit Rate", f"{hit_rate:.1f}%")
    col3.metric("🎯 Triggers", triggers)
    
    # CSV Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Download CSV", csv, "nifty50_backtest.csv", use_container_width=True)

else:
    st.info("👆 Click **RUN BACKTEST** to analyze NIFTY50 data")

# Secrets info
with st.expander("🔧 Email Setup"):
    st.info("""
    **Create `.streamlit/secrets.toml`:**
    ```
    [email]
    EMAIL_SENDER = "xmlkeyserver@gmail.com"
    EMAIL_PASSWORD = "your_app_password"
    ```
    """)

st.markdown("---")
st.markdown("*NIFTY50 Fibonacci Scanner | Exact Flask conversion | Live 24/7*")
