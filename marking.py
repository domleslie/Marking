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
available_models = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-pro"]
selected_model_name = st.sidebar.selectbox("Model Version", available_models)
model = genai.GenerativeModel(selected_model_name)

# --- 3. THE PERMANENT MEMO ---
FILE_ID = "15qetiIoJ1xdUHgMSW6r0Ix3nA6jXQaK7"
MEMO_URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# --- 4. GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 5. STUDENT PORTAL ---
st.title("📝 Student Marking Portal")
student_name = st.text_input("Student Full Name:")

# Change: accept_multiple_files=True
uploaded_files = st.file_uploader("Upload Work (Select all pages at once)", 
                                  type=["jpg", "png", "jpeg", "pdf"], 
                                  accept_multiple_files=True)

if st.button("Submit & Mark"):
    if not student_name or not uploaded_files:
        st.error("Please provide name and upload at least one file.")
    else:
        with st.spinner(f"AI is marking all {len(uploaded_files)} pages for {student_name}..."):
            try:
                # --- PROCESS MULTIPLE FILES ---
                ai_content_list = []
                
                # Instruction/Rubric Prompt
                rubric_prompt = f"""
                You are a strict teacher marking against this memo: {MEMO_URL}.
                Student Name: {student_name}
                
                ### MARKING RUBRIC:
                1. Accuracy: Give full marks only if the answer matches the memo exactly.
                2. Personalization: Address {student_name} by name and encourage them.
                3. Give the student detailed feedback on their mistakes, so that they can learn.
                
                Respond ONLY in this JSON format:
                {{
                    "personalized_feedback": "Hello {student_name}, ...",
                    "score": "X/Total"
                }}
                """
                ai_content_list.append(rubric_prompt)

                for uploaded_file in uploaded_files:
                    if uploaded_file.type == "application/pdf":
                        ai_content_list.append({
                            "mime_type": "application/pdf", 
                            "data": uploaded_file.read()
                        })
                    else:
                        # Image processing (Fix RGBA error)
                        img = Image.open(uploaded_file)
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        img.thumbnail((1024, 1024))
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='JPEG', quality=85)
                        ai_content_list.append({
                            "mime_type": "image/jpeg", 
                            "data": img_byte_arr.getvalue()
                        })

                # --- GENERATE CONTENT (Strict Setting) ---
                response = model.generate_content(
                    ai_content_list,
                    generation_config={
                        "response_mime_type": "application/json",
                        "temperature": 0.0  # Zero temperature for maximum consistency
                    }
                )
                
                result = json.loads(response.text)
                feedback = result.get("personalized_feedback")
                score = result.get("score")

                st.subheader(f"Results for {student_name}")
                st.info(f"**Final Score: {score}**")
                st.markdown(feedback)
                
                # --- 6. APPEND TO SHEET ---
                try:
                    existing_df = conn.read(ttl=0).dropna(how='all')
                except:
                    existing_df = pd.DataFrame(columns=["Student", "Date", "Mark"])
                
                new_row = pd.DataFrame([{
                    "Student": student_name, 
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Mark": score
                }])
                
                updated_df = pd.concat([existing_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success("All pages marked and saved to Gradebook!")

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
