import streamlit as st
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import glob

# Page configuration
st.set_page_config(page_title="Fitness Dashboard", page_icon="📈", layout="wide")
sns.set_theme(style="whitegrid") # Set seaborn theme for better looking charts

# Initialize DuckDB connection
@st.cache_resource
def get_db_connection():
    return duckdb.connect(database=':memory:')

con = get_db_connection()

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["📊 PowerBI-Style Dashboard", "🧹 Data Cleaning (SQL)", "🔍 SQL Insights & Analysis", "📂 Data Overview"])

# Directory input
st.sidebar.markdown("---")
st.sidebar.subheader("Data Source")
data_dir = st.sidebar.text_input("Enter the path to your CSV folder (e.g., D:\FitnessData):", value="data")

def get_csv_files(directory):
    if not os.path.exists(directory):
        return []
    return glob.glob(os.path.join(directory, "*.csv"))

csv_files = get_csv_files(data_dir)

if not csv_files:
    st.warning(f"⚠️ No CSV files found in `{data_dir}`! Please enter the correct folder path.")
else:
    # Register CSV files as views in DuckDB
    for file_path in csv_files:
        table_name = os.path.splitext(os.path.basename(file_path))[0]
        table_name = "".join([c if c.isalnum() else "_" for c in table_name])
        safe_path = file_path.replace("\\", "/")
        try:
            con.execute(f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_csv_auto('{safe_path}')")
        except Exception as e:
            st.sidebar.error(f"Failed to load {file_path}: {e}")
    st.sidebar.success(f"Loaded {len(csv_files)} datasets.")

# ----------------- PAGE: DATA OVERVIEW -----------------
if page == "📂 Data Overview":
    st.title("📂 Data Overview")
    if csv_files:
        tables = con.execute("SHOW TABLES").fetchdf()
        for idx, row in tables.iterrows():
            t_name = row['name']
            st.subheader(f"Dataset: `{t_name}`")
            try:
                df_preview = con.execute(f"SELECT * FROM {t_name} LIMIT 5").fetchdf()
                st.dataframe(df_preview, use_container_width=True)
            except Exception:
                st.error(f"Could not read preview for {t_name}")
    else:
        st.info("Please connect your data folder first.")


# ----------------- PAGE: DATA CLEANING (SQL) -----------------
elif page == "🧹 Data Cleaning (SQL)":
    st.title("🧹 Data Cleaning with SQL")
    st.markdown("""
    Use this section to clean your raw data (e.g., handle nulls, cast data types, filter out outliers) and create new **Clean Views**. 
    For example: `CREATE OR REPLACE VIEW clean_workouts AS SELECT date, COALESCE(calories, 0) as calories FROM raw_workouts WHERE calories > 0`
    """)
    
    if csv_files:
        cleaning_query = st.text_area("Write your SQL Data Cleaning Query (CREATE VIEW ...):", height=150)
        
        if st.button("🧹 Execute Cleaning Query"):
            try:
                con.execute(cleaning_query)
                st.success("Cleaning query executed successfully! The new clean view is now available.")
            except Exception as e:
                st.error(f"SQL Error: {e}")
                
        st.markdown("### Currently Available Tables & Views")
        tables = con.execute("SHOW TABLES").fetchdf()
        st.dataframe(tables)
    else:
        st.info("Please connect your data folder first.")


# ----------------- PAGE: SQL INSIGHTS -----------------
elif page == "🔍 SQL Insights & Analysis":
    st.title("🔍 SQL Insights & Analysis")
    st.markdown("Write raw SQL queries against your cleaned data to generate insights.")
    
    if csv_files:
        tables = con.execute("SHOW TABLES").fetchdf()
        st.write("**Available Tables/Views:**", ", ".join([f"`{t}`" for t in tables['name']]))
        
        query = st.text_area("Enter your SQL Query to generate insights:", height=150)
        
        if st.button("▶️ Get Insights"):
            try:
                result_df = con.execute(query).fetchdf()
                st.success(f"Insight Generated! ({len(result_df)} rows returned)")
                st.dataframe(result_df, use_container_width=True)
            except Exception as e:
                st.error(f"SQL Error: {e}")


# ----------------- PAGE: DASHBOARD (POWER BI STYLE) -----------------
elif page == "📊 PowerBI-Style Dashboard":
    st.title("📊 Interactive Fitness Dashboard")
    st.markdown("A Tableau/PowerBI style dashboard using **Matplotlib** and **Seaborn**.")
    
    if csv_files:
        tables = con.execute("SHOW TABLES").fetchdf()['name'].tolist()
        
        # Dashboard Controls (like PowerBI slicers)
        st.markdown("### 🎛️ Dashboard Controls")
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            selected_table = st.selectbox("Select Dataset for Dashboard", tables)
            
        try:
            df = con.execute(f"SELECT * FROM {selected_table}").fetchdf()
            
            # Key Performance Indicators (KPIs) like PowerBI KPI cards
            st.markdown("### 📈 Key Metrics")
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if len(numeric_cols) >= 3:
                kpi1, kpi2, kpi3 = st.columns(3)
                kpi1.metric(label=f"Total {numeric_cols[0]}", value=round(df[numeric_cols[0]].sum(), 2))
                kpi2.metric(label=f"Average {numeric_cols[1]}", value=round(df[numeric_cols[1]].mean(), 2))
                kpi3.metric(label=f"Max {numeric_cols[2]}", value=round(df[numeric_cols[2]].max(), 2))
            elif len(numeric_cols) > 0:
                st.metric(label=f"Total {numeric_cols[0]}", value=round(df[numeric_cols[0]].sum(), 2))

            # Visualizations using Seaborn/Matplotlib
            st.markdown("### 🎨 Visualizations")
            
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.subheader("Distribution (Seaborn)")
                if len(numeric_cols) > 0:
                    fig1, ax1 = plt.subplots(figsize=(6, 4))
                    sns.histplot(data=df, x=numeric_cols[0], kde=True, ax=ax1, color="skyblue")
                    ax1.set_title(f"Distribution of {numeric_cols[0]}")
                    st.pyplot(fig1)
                    
            with chart_col2:
                st.subheader("Correlation Scatter (Matplotlib)")
                if len(numeric_cols) >= 2:
                    fig2, ax2 = plt.subplots(figsize=(6, 4))
                    ax2.scatter(df[numeric_cols[0]], df[numeric_cols[1]], alpha=0.5, color="coral")
                    ax2.set_xlabel(numeric_cols[0])
                    ax2.set_ylabel(numeric_cols[1])
                    ax2.set_title(f"{numeric_cols[0]} vs {numeric_cols[1]}")
                    ax2.grid(True, linestyle='--', alpha=0.7)
                    st.pyplot(fig2)
                    
            # Full table view
            st.markdown("### 📋 Detailed Data View")
            st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error building dashboard: {e}")
    else:
        st.info("Please connect your data folder first.")
