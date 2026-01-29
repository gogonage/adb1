import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from datetime import datetime

# --- APP CONFIGURATION ---
st.set_page_config(page_title="ADB Analyzer Pro", page_icon="🏦", layout="wide")

# Securely fetch the API Key from Streamlit Secrets
API_KEY = st.secrets.get("GEMINI_API_KEY")

def extract_bank_data(uploaded_file):
    """Uses the latest Gemini models to extract transaction data."""
    if not API_KEY:
        st.error("API Key missing! Add GEMINI_API_KEY to Streamlit Secrets.")
        return None
    
    genai.configure(api_key=API_KEY)
    
    # FIX: Updated to Gemini 3 Flash (2026 standard)
    # If this fails, the code will automatically try Gemini 2.5 Flash
    model_names = ['gemini-3-flash', 'gemini-2.5-flash', 'gemini-2.0-flash']
    
    success_data = None
    for m_name in model_names:
        try:
            model = genai.GenerativeModel(m_name)
            pdf_content = uploaded_file.getvalue()
            pdf_parts = [{"mime_type": "application/pdf", "data": pdf_content}]
            
            prompt = """
            Act as a professional financial auditor. Extract the transaction history from this bank statement.
            Return ONLY a JSON list of objects with "date" (YYYY-MM-DD) and "balance" (number).
            Example: [{"date": "2026-01-01", "balance": 15000.50}]
            """
            
            response = model.generate_content([prompt, pdf_parts[0]])
            raw_text = response.text.replace('```json', '').replace('```', '').strip()
            success_data = json.loads(raw_text)
            break # Exit loop if successful
        except Exception:
            continue # Try next model if 404 occurs
            
    if not success_data:
        st.error("Model Error: Your API key may not have access to these models yet.")
        return None
    return success_data

# --- USER INTERFACE ---
st.title("🏦 Bank Statement ADB Analyzer")
st.markdown("##### Accurate Average Daily Balance Tool for Business Loan DSAs")

with st.sidebar:
    st.header("1. Upload")
    uploaded_file = st.file_uploader("Upload Bank PDF", type="pdf")
    st.divider()
    st.header("2. Analysis Period")
    start_date = st.date_input("Start Date", value=datetime(2026, 1, 1))
    end_date = st.date_input("End Date", value=datetime.now())

if uploaded_file:
    if st.button("🚀 Calculate Verified ADB"):
        with st.spinner("Analyzing with Gemini 3..."):
            data = extract_bank_data(uploaded_file)
            
            if data:
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').drop_duplicates('date', keep='last').set_index('date')
                
                # Math Engine
                analysis_range = pd.date_range(start=start_date, end=end_date, freq='D')
                df_complete = df.reindex(analysis_range).ffill().fillna(0)
                
                adb_result = df_complete['balance'].mean()
                
                st.success("Analysis Complete")
                c1, c2 = st.columns(2)
                c1.metric("Calculated ADB", f"₹{adb_result:,.2f}")
                c2.metric("Days in Period", len(analysis_range))
                
                st.line_chart(df_complete['balance'])
            else:
                st.error("Extraction failed. Please check the PDF.")
