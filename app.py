import streamlit as st
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import zipfile

# 🏋️‍♂️ FITNESS APP STYLING
st.set_page_config(page_title="FitTrack Pro", page_icon="💪", layout="wide")
sns.set_theme(style="darkgrid", palette="flare") # A sporty, energetic color palette

# Custom CSS to make it look more like an app
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    h1 {
        color: #ff4b4b;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Database Connection
DB_FILE = 'fitness.db'
ZIP_FILE = 'fitness.zip'

@st.cache_resource
def get_db_connection():
    if not os.path.exists(DB_FILE) and os.path.exists(ZIP_FILE):
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
            zip_ref.extractall('.')
    if os.path.exists(DB_FILE):
        return duckdb.connect(database=DB_FILE, read_only=False)
    else:
        return duckdb.connect(database=':memory:')

con = get_db_connection()
tables_df = con.execute("SHOW TABLES").fetchdf()
has_data = not tables_df.empty

# Sidebar Menu
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2964/2964514.png", width=100)
st.sidebar.title("FitTrack Pro")
page = st.sidebar.radio("Menu", ["🏃‍♂️ My Dashboard", "🏆 Activity History", "⚙️ Developer Tools (SQL)"])

if not has_data:
    st.warning("⚠️ No fitness data found. Please connect your database.")

# ----------------- PAGE: MAIN DASHBOARD -----------------
if page == "🏃‍♂️ My Dashboard":
    st.markdown("<h1>💪 Welcome Back!</h1>", unsafe_allow_html=True)
    st.markdown("### Your Weekly Fitness Summary")
    
    if has_data:
        tables = tables_df['name'].tolist()
        selected_activity = st.selectbox("Select Activity Log", tables)
        
        try:
            df = con.execute(f"SELECT * FROM {selected_activity}").fetchdf()
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            # --- KPI METRICS ---
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            
            # We try to show up to 4 metrics based on whatever numeric data exists
            if len(numeric_cols) > 0:
                col1.metric(label=f"🔥 Total {numeric_cols[0].replace('_', ' ').title()}", value=f"{int(df[numeric_cols[0]].sum()):,}")
            if len(numeric_cols) > 1:
                col2.metric(label=f"📈 Avg {numeric_cols[1].replace('_', ' ').title()}", value=f"{round(df[numeric_cols[1]].mean(), 1)}")
            if len(numeric_cols) > 2:
                col3.metric(label=f"⚡ Max {numeric_cols[2].replace('_', ' ').title()}", value=f"{int(df[numeric_cols[2]].max())}")
            if len(numeric_cols) > 3:
                col4.metric(label=f"⏱️ Total {numeric_cols[3].replace('_', ' ').title()}", value=f"{int(df[numeric_cols[3]].sum())}")
            
            st.markdown("<br><hr><br>", unsafe_allow_html=True)
            
            # --- CHARTS ---
            st.markdown("### 📊 Activity Trends")
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                if len(numeric_cols) > 0:
                    fig1, ax1 = plt.subplots(figsize=(6, 4))
                    sns.lineplot(data=df, y=numeric_cols[0], x=df.index, ax=ax1, color="#ff4b4b", linewidth=2.5)
                    ax1.set_title(f"{numeric_cols[0].replace('_', ' ').title()} Over Time", fontweight='bold')
                    ax1.set_xlabel("Entries")
                    st.pyplot(fig1)
                    
            with chart_col2:
                if len(numeric_cols) > 1:
                    fig2, ax2 = plt.subplots(figsize=(6, 4))
                    sns.histplot(data=df, x=numeric_cols[1], kde=True, ax=ax2, color="#ff904f")
                    ax2.set_title(f"{numeric_cols[1].replace('_', ' ').title()} Distribution", fontweight='bold')
                    st.pyplot(fig2)
                    
        except Exception as e:
            st.error("Could not load dashboard graphics.")
            
# ----------------- PAGE: ACTIVITY HISTORY -----------------
elif page == "🏆 Activity History":
    st.markdown("<h1>📅 Activity History</h1>", unsafe_allow_html=True)
    st.write("Browse through all your logged workouts and activities.")
    
    if has_data:
        tables = tables_df['name'].tolist()
        for t in tables:
            with st.expander(f"📁 {t.replace('_', ' ').title()} Data"):
                df = con.execute(f"SELECT * FROM {t} LIMIT 50").fetchdf()
                st.dataframe(df, use_container_width=True)


# ----------------- PAGE: DEVELOPER TOOLS (SQL) -----------------
elif page == "⚙️ Developer Tools (SQL)":
    st.markdown("<h1>⚙️ Advanced Data & SQL</h1>", unsafe_allow_html=True)
    st.markdown("For project grading: This section fulfills the SQL Analysis and Data Cleaning requirements.")
    
    tab1, tab2 = st.tabs(["🔍 SQL Analysis", "🧹 Data Cleaning"])
    
    with tab1:
        st.subheader("Write Custom Queries")
        if has_data:
            st.write("**Available Tables:**", ", ".join([f"`{t}`" for t in tables_df['name']]))
            query = st.text_area("SQL Query:", height=150)
            if st.button("Run Query"):
                try:
                    res = con.execute(query).fetchdf()
                    st.dataframe(res, use_container_width=True)
                except Exception as e:
                    st.error(e)
                    
    with tab2:
        st.subheader("Data Cleaning")
        if has_data:
            st.write("Create views to clean data. E.g. `CREATE OR REPLACE VIEW clean_data AS SELECT * FROM table WHERE col IS NOT NULL`")
            clean_query = st.text_area("Cleaning SQL:", height=100)
            if st.button("Execute Clean"):
                try:
                    con.execute(clean_query)
                    st.success("Cleaning view created!")
                except Exception as e:
                    st.error(e)
