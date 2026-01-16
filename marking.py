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
                # A. Process Student Work into bytes
                student_bytes = uploaded_work.read()
                student_mime = uploaded_work.type
                
                # B. The AI Prompt
                prompt = """
                You are a teacher marking a student's work.
                1. Use the provided MEMO URL as the source of truth for correct answers.
                2. Mark the STUDENT WORK provided in the bytes.
                3. Provide a clear total score.
                4. List specific corrections for any mistakes.
                """
                
                # C. The "Dictionary Method" to avoid Part errors
                # This sends the memo from Drive and the student file from the uploader
                response = model.generate_content([
                    prompt,
                    {"mime_type": "image/jpeg", "part_metadata": {"file_uri": MEMO_URL}}, 
                    {"mime_type": student_mime, "data": student_bytes}
                ])
                
                # Show results to student
                st.subheader(f"Results for {student_name}")
                st.markdown(response.text)
                
                # --- 6. SEND TO GOOGLE SHEETS ---
                new_row = pd.DataFrame([{
                    "Student": student_name, 
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "AI_Feedback": response.text[:1000] # Limit characters for the sheet cell
                }])
                
                # Append to your Google Sheet
                conn.create(data=new_row)
                st.success("Your mark has been recorded in the Gradebook!")

            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.info("Check if your Gemini API key and Google Sheet URL are correct in Secrets.")