import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import json
from PIL import Image
import io

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

# --- 4. GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 5. STUDENT PORTAL ---
st.title("📝 Student Marking Portal")
student_name = st.text_input("Student Full Name:")
uploaded_work = st.file_uploader("Upload Work", type=["jpg", "png", "jpeg", "pdf"])

if st.button("Submit & Mark"):
    if not student_name or not uploaded_work:
        st.error("Please provide name and work.")
    else:
        with st.spinner(f"AI is marking {student_name}'s work..."):
            try:
                # --- FORMAT HANDLING ---
                if uploaded_work.type == "application/pdf":
                    # PDF: Send directly without resizing
                    file_data = uploaded_work.read()
                    mime_type = "application/pdf"
                else:
                    # IMAGE: Optimize to prevent 500 errors
                    img = Image.open(uploaded_work)
                    img.thumbnail((1024, 1024))
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG')
                    file_data = img_byte_arr.getvalue()
                    mime_type = "image/jpeg"
                
                # Personalized JSON Prompt
                prompt = f"""
                You are a teacher. Mark this work against the memo at {MEMO_URL}.
                For the sake of consistency mark the work ten times and then take the average score rounded to the nearest whole number as the final result.
                The student's name is {student_name}.
                Address them by name in the feedback.
                The feedback must be detailed and particularly focused on where the student lost their marks.
                The feedback must be clear.
                
                Respond ONLY in this JSON format:
                {{
                    "personalized_feedback": "Hello {student_name}, ...",
                    "score": "X/Total"
                }}
                """
                
                response = model.generate_content(
                    [prompt, {"mime_type": mime_type, "data": file_data}],
                    generation_config={"response_mime_type": "application/json"}
                )
                
                result = json.loads(response.text)
                feedback = result.get("personalized_feedback")
                score = result.get("score")

                st.subheader(f"Results for {student_name}")
                st.info(f"**Score: {score}**")
                st.markdown(feedback)
                
                # --- 6. THE APPEND FIX ---
                try:
                    # ttl=0 ensures we fetch the absolute latest version from the sheet
                    existing_df = conn.read(ttl=0).dropna(how='all')
                except:
                    existing_df = pd.DataFrame(columns=["Student", "Mark"])
                
                new_row = pd.DataFrame([{
                    "Student": student_name, 
                    "Mark": score
                }])
                
                updated_df = pd.concat([existing_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                
                st.success("Entry added to the Gradebook!")

            except Exception as e:
                st.error(f"Error: {e}")

# --- 7. TEACHER VIEW ---
st.divider()
st.subheader("📊 Teacher Gradebook")
teacher_pwd = st.text_input("Enter Password", type="password")

if teacher_pwd == st.secrets.get("TEACHER_PASSWORD", "admin123"):
    try:
        current_sheet = conn.read(ttl=0)
        st.dataframe(current_sheet, use_container_width=True)
    except:
        st.info("No marks recorded yet.")