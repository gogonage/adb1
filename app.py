import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from datetime import datetime

# --- APP CONFIGURATION ---
st.set_page_config(page_title="ADB Analyzer Pro", page_icon="🏦", layout="wide")

# Securely fetch the API Key from Streamlit Secrets
# Setup: Streamlit Cloud > Settings > Secrets > GEMINI_API_KEY = "your_key"
API_KEY = st.secrets.get("GEMINI_API_KEY")

def extract_bank_data(uploaded_file):
    """Uses Gemini 1.5 Flash to extract structured transaction data from PDF."""
    if not API_KEY:
        st.error("API Key missing! Add GEMINI_API_KEY to Streamlit Secrets.")
        return None
    
    genai.configure(api_key=API_KEY)
    
    # FIXED: Using 'gemini-1.5-flash-latest' to avoid 404/version errors
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    pdf_content = uploaded_file.getvalue()
    pdf_parts = [{"mime_type": "application/pdf", "data": pdf_content}]
    
    prompt = """
    Act as a professional financial auditor. Extract the transaction history from this bank statement.
    RULES:
    1. Identify the 'Date' and the 'Running Balance' for every transaction.
    2. If a single day has multiple transactions, ONLY return the final closing balance for that day.
    3. Format all dates as YYYY-MM-DD.
    4. Return ONLY a JSON list of objects. No prose or explanations.
    
    EXAMPLE OUTPUT:
    [{"date": "2025-01-01", "balance": 15000.50}, {"date": "2025-01-05", "balance": 12000.00}]
    """
    
    try:
        response = model.generate_content([prompt, pdf_parts[0]])
        # Clean the AI text to ensure it's pure JSON
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw_text)
    except Exception as e:
        st.error(f"AI Extraction Error: {e}")
        return None

# --- USER INTERFACE ---
st.title("🏦 Bank Statement ADB Analyzer")
st.markdown("##### Accurate Average Daily Balance Tool for Business Loan DSAs")

# Sidebar for inputs
with st.sidebar:
    st.header("1. Upload Statement")
    uploaded_file = st.file_uploader("Upload Bank PDF", type="pdf")
    
    st.divider()
    st.header("2. Analysis Period")
    st.write("Select the range to calculate ADB:")
    start_date = st.date_input("Start Date", value=datetime(2025, 1, 1))
    end_date = st.date_input("End Date", value=datetime.now())

# Main Analysis Logic
if uploaded_file:
    if st.button("🚀 Calculate Verified ADB"):
        with st.spinner("AI is analyzing transaction tables..."):
            data = extract_bank_data(uploaded_file)
            
            if data:
                # 1. Prepare DataFrame
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                
                # 2. Handle duplicates (Keep only the last balance for each date)
                df = df.sort_values('date').drop_duplicates('date', keep='last')
                df = df.set_index('date')
                
                # 3. ACCURACY ENGINE: Create a range for EVERY day in the period
                analysis_range = pd.date_range(start=start_date, end=end_date, freq='D')
                
                # 4. Fill gaps (Forward Fill): If no transaction on Saturday, use Friday's balance
                df_complete = df.reindex(analysis_range).ffill().fillna(0)
                
                # 5. Final ADB Calculation (Sum of all daily balances / Number of days)
                adb_result = df_complete['balance'].mean()
                
                # --- RESULTS DISPLAY ---
                st.success("Analysis Complete")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Calculated ADB", f"₹{adb_result:,.2f}")
                col2.metric("Total Days in Period", len(analysis_range))
                col3.metric("Final Balance", f"₹{df_complete['balance'].iloc[-1]:,.2f}")
                
                # Visualizations
                st.subheader("Daily Balance Stability Trend")
                st.line_chart(df_complete['balance'])
                
                with st.expander("View Daily Balance Sheet (Excel Style)"):
                    st.dataframe(df_complete)
            else:
                st.error("Extraction failed. Ensure the PDF is clear and not password-protected.")
else:
    st.info("Awaiting PDF upload to begin analysis.")
