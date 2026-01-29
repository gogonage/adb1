import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="ADB Analyzer Pro", page_icon="📊", layout="wide")

# Securely get API Key from Streamlit Secrets
# Set this in Streamlit Cloud: Settings > Secrets
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

def extract_data_with_ai(uploaded_file):
    if not API_KEY:
        st.error("API Key missing! Please add GEMINI_API_KEY to Streamlit Secrets.")
        return None
    
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    pdf_parts = [{"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
    prompt = """
    Extract the transaction history from this bank statement. 
    Return ONLY a JSON list of objects with "date" (YYYY-MM-DD) and "balance" (number).
    Example: [{"date": "2024-01-01", "balance": 50000.00}]
    """
    
    try:
        response = model.generate_content([prompt, pdf_parts[0]])
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        st.error(f"AI Extraction Error: {e}")
        return None

# --- UI INTERFACE ---
st.title("🏦 Bank Statement ADB Analyzer")
st.markdown("### Professional Tool for Small Business Loan DSA")

with st.sidebar:
    st.header("Settings")
    uploaded_file = st.file_uploader("Upload Bank Statement (PDF)", type="pdf")
    
    st.divider()
    st.write("Analysis Period:")
    start_date = st.date_input("Start Date", value=datetime(2024, 1, 1))
    end_date = st.date_input("End Date", value=datetime.now())

if uploaded_file:
    if st.button("Run Analysis"):
        with st.spinner("AI is reading the statement..."):
            raw_data = extract_data_with_ai(uploaded_file)
            
            if raw_data:
                # Process Data
                df = pd.DataFrame(raw_data)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').drop_duplicates('date', keep='last')
                df = df.set_index('date')

                # Apply Date Range & Reindex for ADB
                full_range = pd.date_range(start=start_date, end=end_date, freq='D')
                df_final = df.reindex(full_range).ffill().fillna(0) # Fill gaps with last balance

                # Calculations
                adb_value = df_final['balance'].mean()

                # --- DISPLAY RESULTS ---
                st.success("Analysis Complete")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Average Daily Balance (ADB)", f"₹{adb_value:,.2f}")
                
                st.subheader("Balance Trend Over Selected Period")
                st.line_chart(df_final['balance'])
                
                with st.expander("View Daily Balance Sheet"):
                    st.dataframe(df_final)
else:
    st.info("Please upload a PDF statement and select your date range to begin.")
