import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. SETUP & CONFIG ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 2. TEACHER ACCESS (Sidebar) ---
st.sidebar.title("🍎 Teacher Dashboard")
password = st.sidebar.text_input("Enter Teacher Password", type="password")

# --- MODEL PICKER (Fixes the 404 Error) ---
# We use Gemini 2.5 Flash as it is the current workhorse
available_models = ["gemini-2.5-flash", "gemini-1.5-flash-latest", "gemini-3-flash"]
selected_model_name = st.sidebar.selectbox("Model Version", available_models)
model = genai.GenerativeModel(selected_model_name)

# --- 3. THE PERMANENT MEMO ---
FILE_ID = "1ia4jAk_m3vDGelBD096Mxl13ohG6QChU"
MEMO_URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# --- 4. GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 5. STUDENT PORTAL (Main Page) ---
st.title("📝 Student Marking Portal")
st.write("Upload your work to get instant feedback.")

student_name = st.text_input("Student Full Name:")
uploaded_work = st.file_uploader("Upload your worksheet", type=["jpg", "png", "pdf"])

if st.button("Submit & Mark"):
    if not student_name or not uploaded_work:
        st.error("Please provide both your name and your work.")
    else:
        with st.spinner(f"AI ({selected_model_name}) is marking..."):
            try:
                # A. Read student file
                student_bytes = uploaded_work.read()
                student_mime = uploaded_work.type
                
                # B. Build the request with "inline_data"
                student_part = {
                    "inline_data": {
                        "mime_type": student_mime,
                        "data": student_bytes
                    }
                }
                
                # C. The Instruction Prompt
                prompt = f"""
                You are a teacher. 
                1. Refer to the memo at this link: {MEMO_URL}
                2. Mark the student's uploaded work against that memo.
                3. Provide a Score and corrections.
                """

                # D. Generate Content
                response = model.generate_content([prompt, student_part])
                
                # E. Show Results
                st.subheader(f"Results for {student_name}")
                st.markdown(response.text)
                
                # --- 6. SEND TO GOOGLE SHEETS ---
                new_data = pd.DataFrame([{
                    "Student": student_name, 
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Marking_Details": response.text[:1000] 
                }])
                conn.create(data=new_data)
                st.success("Your mark has been recorded!")

            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.info("Try switching the 'Model Version' in the sidebar.")