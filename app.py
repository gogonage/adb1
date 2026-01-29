import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="ADB Analyzer Pro", page_icon="📊", layout="wide")

# Securely fetch API Key from Streamlit Secrets
API_KEY = st.secrets.get("GEMINI_API_KEY")

def extract_bank_data(uploaded_file):
    """Uses Gemini to extract structured transaction data from PDF."""
    if not API_KEY:
        st.error("API Key missing! Add it to Streamlit Secrets.")
        return None
    
    # Configure the library
    genai.configure(api_key=API_KEY)
    
    # FIXED MODEL STRING: Using 'gemini-1.5-flash-latest' for better compatibility
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    pdf_content = uploaded_file.getvalue()
    pdf_parts = [{"mime_type": "application/pdf", "data": pdf_content}]
    
    prompt = """
    Act as a professional bank auditor. Extract the transaction history from this bank statement.
    RULES:
    1. Focus ONLY on the 'Date' and the 'Running Balance' (closing balance) for that day.
    2. Format all dates as YYYY-MM-DD.
    3. Return ONLY a JSON list of objects.
    Example: [{"date": "2025-01-01", "balance": 15000.50}]
    """
    
    try:
        # Standard call without beta version overrides
        response = model.generate_content([prompt, pdf_parts[0]])
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw_text)
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

# --- UI INTERFACE ---
st.title("🏦 Bank Statement ADB Analyzer")
st.markdown("##### Professional Tool for Business Loan DSAs")

with st.sidebar:
    st.header("1. Upload")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    st.divider()
    st.header("2. Period")
    start_date = st.date_input("Start Date", value=datetime(2025, 1, 1))
    end_date = st.date_input("End Date", value=datetime.now())

if uploaded_file:
    if st.button("🚀 Calculate Verified ADB"):
        with st.spinner("AI is analyzing transaction tables..."):
            data = extract_bank_data(uploaded_file)
            
            if data:
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').drop_duplicates('date', keep='last').set_index('date')
                
                # Accuracy Engine
                analysis_range = pd.date_range(start=start_date, end=end_date, freq='D')
                df_complete = df.reindex(analysis_range).ffill().fillna(0)
                
                adb_result = df_complete['balance'].mean()
                
                st.success("Analysis Complete")
                m1, m2 = st.columns(2)
                m1.metric("Average Daily Balance", f"₹{adb_result:,.2f}")
                m2.metric("Days in Period", len(analysis_range))
                
                st.line_chart(df_complete['balance'])
            else:
                st.error("Could not extract data. Please check PDF quality.")
else:
    st.info("Upload a statement to begin.")
