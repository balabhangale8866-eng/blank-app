# app.py
import os
import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, time as dtime
from strategy import SensexTradingBot
from data_manager import DataManager
from trade_manager import TradeManager
from options_manager import OptionsManager
from streamlit_autorefresh import st_autorefresh

DAILY_SUMMARY_FILE = "daily_summary.csv"
STARTING_CAPITAL = 35000

# Sidebar
st.sidebar.title("🔑 Kite Connect Credentials")
api_key = st.sidebar.text_input("API Key", type="password")
access_token = st.sidebar.text_input("Access Token", type="password")

# Header
st.title("📈 Sensex ATM Options Paper Trading")
st.markdown("Live paper-trading bot using MACD + Day High filter")

# Start Bot
if st.sidebar.button("▶️ Start Bot"):
    if not api_key or not access_token:
        st.sidebar.error("Both API Key and Access Token are required.")
    else:
        bot = SensexTradingBot(api_key, access_token)
        st.session_state.bot = bot
        st.session_state.start_time = datetime.now()
        st.rerun()

# Stop Bot
if 'bot' in st.session_state and st.sidebar.button("⏹️ Stop Bot"):
    st.session_state.bot.stop()
    st.sidebar.success("Bot stopped.")
    del st.session_state.bot
    st.rerun()

# Placeholders for live sections
metrics_placeholder = st.empty()
macd_chart_placeholder = st.empty()
daily_chart_placeholder = st.empty()
cumulative_chart_placeholder = st.empty()
equity_chart_placeholder = st.empty()

# Function to update performance charts
def update_performance_charts():
    if os.path.exists(DAILY_SUMMARY_FILE):
        daily_df = pd.read_csv(DAILY_SUMMARY_FILE)
        daily_df['date'] = pd.to_datetime(daily_df['date'])

        # Live update for today's P&L
        if 'bot' in st.session_state and os.path.exists(st.session_state.bot.trade_manager.csv_file):
            df_today = pd.read_csv(st.session_state.bot.trade_manager.csv_file)
            live_pnl = df_today['PnL'].sum()
            today_date = datetime.now().strftime("%Y-%m-%d")

            if daily_df['date'].dt.strftime("%Y-%m-%d").iloc[-1] != today_date:
                daily_df = pd.concat([daily_df, pd.DataFrame([{
                    "date": datetime.now(),
                    "total_trades": len(df_today),
                    "total_pnl": live_pnl
                }])], ignore_index=True)
            else:
                daily_df.at[daily_df.index[-1], 'total_pnl'] = live_pnl
                daily_df.at[daily_df.index[-1], 'total_trades'] = len(df_today)

        # Daily P&L Chart
        fig_daily = go.Figure()
        fig_daily.add_trace(go.Bar(
            x=daily_df['date'],
            y=daily_df['total_pnl'],
            marker_color=daily_df['total_pnl'].apply(lambda x: 'green' if x >= 0 else 'red')
        ))
        fig_daily.update_layout(title="Daily Profit & Loss", template="plotly_white")
        daily_chart_placeholder.plotly_chart(fig_daily, use_container_width=True)

        # Cumulative P&L Chart
        daily_df['cumulative_pnl'] = daily_df['total_pnl'].cumsum()
        fig_cumulative = go.Figure()
        fig_cumulative.add_trace(go.Scatter(
            x=daily_df['date'], y=daily_df['cumulative_pnl'],
            mode='lines+markers', line=dict(color='blue', width=2)
        ))
        fig_cumulative.update_layout(title="Cumulative P&L Over Time", template="plotly_white")
        cumulative_chart_placeholder.plotly_chart(fig_cumulative, use_container_width=True)

        # Equity Curve Chart
        daily_df['equity'] = STARTING_CAPITAL + daily_df['total_pnl'].cumsum()
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(
            x=daily_df['date'], y=daily_df['equity'],
            mode='lines+markers', line=dict(color='purple', width=2)
        ))
        fig_equity.update_layout(
            title=f"Equity Curve (Starting ₹{STARTING_CAPITAL:,})",
            template="plotly_white"
        )
        equity_chart_placeholder.plotly_chart(fig_equity, use_container_width=True)

# Bot running section
if 'bot' in st.session_state:
    now_time = datetime.now().time()

    # Auto-stop at 3:30 PM
    if now_time >= dtime(15, 30):
        bot = st.session_state.bot
        bot.stop()

        if os.path.exists(bot.trade_manager.csv_file):
            df_history = pd.read_csv(bot.trade_manager.csv_file)
            total_pnl = df_history['PnL'].sum()
            trade_count = len(df_history)

            summary_df = pd.DataFrame([{
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_trades": trade_count,
                "total_pnl": total_pnl
            }])

            if os.path.exists(DAILY_SUMMARY_FILE):
                summary_df.to_csv(DAILY_SUMMARY_FILE, mode='a', header=False, index=False)
            else:
                summary_df.to_csv(DAILY_SUMMARY_FILE, index=False)

            st.success(f"📁 Daily summary saved — {trade_count} trades, P&L ₹{total_pnl:.2f}")

        del st.session_state.bot
        st.warning("⏹ Bot stopped automatically at 3:30 PM IST.")
    else:
        # Auto-refresh
        st_autorefresh(interval=10000, key="data_refresh")

        bot = st.session_state.bot
        bot.run_strategy_cycle()

        # Live metrics
        with metrics_placeholder.container():
            spot = bot.get_sensex_data()['last_price']
            st.metric("Sensex Spot Price", f"₹{spot:.2f}")

            day_high = bot.data_manager.day_high_930 or 0
            st.metric("Day High (till 09:30)", f"₹{day_high:.2f}")

            if os.path.exists(bot.trade_manager.csv_file):
                df_history = pd.read_csv(bot.trade_manager.csv_file)
                total_pnl = df_history['PnL'].sum()
                st.metric("Total P&L", f"₹{total_pnl:.2f}")

        # MACD Chart
        with macd_chart_placeholder.container():
            closes = bot.data_manager.get_recent_closes()
            macd = closes.ewm(span=12, adjust=False).mean() - closes.ewm(span=26, adjust=False).mean()
            signal = macd.ewm(span=9, adjust=False).mean()

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=closes.index, y=macd, name="MACD Line"))
            fig.add_trace(go.Scatter(x=closes.index, y=signal, name="Signal Line"))
            st.plotly_chart(fig, use_container_width=True)

        # Open positions
        if bot.trade_manager.positions:
            df_open = pd.DataFrame(bot.trade_manager.positions)
            df_open['entry_timestamp'] = pd.to_datetime(df_open['timestamp'])
            st.subheader("🛠 Open Positions")
            st.dataframe(df_open[['type','symbol','entry_price','stop_loss','target','lots','entry_timestamp']])

# Update charts (always runs)
update_performance_charts()