import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import json

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
uploaded_work = st.file_uploader("Upload Work", type=["jpg", "png", "pdf"])

if st.button("Submit & Mark"):
    if not student_name or not uploaded_work:
        st.error("Please provide name and work.")
    else:
        with st.spinner(f"AI is marking {student_name}'s work..."):
            try:
                # A. Prepare the file
                file_bytes = uploaded_work.read()
                
                # B. REFINED PROMPT (Personalized & JSON)
                prompt = f"""
                You are a teacher. Mark this work against the memo at {MEMO_URL}.
                The student's name is {student_name}.
                Mark the work 5 times and take the avergae result rounded to the nearest whole number as the final score.
                1. Address the student by their name in the feedback.
                2. Respond ONLY in this JSON format:
                {{
                    "personalized_feedback": "Hello {student_name}, [your comments here]",
                    "score": "X/Total"
                }}
                """
                
                # C. Generate Content with JSON mode
                response = model.generate_content(
                    [prompt, {"mime_type": uploaded_work.type, "data": file_bytes}],
                    generation_config={"response_mime_type": "application/json"}
                )
                
                # D. Parse Data
                result = json.loads(response.text)
                feedback = result.get("personalized_feedback")
                score = result.get("score")

                # E. Show Results
                st.subheader(f"Results for {student_name}")
                st.info(f"**Score: {score}**")
                st.markdown(feedback)
                
                # --- 6. THE "SAME SHEET" FIX ---
                # 1. Read the existing data first
                try:
                    existing_df = conn.read()
                except:
                    # If the sheet is empty, create a blank dataframe with headers
                    existing_df = pd.DataFrame(columns=["Student", "Date", "Mark"])
                
                # 2. Create the new row
                new_row = pd.DataFrame([{
                    "Student": student_name, 
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Mark": score
                }])
                
                # 3. Join them together (Append)
                updated_df = pd.concat([existing_df, new_row], ignore_index=True)
                
                # 4. Write the whole list back to the same sheet
                conn.update(data=updated_df)
                
                st.success("Gradebook updated on the same sheet!")

            except Exception as e:
                st.error(f"Error: {e}")