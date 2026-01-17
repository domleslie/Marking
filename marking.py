import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import re

# --- 1. SETUP ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 2. TEACHER SIDEBAR ---
st.sidebar.title("🍎 Teacher Dashboard")
available_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
selected_model_name = st.sidebar.selectbox("Model Version", available_models)
model = genai.GenerativeModel(selected_model_name)

# --- 3. THE PERMANENT MEMO ---
FILE_ID = "1ia4jAk_m3vDGelBD096Mxl13ohG6QChU"
MEMO_URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# --- 4. GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 5. STUDENT PORTAL ---
st.title("📝 Student Marking Portal")
student_name = st.text_input("Student Full Name:")
uploaded_work = st.file_uploader("Upload Work", type=["jpg", "png", "pdf"])

if st.button("Submit & Mark"):
    if not student_name or not uploaded_work:
        st.error("Please provide name and work.")
    else:
        with st.spinner("AI is calculating the mark..."):
            try:
                # File Processing
                file_bytes = uploaded_work.read()
                
                # REFINED PROMPT: Tells AI to end with a clear tag
                prompt = f"""
                Compare the work to this memo: {MEMO_URL}.
                1. Provide detailed feedback for the student to read.
                2. At the very end of your response, provide the final score in this EXACT format:
                   SCORE: [number]/[total]
                """
                
                response = model.generate_content([
                    prompt,
                    {"mime_type": uploaded_work.type, "data": file_bytes}
                ])
                
                full_text = response.text
                
                # --- EXTRACTION LOGIC ---
                # This looks for the "SCORE: 15/20" tag at the end
                score_match = re.search(r"SCORE:\s*(\d+/\d+)", full_text)
                final_score = score_match.group(1) if score_match else "N/A"
                
                # Show full feedback to student
                st.subheader("Feedback")
                st.markdown(full_text)
                
                # --- 6. CLEAN GOOGLE SHEETS ENTRY ---
                # We create columns for Name, Date, and Mark (Score)
                new_row = pd.DataFrame([{
                    "Student": student_name, 
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Mark": final_score
                }])
                
                # Add it to the sheet
                conn.create(data=new_row)
                st.success(f"Success! {student_name}'s mark ({final_score}) is now in the Gradebook.")

            except Exception as e:
                st.error(f"Error: {e}")