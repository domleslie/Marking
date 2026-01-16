import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. SETUP & CONFIG ---
# Ensure your GEMINI_API_KEY is in Streamlit Secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# FIX: We use 'gemini-1.5-flash' which the library maps to the stable v1 API
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 2. THE PERMANENT MEMO ---
FILE_ID = "1ia4jAk_m3vDGelBD096Mxl13ohG6QChU"
MEMO_URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# --- 3. GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 4. TEACHER ACCESS (Sidebar) ---
st.sidebar.title("🍎 Teacher Access")
password = st.sidebar.text_input("Enter Teacher Password", type="password")

# --- 5. STUDENT PORTAL (Main Page) ---
st.title("📝 Student Marking Portal")
st.write("Upload your work to get instant feedback.")

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
                
                # B. The Prompt
                # We mention the Memo URL here for the AI to "look" at it
                prompt = f"""
                You are a teacher marking a worksheet.
                1. Refer to the official memo image at this link: {MEMO_URL}
                2. Mark the student's uploaded work against that memo.
                3. Provide a clear Score and brief corrections.
                """
                
                # C. The Stable Data Format
                # We wrap the bytes in a dictionary that the model understands
                student_data = {
                    "mime_type": student_mime,
                    "data": student_bytes
                }

                # D. Generate Content (The Action)
                # We pass the prompt and the data as a list
                response = model.generate_content([prompt, student_data])
                
                # E. Show results
                st.subheader(f"Results for {student_name}")
                st.markdown(response.text)
                
                # --- 6. SEND TO GOOGLE SHEETS ---
                new_data = pd.DataFrame([{
                    "Student": student_name, 
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Marking_Details": response.text[:1000] 
                }])
                
                conn.create(data=new_data)
                st.success("Your mark has been recorded in the gradebook!")

            except Exception as e:
                # This catches any remaining errors and shows them clearly
                st.error(f"Something went wrong: {e}")