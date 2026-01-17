import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime

# --- 1. SETUP ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. THE PERMANENT MEMO ---
FILE_ID = "1ia4jAk_m3vDGelBD096Mxl13ohG6QChU"
MEMO_URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# --- 3. STUDENT PORTAL ---
st.title("📝 Student Marking Portal")
student_name = st.text_input("Full Name:")
uploaded_work = st.file_uploader("Upload your worksheet", type=["jpg", "png", "pdf"])

if st.button("Submit & Mark"):
    if not student_name or not uploaded_work:
        st.error("Please provide your name and work.")
    else:
        with st.spinner("AI Marking in progress..."):
            try:
                # Process File
                student_bytes = uploaded_work.read()
                student_mime = uploaded_work.type
                
                # Mark with Gemini
                prompt = f"Mark this work against the memo at {MEMO_URL}. Give a score."
                response = model.generate_content([
                    prompt,
                    {"inline_data": {"mime_type": student_mime, "data": student_bytes}}
                ])
                
                st.markdown(response.text)

                # --- 4. THE EASY SHEETS WAY (Google Forms Bypass) ---
                # We use a simple trick: Sending data via a URL 
                # OR using the st-gsheets-connection in 'public' mode
                from streamlit_gsheets import GSheetsConnection
                conn = st.connection("gsheets", type=GSheetsConnection)
                
                new_row = pd.DataFrame([{
                    "Student": student_name,
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Feedback": response.text[:500]
                }])
                
                # Because the sheet is public, this requires MINIMAL secrets
                conn.create(data=new_row)
                st.success("Recorded in Sheet!")

            except Exception as e:
                st.error(f"Error: {e}")