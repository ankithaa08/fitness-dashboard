import streamlit as st
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Page configuration
st.set_page_config(page_title="Fitness Dashboard", page_icon="📈", layout="wide")
sns.set_theme(style="whitegrid")

import zipfile

# Initialize connection to the merged database file
DB_FILE = 'fitness.db'
ZIP_FILE = 'fitness.zip'

@st.cache_resource
def get_db_connection():
    # If the database doesn't exist but a ZIP file does, extract it!
    if not os.path.exists(DB_FILE) and os.path.exists(ZIP_FILE):
        with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
            zip_ref.extractall('.')
            
    # If the file doesn't exist, create an in-memory DB so the app doesn't crash
    if os.path.exists(DB_FILE):
        return duckdb.connect(database=DB_FILE, read_only=False)
    else:
        return duckdb.connect(database=':memory:')

con = get_db_connection()

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["📊 PowerBI-Style Dashboard", "🧹 Data Cleaning (SQL)", "🔍 SQL Insights & Analysis", "📂 Data Overview"])

# Check if tables exist
tables_df = con.execute("SHOW TABLES").fetchdf()
has_data = not tables_df.empty

if not has_data:
    st.sidebar.warning(f"⚠️ No data found! Make sure `{DB_FILE}` is in the same folder as this app.")
else:
    st.sidebar.success(f"Connected to Database! Found {len(tables_df)} datasets.")


# ----------------- PAGE: DATA OVERVIEW -----------------
if page == "📂 Data Overview":
    st.title("📂 Data Overview")
    if has_data:
        for idx, row in tables_df.iterrows():
            t_name = row['name']
            st.subheader(f"Dataset: `{t_name}`")
            try:
                df_preview = con.execute(f"SELECT * FROM {t_name} LIMIT 5").fetchdf()
                st.dataframe(df_preview, use_container_width=True)
            except Exception:
                st.error(f"Could not read preview for {t_name}")
    else:
        st.info("No data available.")

# ----------------- PAGE: DATA CLEANING (SQL) -----------------
elif page == "🧹 Data Cleaning (SQL)":
    st.title("🧹 Data Cleaning with SQL")
    st.markdown("""
    Use this section to clean your raw data (e.g., handle nulls, cast data types) and create new **Clean Views**. 
    Example: `CREATE OR REPLACE VIEW clean_data AS SELECT * FROM raw_table WHERE calories > 0`
    """)
    
    if has_data:
        cleaning_query = st.text_area("Write your SQL Data Cleaning Query (CREATE VIEW ...):", height=150)
        
        if st.button("🧹 Execute Cleaning Query"):
            try:
                con.execute(cleaning_query)
                st.success("Cleaning query executed successfully! The new clean view is now available.")
            except Exception as e:
                st.error(f"SQL Error: {e}")
                
        st.markdown("### Currently Available Tables & Views")
        st.dataframe(con.execute("SHOW TABLES").fetchdf())
    else:
        st.info("No data available.")

# ----------------- PAGE: SQL INSIGHTS -----------------
elif page == "🔍 SQL Insights & Analysis":
    st.title("🔍 SQL Insights & Analysis")
    st.markdown("Write raw SQL queries against your cleaned data to generate insights.")
    
    if has_data:
        st.write("**Available Tables/Views:**", ", ".join([f"`{t}`" for t in tables_df['name']]))
        
        query = st.text_area("Enter your SQL Query to generate insights:", height=150)
        
        if st.button("▶️ Get Insights"):
            try:
                result_df = con.execute(query).fetchdf()
                st.success(f"Insight Generated! ({len(result_df)} rows returned)")
                st.dataframe(result_df, use_container_width=True)
            except Exception as e:
                st.error(f"SQL Error: {e}")
    else:
        st.info("No data available.")

# ----------------- PAGE: DASHBOARD (POWER BI STYLE) -----------------
elif page == "📊 PowerBI-Style Dashboard":
    st.title("📊 Interactive Fitness Dashboard")
    st.markdown("A Tableau/PowerBI style dashboard using **Matplotlib** and **Seaborn**.")
    
    if has_data:
        tables = tables_df['name'].tolist()
        
        # Dashboard Controls
        st.markdown("### 🎛️ Dashboard Controls")
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            selected_table = st.selectbox("Select Dataset for Dashboard", tables)
            
        try:
            df = con.execute(f"SELECT * FROM {selected_table}").fetchdf()
            
            # Key Performance Indicators (KPIs)
            st.markdown("### 📈 Key Metrics")
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if len(numeric_cols) >= 3:
                kpi1, kpi2, kpi3 = st.columns(3)
                kpi1.metric(label=f"Total {numeric_cols[0]}", value=round(df[numeric_cols[0]].sum(), 2))
                kpi2.metric(label=f"Average {numeric_cols[1]}", value=round(df[numeric_cols[1]].mean(), 2))
                kpi3.metric(label=f"Max {numeric_cols[2]}", value=round(df[numeric_cols[2]].max(), 2))
            elif len(numeric_cols) > 0:
                st.metric(label=f"Total {numeric_cols[0]}", value=round(df[numeric_cols[0]].sum(), 2))

            # Visualizations
            st.markdown("### 🎨 Visualizations")
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.subheader("Distribution (Seaborn)")
                if len(numeric_cols) > 0:
                    fig1, ax1 = plt.subplots(figsize=(6, 4))
                    sns.histplot(data=df, x=numeric_cols[0], kde=True, ax=ax1, color="skyblue")
                    st.pyplot(fig1)
                    
            with chart_col2:
                st.subheader("Correlation Scatter (Matplotlib)")
                if len(numeric_cols) >= 2:
                    fig2, ax2 = plt.subplots(figsize=(6, 4))
                    ax2.scatter(df[numeric_cols[0]], df[numeric_cols[1]], alpha=0.5, color="coral")
                    ax2.set_xlabel(numeric_cols[0])
                    ax2.set_ylabel(numeric_cols[1])
                    ax2.grid(True, linestyle='--', alpha=0.7)
                    st.pyplot(fig2)
                    
            st.markdown("### 📋 Detailed Data View")
            st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error building dashboard: {e}")
    else:
        st.info("No data available.")
