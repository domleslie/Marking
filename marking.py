import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
from google.generativeai import types # Important for PDF support

# Line 1: The 'Permanent' link to your memo (replace with your direct link)
MEMO_URL = "https://drive.google.com/file/d/1ia4jAk_m3vDGelBD096Mxl13ohG6QChU/view?usp=drive_link"

# Line 2: Adding the URL directly into the AI's content list
response = model.generate_content([prompt, types.Part.from_uri(uri=MEMO_URL, mime_type="image/jpeg"), student_img])

# --- 1. SETUP ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. TEACHER SECTION: THE MEMO ---
st.sidebar.title("🍎 Teacher Dashboard")
memo_file = st.sidebar.file_uploader("Upload Official Memo (PDF/JPEG)", type=["pdf", "jpg", "png"], key="memo")

# --- 3. GOOGLE SHEETS CONNECTION (The 4 Lines) ---
from streamlit_gsheets import GSheetsConnection
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 4. STUDENT SECTION ---
st.title("📝 Student Marking Portal")
student_name = st.text_input("Enter your name:")
uploaded_work = st.file_uploader("Upload your worksheet (JPEG/PNG)", type=["jpg", "png"], key="work")

if st.button("Submit & Mark") and memo_file and uploaded_work:
    # Prepare the memo for the AI
    memo_bytes = memo_file.read()
    memo_mime = "application/pdf" if memo_file.type == "application/pdf" else "image/jpeg"
    
    # Prepare the student work
    student_img = Image.open(uploaded_work)
    
    with st.spinner("AI Teacher is marking..."):
        # The prompt that links the two files
        prompt = "Compare the student's work in the image to the official memo provided. Calculate a total score and list corrections."
        
        # Send both the Memo and the Work to Gemini
        response = model.generate_content([
            prompt,
            types.Part.from_bytes(data=memo_bytes, mime_type=memo_mime),
            student_img
        ])
        
        st.markdown(response.text)
        
        # --- SEND TO GOOGLE SHEETS ---
        # We extract a rough score (this logic can be refined)
        new_row = pd.DataFrame([{"Student": student_name, "Date": datetime.now(), "Feedback": response.text[:100]}])
        conn.create(data=new_row)
        st.success("Result saved to Google Sheets!")