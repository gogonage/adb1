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
    """Uses Gemini to extract structured transaction data from PDF."""
    if not API_KEY:
        st.error("API Key missing! Add GEMINI_API_KEY to Streamlit Secrets.")
        return None
    
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Prepare the PDF for the AI
    pdf_content = uploaded_file.getvalue()
    pdf_parts = [{"mime_type": "application/pdf", "data": pdf_content}]
    
    prompt = """
    Act as a professional bank auditor. Extract the transaction history from this bank statement.
    RULES:
    1. Focus ONLY on the 'Date' and the 'Running Balance' (closing balance) for that day.
    2. If a day has multiple transactions, only take the LAST balance of that day.
    3. Format all dates as YYYY-MM-DD.
    4. Return ONLY a JSON list of objects.
    
    EXAMPLE OUTPUT:
    [{"date": "2024-01-01", "balance": 15000.50}, {"date": "2024-01-05", "balance": 12000.00}]
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
st.markdown("##### Accurate Average Daily Balance Tool for Business Loans")

# Sidebar for inputs
with st.sidebar:
    st.header("1. Upload Statement")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    
    st.divider()
    st.header("2. Analysis Period")
    start_date = st.date_input("Start Date", value=datetime(2024, 1, 1))
    end_date = st.date_input("End Date", value=datetime.now())

# Main Logic
if uploaded_file:
    if st.button("🚀 Calculate Final ADB"):
        with st.spinner("AI is analyzing balances..."):
            data = extract_bank_data(uploaded_file)
            
            if data:
                # Convert to Dataframe
                df = pd.DataFrame(data)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').drop_duplicates('date', keep='last')
                df = df.set_index('date')
                
                # --- ACCURACY ENGINE ---
                # This fills in the gaps for days where no transactions happened
                analysis_range = pd.date_range(start=start_date, end=end_date, freq='D')
                df_complete = df.reindex(analysis_range).ffill().fillna(0)
                
                # Final Calculation
                adb_result = df_complete['balance'].mean()
                
                # --- RESULTS DISPLAY ---
                st.success("Analysis Finished Successfully")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Average Daily Balance", f"₹{adb_result:,.2f}")
                col2.metric("Days Analyzed", len(analysis_range))
                col3.metric("Final Closing Balance", f"₹{df_complete['balance'].iloc[-1]:,.2f}")
                
                st.subheader("Daily Balance Trend")
                st.line_chart(df_complete['balance'])
                
                with st.expander("View Daily Data Table"):
                    st.dataframe(df_complete)
            else:
                st.error("Failed to extract data. Please check the PDF quality.")
else:
    st.info("Please upload a PDF statement to begin the analysis.")
