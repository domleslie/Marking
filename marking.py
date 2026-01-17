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
available_models = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
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
        st.error("Please provide both your name and your work.")
    else:
        with st.spinner(f"AI ({selected_model_name}) is marking..."):
            try:
                # 1. Prepare File
                file_bytes = uploaded_work.read()
                
                # 2. THE RIGID PROMPT (Forces Structured Output)
                prompt = f"""
                You are a teacher marking against this memo: {MEMO_URL}
                
                Mark the uploaded student work and respond ONLY in the following JSON format:
                {{
                    "feedback": "Your detailed comments for the student here",
                    "score": "The numeric score, e.g., 18/20"
                }}
                """

                # 3. Request (Note the 'response_mime_type' setting)
                response = model.generate_content(
                    [prompt, {"mime_type": uploaded_work.type, "data": file_bytes}],
                    generation_config={"response_mime_type": "application/json"}
                )
                
                # 4. Parse the JSON
                import json
                result = json.loads(response.text)
                
                feedback_text = result.get("feedback", "No feedback provided.")
                final_score = result.get("score", "N/A")

                # 5. Display to Student
                st.subheader(f"Results for {student_name}")
                st.info(f"**Final Score: {final_score}**")
                st.markdown(feedback_text)
                
                # 6. SAVE TO GOOGLE SHEETS
                new_row = pd.DataFrame([{
                    "Student": student_name, 
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Mark": final_score
                }])
                conn.create(data=new_row)
                st.success("Your mark has been saved!")

            except Exception as e:
                st.error(f"Something went wrong: {e}")