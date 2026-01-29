import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="ADB Analyzer Pro", page_icon="📊", layout="wide")

# This looks for your key in the Streamlit Cloud "Secrets" section
API_KEY = st.secrets.get("GEMINI_API_KEY")

def extract_bank_data(uploaded_file):
    """Uses Gemini to extract structured transaction data from PDF."""
    if not API_KEY:
        st.error("API Key missing! Please go to Streamlit Settings > Secrets and add: GEMINI_API_KEY = 'your_key_here'")
        return None
    
    genai.configure(api_key=API_KEY)
    # Using Flash for speed and cost-efficiency
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    pdf_content = uploaded_file.getvalue()
    pdf_parts = [{"mime_type": "application/pdf", "data": pdf_content}]
    
    prompt = """
    Act as a professional bank auditor for Indian business loans. 
    Extract the transaction history from this bank statement.
    
    RULES:
    1. Focus ONLY on the 'Date' and the 'Running Balance' (closing balance) for that day.
    2. If a day has multiple transactions, ONLY take the final closing balance for that date.
    3. Format dates as YYYY-MM-DD.
    4. Return ONLY a JSON list of objects.
    
    EXAMPLE: [{"date": "2024-01-01", "balance": 45000.00}, {"date": "2024-01-02", "balance": 42000.00}]
    """
    
    try:
        response = model.generate_content([prompt, pdf_parts[0]])
        # Clean text to ensure only JSON remains
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw_text)
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

# --- UI INTERFACE ---
st.title("🏦 Bank Statement ADB Analyzer")
st.markdown("##### Accurate Average Daily Balance Tool for Business Loan DSAs")

# Sidebar for inputs
with st.sidebar:
    st.header("1. Upload File")
    uploaded_file = st.file_uploader("Upload Bank Statement (PDF)", type="pdf")
    
    st.divider()
    st.header("2. Set Date Range")
    st.info("Select the exact month or period you want to calculate ADB for.")
    start_date = st.date_input("Start Date", value=datetime(2025, 1, 1))
    end_date = st.date_input("End Date", value=datetime.now())

# Main Logic
if uploaded_file:
    if st.button("🚀 Calculate Verified ADB"):
        with st.spinner("AI is analyzing transaction tables..."):
            data = extract_bank_data(uploaded_file)
            
            if data:
                # Create DataFrame
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                # Ensure we only have one balance per day (the last one)
                df = df.sort_values('date').drop_duplicates('date', keep='last')
                df = df.set_index('date')
                
                # --- CALCULATION ENGINE ---
                # Create a range for EVERY day in your selected period
                analysis_range = pd.date_range(start=start_date, end=end_date, freq='D')
                
                # Reindex fills in missing dates; ffill() carries the last balance forward
                df_complete = df.reindex(analysis_range).ffill().fillna(0)
                
                # Math: Sum of daily balances / total number of days
                adb_result = df_complete['balance'].mean()
                
                # --- DISPLAY ---
                st.success("Calculations Complete")
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Calculated ADB", f"₹{adb_result:,.2f}")
                m2.metric("Total Days in Period", len(analysis_range))
                m3.metric("Closing Balance", f"₹{df_complete['balance'].iloc[-1]:,.2f}")
                
                st.subheader("Daily Balance Stability")
                st.line_chart(df_complete['balance'])
                
                with st.expander("View Full Daily Breakdown"):
                    st.write("This table shows the balance for every single day in your range.")
                    st.dataframe(df_complete)
            else:
                st.error("No data extracted. Ensure the PDF is not password-protected.")
else:
    st.info("Awaiting PDF upload...")
