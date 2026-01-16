import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
from datetime import datetime
from google.generativeai import types
from streamlit_gsheets import GSheetsConnection

# --- 1. SETUP & CONFIGURATION (Preheat the Oven) ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. THE PERMANENT MEMO (The Source of Truth) ---
# Note: I've converted your link to a Direct Download format
FILE_ID = "1ia4jAk_m3vDGelBD096Mxl13ohG6QChU"
MEMO_URL = f"https://drive.google.com/uc?export=download&id={FILE_ID}"

# --- 3. GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 4. TEACHER SECTION ---
st.sidebar.title("🍎 Teacher Dashboard")
teacher_password = st.sidebar.text_input("Teacher Password", type="password")

# --- 5. STUDENT SECTION ---
st.title("📝 Student Marking Portal")
student_name = st.text_input("Enter your name:")
uploaded_work = st.file_uploader("Upload your worksheet (JPEG/PNG)", type=["jpg", "png"])

if st.button("Submit & Mark"):
    if not student_name or not uploaded_work:
        st.error("Please provide your name and upload your work.")
    else:
        # Prepare the student work image
        student_img = Image.open(uploaded_work)
        
        with st.spinner("AI Teacher is marking..."):
            # The prompt instructions
            prompt = "Compare the student's work in the image to the official memo provided via the URL. Calculate a total score and list corrections."
            
            # THE BRAIN ACTION: We call this AFTER model is defined
            response = model.generate_content([
                prompt,
                types.Part.from_uri(uri=MEMO_URL, mime_type="image/jpeg"), 
                student_img
            ])
            
            # Show results
            st.markdown(response.text)
            
            # --- SEND TO GOOGLE SHEETS ---
            new_row = pd.DataFrame([{
                "Student": student_name, 
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"), 
                "Feedback": response.text[:200]
            }])
            conn.create(data=new_row)
            st.success("Result saved to Google Sheets!")