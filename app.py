import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="2026 Engine Repair Dashboard",
    page_icon="🔧",
    layout="wide"
)

# Database setup
def init_db():
    conn = sqlite3.connect('engine_repair.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_log (
            date TEXT PRIMARY KEY,
            glucose REAL,
            sleep REAL,
            mood INTEGER,
            unhook TEXT,
            control_note TEXT,
            one_must TEXT,
            one_must_done TEXT,
            phone_boxed TEXT,
            presence TEXT,
            shutdown TEXT,
            notes TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_entry(data):
    conn = sqlite3.connect('engine_repair.db')
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO daily_log VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', data)
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect('engine_repair.db')
    df = pd.read_sql_query("SELECT * FROM daily_log ORDER BY date DESC", conn)
    conn.close()
    if len(df) > 0:
        df['date'] = pd.to_datetime(df['date'])
    return df

def check_streak(df):
    if len(df) == 0:
        return 0, "No entries yet"
    
    df_sorted = df.sort_values('date', ascending=False)
    today = pd.Timestamp(date.today())
    
    # Check if we have today's entry
    if df_sorted.iloc[0]['date'].date() != today.date():
        days_since = (today - df_sorted.iloc[0]['date']).days
        if days_since == 1:
            return len(df_sorted), "⚠️ Log today to keep your streak!"
        elif days_since > 1:
            return 0, f"❌ Streak broken! Last entry was {days_since} days ago. Reset and start again."
    
    # Count consecutive days
    streak = 1
    for i in range(len(df_sorted) - 1):
        diff = (df_sorted.iloc[i]['date'] - df_sorted.iloc[i+1]['date']).days
        if diff <= 2:  # Two-day rule
            streak += 1
        else:
            break
    
    return streak, "🔥 Keep going!"

# Initialize
init_db()

# Header
st.title("🔧 2026 Engine Repair Dashboard")
st.markdown("*Simplicity. Consistency. Self-Forgiveness.*")

# Tabs
tab1, tab2 = st.tabs(["📝 Today's Check-In", "📊 Dashboard"])

with tab1:
    st.header("Daily Check-In")
    
    # Check if already logged today
    df = load_data()
    today_str = date.today().isoformat()
    already_logged = False
    if len(df) > 0:
        already_logged = today_str in df['date'].dt.date.astype(str).values
    
    if already_logged:
        st.success("✅ You've already logged today! Great work.")
        if st.button("Update Today's Entry"):
            already_logged = False
    
    if not already_logged:
        with st.form("daily_checkin"):
            st.subheader("1️⃣ The Engine Check (Bio-Metrics)")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                glucose = st.number_input("AM Glucose", min_value=0.0, max_value=20.0, step=0.1, value=5.5)
                if glucose > 7.0:
                    st.warning("⚠️ Above 7.0 - Recovery day. Don't push hard.")
            
            with col2:
                sleep = st.number_input("Sleep (hours)", min_value=0.0, max_value=12.0, step=0.5, value=7.0)
                if sleep < 7.0:
                    st.warning("⚠️ Under 7 hours - Impaired executive function. Lower your demands.")
            
            with col3:
                mood = st.select_slider("Mood", options=[1,2,3,4,5], value=3,
                    help="1-2: Red Zone (walk only)\n3: Yellow (maintenance)\n4-5: Green (deep work)")
                if mood <= 2:
                    st.error("🔴 Red Zone - No hard decisions today. Walk only.")
                elif mood == 3:
                    st.warning("🟡 Yellow Zone - Maintenance mode.")
                else:
                    st.success("🟢 Green Zone - Attack the Deep Work!")
            
            st.markdown("---")
            st.subheader("2️⃣ The Stoic Anchor (Mental Health)")
            
            unhook = st.radio("Did you catch yourself spiraling and drop anchor?", ["Yes", "No", "N/A"])
            control_note = st.text_input("ONE thing you controlled today:", 
                placeholder="e.g., 'I didn't yell when frustrated' or 'I chose water over soda'")
            
            st.markdown("---")
            st.subheader("3️⃣ The 'One Must' (Professional)")
            
            one_must = st.text_area("What is your ONE cognitive task (The Frog)?", 
                placeholder="The one thing that would make today a success if done by 11 AM")
            one_must_done = st.radio("Did you finish it by 11 AM?", ["Yes", "No", "In Progress"])
            
            st.markdown("---")
            st.subheader("4️⃣ Connection (Family)")
            
            phone_boxed = st.radio("20 minutes phone-free with Bjorn or Bernadette?", ["Yes", "No"])
            presence = st.radio("Did you listen without trying to 'fix' them?", ["Yes", "No", "N/A"])
            
            st.markdown("---")
            st.subheader("5️⃣ The Shutdown")
            
            shutdown = st.radio("Did you close the garage? (Laptop closed, tomorrow's 'One Must' written, said 'Done')", 
                ["Yes", "No", "Not Yet"])
            
            notes = st.text_area("Any other notes?", placeholder="Optional reflections...")
            
            submitted = st.form_submit_button("💾 Save Today's Entry", type="primary")
            
            if submitted:
                entry = (
                    today_str,
                    glucose,
                    sleep,
                    mood,
                    unhook,
                    control_note,
                    one_must,
                    one_must_done,
                    phone_boxed,
                    presence,
                    shutdown,
                    notes,
                    datetime.now().isoformat()
                )
                save_entry(entry)
                st.success("✅ Entry saved! You showed up today. That's what matters.")
                st.rerun()

with tab2:
    st.header("Your Progress")
    
    df = load_data()
    
    if len(df) == 0:
        st.info("No data yet. Complete your first check-in to see your dashboard!")
    else:
        # Streak
        streak, message = check_streak(df)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current Streak", f"{streak} days", message)
        with col2:
            st.metric("Total Check-Ins", len(df))
        with col3:
            # Win rate (days with mood >= 3 and one_must done)
            wins = len(df[(df['mood'] >= 3) & (df['one_must_done'] == 'Yes')])
            win_rate = (wins / len(df) * 100) if len(df) > 0 else 0
            st.metric("Win Rate", f"{win_rate:.0f}%", f"{wins} wins")
        
        st.markdown("---")
        
        # Recent data (last 30 days)
        df_recent = df[df['date'] >= (datetime.now() - timedelta(days=30))]
        
        # Glucose & Sleep trends
        col1, col2 = st.columns(2)
        
        with col1:
            fig_glucose = px.line(df_recent, x='date', y='glucose', 
                title='Glucose Trend (Last 30 Days)',
                markers=True)
            fig_glucose.add_hline(y=7.0, line_dash="dash", line_color="red", 
                annotation_text="Recovery Threshold")
            st.plotly_chart(fig_glucose, use_container_width=True)
        
        with col2:
            fig_sleep = px.line(df_recent, x='date', y='sleep',
                title='Sleep Pattern (Last 30 Days)',
                markers=True)
            fig_sleep.add_hline(y=7.0, line_dash="dash", line_color="green",
                annotation_text="Target")
            st.plotly_chart(fig_sleep, use_container_width=True)
        
        # Mood distribution
        mood_counts = df_recent['mood'].value_counts().sort_index()
        fig_mood = go.Figure(data=[go.Bar(
            x=mood_counts.index,
            y=mood_counts.values,
            marker_color=['red', 'orange', 'yellow', 'lightgreen', 'green'][:len(mood_counts)]
        )])
        fig_mood.update_layout(title='Mood Distribution (Last 30 Days)',
            xaxis_title='Mood Level', yaxis_title='Days')
        st.plotly_chart(fig_mood, use_container_width=True)
        
        # Recent entries
        st.subheader("Recent Entries")
        display_df = df_recent[['date', 'glucose', 'sleep', 'mood', 'one_must_done', 'shutdown']].copy()
        display_df['date'] = display_df['date'].dt.date
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Export option
        st.markdown("---")
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download All Data (CSV)",
            data=csv,
            file_name=f"engine_repair_{date.today()}.csv",
            mime="text/csv"
        )
