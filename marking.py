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
# Note: Using the official stable names
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
                # OPTIMIZE IMAGE (Prevents 500 Errors)
                img = Image.open(uploaded_work)
                img.thumbnail((1024, 1024))
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                optimized_bytes = img_byte_arr.getvalue()
                
                # Personalized JSON Prompt
                prompt = f"""
                You are a teacher. Mark this work against the memo at {MEMO_URL}.
                The student's name is {student_name}.
                Address them by name in the feedback.
                
                Respond ONLY in this JSON format:
                {{
                    "personalized_feedback": "Hello {student_name}, ...",
                    "score": "X/Total"
                }}
                """
                
                response = model.generate_content(
                    [prompt, {"mime_type": "image/jpeg", "data": optimized_bytes}],
                    generation_config={"response_mime_type": "application/json"}
                )
                
                result = json.loads(response.text)
                feedback = result.get("personalized_feedback")
                score = result.get("score")

                st.subheader(f"Results for {student_name}")
                st.info(f"**Score: {score}**")
                st.markdown(feedback)
                
                # --- 6. THE APPEND FIX ---
                # Step A: Read the CURRENT sheet
                try:
                    # We use ttl=0 to ensure we aren't looking at a "cached" old version
                    existing_df = conn.read(ttl=0) 
                    # Drop any completely empty rows that might interfere
                    existing_df = existing_df.dropna(how='all')
                except:
                    existing_df = pd.DataFrame(columns=["Student", "Date", "Mark"])
                
                # Step B: Create the new row
                new_row = pd.DataFrame([{
                    "Student": student_name, 
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Mark": score
                }])
                
                # Step C: Combine them
                updated_df = pd.concat([existing_df, new_row], ignore_index=True)
                
                # Step D: Update the sheet
                # We specify the worksheet name (usually 'Sheet1') to be safe
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
        # Fetch fresh data for the teacher
        current_sheet = conn.read(ttl=0)
        st.dataframe(current_sheet, use_container_width=True)
    except:
        st.info("No marks recorded yet.")
