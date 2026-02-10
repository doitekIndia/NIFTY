# QUICK FIX - Replace ONLY the send_email() function in your app.py:

def send_email(recipients, symbol, signals):
    try:
        # ✅ FIXED: Use YOUR exact secrets structure
        sender_email = st.secrets["email"]["sender"]  
        sender_password = st.secrets["email"]["app_password"]
        
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
🎯 Triggers: {len(triggers)} / {total_days} days ({hit_rate:.1f}%)"""
        else:
            body = f"""🔥 NIFTY50 LIVE TRADING ALERT
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}
📈 Buy 50%: ₹{signals.get('buy_50', 0):,.0f}
🛑 SL: ₹{signals.get('sl', 0):,.0f}
🎯 T1: ₹{signals.get('target1', 0):,.0f}"""
        
        success_count = 0
        for recipient in recipients:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = recipient
            server.send_message(msg)
            success_count += 1
        
        server.quit()
        st.success(f"✅ {success_count} emails sent to: {', '.join(recipients)}")
        return True
    except Exception as e:
        st.error(f"❌ Email failed: {str(e)}")
        return False
