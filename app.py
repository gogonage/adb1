import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

# 1. Setup API Key from Secrets
API_KEY = st.secrets.get("GEMINI_API_KEY")

st.title("🏦 Bank Statement ADB Analyzer")
st.write("Professional Tool for Small Business Loan DSA")

# 2. Corrected File Uploader
uploaded_file = st.file_uploader("Upload your PDF statement", type="pdf")

if st.button("Run Analysis"):
    if not API_KEY:
        st.error("API Key missing! Please add GEMINI_API_KEY to Streamlit Secrets.")
    elif not uploaded_file:
        st.warning("Please upload a PDF file first.")
    else:
        with st.spinner("Analyzing..."):
            # Your AI logic here
            st.success("Key found and file uploaded!")
