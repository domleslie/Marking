import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. SETUP & BRAIN CONFIG ---
# Ensure GEMINI_API_KEY is in your Streamlit Secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. THE PERMANENT MEMO ---
# Your Direct Link ID (Extracted from your URL)
FILE_ID = "1ia4jAk_m3vDGelBD096Mxl13ohG6QChU"
# Direct download link for the AI to "read" the file
MEMO_URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# --- 3. GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 4. TEACHER ACCESS (Sidebar) ---
st.sidebar.title("🍎 Teacher Access")
password = st.sidebar.text_input("Enter Password", type="password")

# Check password from secrets, default to 'admin123' if not set
if password == st.secrets.get("TEACHER_PASSWORD", "admin123"):
    st.sidebar.success("Teacher Mode Active")
    st.sidebar.info(f"Using Memo ID: {FILE_ID}")

# --- 5. STUDENT PORTAL (Main) ---
st.title("📝 Student Marking Portal")
st.write("Upload your work (Image or PDF) to get instant feedback.")

student_name = st.text_input("Full Name:")
uploaded_work = st.file_uploader("Upload your worksheet", type=["jpg", "png", "pdf"])

if st.button("Submit & Mark"):
    if not student_name or not uploaded_work:
        st.error("Please provide your name and upload your work!")
    else:
        with st.spinner("AI Teacher is marking..."):
            try:
                # 1. Read student file
                student_bytes = uploaded_work.read()
                student_mime = uploaded_work.type
                
                # 2. Build the request using the exact keys the error asked for
                # 'inline_data' is for the student's file
                student_part = {"inline_data": {"mime_type": student_mime, "data": student_bytes}}
                
                # For the Memo, we will provide the URL as text in the prompt 
                # because Google Drive URLs work best when the AI 'fetches' them via text instructions
                instruction_prompt = f"""
                You are a teacher. 
                1. Access the official memo here: {MEMO_URL}
                2. Mark the attached student work against that memo.
                3. Provide a score and corrections.
                """

                # 3. Call the model
                response = model.generate_content([instruction_prompt, student_part])
                
                # Show results
                st.subheader(f"Results for {student_name}")
                st.markdown(response.text)
                
                # 4. Save to Sheets
                new_row = pd.DataFrame([{
                    "Student": student_name, 
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "AI_Feedback": response.text[:1000]
                }])
                conn.create(data=new_row)
                st.success("Result recorded!")

            except Exception as e:
                st.error(f"Something went wrong: {e}")