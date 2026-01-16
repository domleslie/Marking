import streamlit as st
import google.generativeai as genai
from PIL import Image

import os
from dotenv import load_dotenv


# --- 1. SETTINGS & PROMPT ---
# This is the "Teacher's Brain" section
MARKING_PROMPT = """
You are a Math teacher marking a math worksheet. 
You have been given the memorandum. Mark the student's answers accordingly.

 Output the result as a clear list: 
   - Total Score
   - Correct answers
   - Mistakes (and why they are wrong)
"""

# --- 2. SETUP ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
#genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 3. UI ---
st.title("📝 Automated Marking")
uploaded_file = st.file_uploader("Upload worksheet", type=["jpg", "png","pdf"])

if uploaded_file:
    img = Image.open(uploaded_file)
    if st.button("Mark Now"):
        # We pass the prompt variable here
        response = model.generate_content([MARKING_PROMPT, img])
        st.markdown(response.text)