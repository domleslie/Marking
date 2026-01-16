import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
from google.generativeai import types
from streamlit_gsheets import GSheetsConnection

# --- 1. SETUP & BRAIN CONFIG ---
# Ensure GEMINI_API_KEY is in your Streamlit Secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. THE PERMANENT MEMO ---
# Your Direct Link ID (Extracted from your URL)
FILE_ID = "1ia4jAk_m3vDGelBD096Mxl13ohG6QChU"
MEMO_URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# --- 3. GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 4. TEACHER ACCESS (Sidebar) ---
st.sidebar.title("🍎 Teacher Access")
password = st.sidebar.text_input("Enter Password", type="password")
if password == st.secrets.get("TEACHER_PASSWORD", "admin123"):
    st.sidebar.success("Teacher Mode Active")
    st.sidebar.info("The AI is currently using the Google Drive Memo link.")

# --- 5. STUDENT PORTAL (Main) ---
st.title("📝 Student Marking Portal")
st.write("Upload your work to get instant feedback.")

student_name = st.text_input("Full Name:")
# Added 'pdf' to the types here
uploaded_work = st.file_uploader("Upload your worksheet (JPEG/PNG/PDF)", type=["jpg", "png", "pdf"])

if st.button("Submit & Mark"):
    if not student_name or not uploaded_work:
        st.error("Please provide your name and upload your work!")
    else:
        with st.spinner("AI Teacher is marking..."):
            # A. Process Student Work (Bytes work for both PDF and Image)
            student_bytes = uploaded_work.read()
            student_mime = uploaded_work.type
            
            # B. The AI Prompt
            prompt = """
            1. Look at the provided MEMO (the URL file).
            2. Mark the STUDENT WORK (uploaded file) strictly against the memo.
            3. Award marks and provide brief corrections for any mistakes.
            4. Start your response with 'SCORE: [X]/[Total]'
            """
            
            # C. Send to Gemini
            # Note: types.Part.from_uri handles the remote memo
            # types.Part.from_bytes handles the local student upload
            try:
                response = model.generate_content([
                    prompt,
                    types.Part.from_uri(uri=MEMO_URL, mime_type="image/jpeg"), 
                    types.Part.from_bytes(data=student_bytes, mime_type=student_mime)
                ])
                
                # Show results to student
                st.subheader(f"Results for {student_name}")
                st.markdown(response.text)
                
                # --- 6. SEND TO GOOGLE SHEETS ---
                new_row = pd.DataFrame([{
                    "Student": student_name, 
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "AI_Feedback": response.text[:500] # Saves first 500 chars to the sheet
                }])
                
                conn.create(data=new_row)
                st.success("Your mark has been recorded in the Gradebook!")

            except Exception as e:
                st.error(f"An error occurred: {e}")