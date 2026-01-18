import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import json

# --- 1. SETUP ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- 2. TEACHER SIDEBAR (Model Switcher) ---
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
                # File Processing
                file_bytes = uploaded_work.read()
                
                # Personalized JSON Prompt
                prompt = f"""
                You are a teacher. Mark this work against the memo at {MEMO_URL}.
                The student's name is {student_name}.
                
                1. Address the student by their name in the feedback.
                2. Respond ONLY in this JSON format:
                {{
                    "personalized_feedback": "Hello {student_name}, [your comments here]",
                    "score": "X/Total"
                }}
                """
                
                # Generate Content
                response = model.generate_content(
                    [prompt, {"mime_type": uploaded_work.type, "data": file_bytes}],
                    generation_config={"response_mime_type": "application/json"}
                )
                
                result = json.loads(response.text)
                feedback = result.get("personalized_feedback")
                score = result.get("score")

                # Show Results to Student
                st.subheader(f"Results for {student_name}")
                st.info(f"**Score: {score}**")
                st.markdown(feedback)
                
                # --- 6. THE "APPEND" FIX (Keeps previous entries) ---
                # Read existing data or create a fresh one if the sheet is blank
                try:
                    existing_df = conn.read()
                except:
                    existing_df = pd.DataFrame(columns=["Student", "Date", "Mark"])
                
                # Create the new row
                new_row = pd.DataFrame([{
                    "Student": student_name, 
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Mark": score
                }])
                
                # Combine old and new data (Append)
                updated_df = pd.concat([existing_df, new_row], ignore_index=True)
                
                # Write the whole list back to the same sheet
                conn.update(data=updated_df)
                st.success("Your mark has been successfully recorded!")

            except Exception as e:
                st.error(f"Error: {e}")

# --- 7. TEACHER VIEW (Password Protected) ---
st.divider()
st.subheader("📊 Teacher Gradebook")
teacher_pwd = st.text_input("Enter Password to View Sheet", type="password")

if teacher_pwd == st.secrets.get("TEACHER_PASSWORD", "admin123"):
    st.write("Current Marks:")
    try:
        grade_data = conn.read()
        st.dataframe(grade_data) # Shows the full sheet as a table
    except:
        st.warning("Gradebook is currently empty.")