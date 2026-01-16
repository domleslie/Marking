import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. SETUP & CONFIG ---
# Ensure your GEMINI_API_KEY is in Streamlit Secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Use the most stable model name to avoid 404 errors
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. THE PERMANENT MEMO ---
# Your direct download link for the memo image/PDF
FILE_ID = "1ia4jAk_m3vDGelBD096Mxl13ohG6QChU"
MEMO_URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# --- 3. GOOGLE SHEETS CONNECTION ---
# This looks for [connections.gsheets] in your secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 4. TEACHER ACCESS (Sidebar) ---
st.sidebar.title("🍎 Teacher Access")
password = st.sidebar.text_input("Enter Teacher Password", type="password")

# --- 5. STUDENT PORTAL (Main Page) ---
st.title("📝 Student Marking Portal")
st.write("Upload your work to get instant feedback from the AI.")

student_name = st.text_input("Student Full Name:")
uploaded_work = st.file_uploader("Upload your worksheet (JPG, PNG, or PDF)", type=["jpg", "png", "pdf"])

if st.button("Submit & Mark"):
    if not student_name or not uploaded_work:
        st.error("Please provide both your name and your work.")
    else:
        with st.spinner("AI Teacher is marking..."):
            try:
                # A. Read the student file bytes
                student_bytes = uploaded_work.read()
                student_mime = uploaded_work.type
                
                # B. The Prompt (Points the AI to your Drive Memo)
                prompt = f"""
                You are a math teacher marking a worksheet.
                1. Use the official memo found at this link: {MEMO_URL}
                2. Mark the attached student work strictly against that memo.
                3. Provide a clear Score (e.g., 15/20) and a list of corrections.
                """
                
                # C. The "Inline Data" format (Fixes the Dict error)
                student_part = {
                    "inline_data": {
                        "mime_type": student_mime,
                        "data": student_bytes
                    }
                }

                # D. Generate Content
                response = model.generate_content([prompt, student_part])
                
                # E. Show results to student
                st.subheader(f"Results for {student_name}")
                st.markdown(response.text)
                
                # --- 6. SEND TO GOOGLE SHEETS ---
                # We create a single-row DataFrame to append
                new_data = pd.DataFrame([{
                    "Student": student_name, 
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Marking_Details": response.text[:1000] # Limits text size for the sheet
                }])
                
                # This appends the row to your existing sheet
                conn.create(data=new_data)
                st.success("Your mark has been successfully recorded in the gradebook!")

            except Exception as e:
                st.error(f"Something went wrong: {e}")