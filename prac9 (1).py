# =========================================================
# AI PLASTIC DETECTION SYSTEM - PREMIUM FINAL VERSION
# =========================================================
# INSTALL:
# pip install streamlit tensorflow pillow numpy pandas
# pip install plotly opencv-python fpdf matplotlib
#
# RUN:
# streamlit run app.py
# =========================================================

# =========================================================
# IMPORT LIBRARIES
# =========================================================

import streamlit as st
import tensorflow as tf
import numpy as np
from PIL import Image
import pandas as pd
import plotly.express as px
import sqlite3
from fpdf import FPDF
from datetime import datetime
import time

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Plastic Detection",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# SIDEBAR DARK MODE TOGGLE
# =========================================================

st.sidebar.title("⚙️ Control Panel")

dark_mode = st.sidebar.toggle(
    "🌙 Dark Mode",
    value=True
)

# =========================================================
# THEME COLORS
# =========================================================

if dark_mode:

    main_bg = "linear-gradient(135deg,#020617,#0f172a,#1e293b)"
    text_color = "white"
    sub_text = "#cbd5e1"
    glass_bg = "rgba(255,255,255,0.08)"
    sidebar_bg = "white"
    sidebar_text = "#2563eb"

else:

    main_bg = "#f1f5f9"
    text_color = "#111827"
    sub_text = "#475569"
    glass_bg = "rgba(255,255,255,0.85)"
    sidebar_bg = "#e2e8f0"
    sidebar_text = "#1e293b"

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(f"""
<style>

@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"]{{
    font-family:'Poppins',sans-serif;
}}

/* Main Background */
[data-testid="stAppViewContainer"]{{
    background:{main_bg};
    color:{text_color};
}}

/* Sidebar */
[data-testid="stSidebar"]{{
    background:{sidebar_bg};
    border-right:2px solid #2563eb;
}}

/* Sidebar Text */
[data-testid="stSidebar"] *{{
    color:{sidebar_text} !important;
    font-weight:600;
}}

/* Sidebar Radio */
.stRadio label{{
    color:{sidebar_text} !important;
    font-size:18px !important;
}}

/* Sidebar Title */
[data-testid="stSidebar"] h1{{
    color:{sidebar_text} !important;
    font-size:32px !important;
}}

/* Upload Label */
[data-testid="stFileUploader"] label{{
    color:{text_color} !important;
    font-size:20px !important;
    font-weight:600 !important;
}}

/* Selectbox Label */
.stSelectbox label{{
    color:{text_color} !important;
    font-size:18px !important;
    font-weight:600 !important;
}}

/* Number Input Label */
.stNumberInput label{{
    color:{text_color} !important;
    font-size:18px !important;
    font-weight:600 !important;
}}

/* Header */
.main-title{{
    text-align:center;
    font-size:60px;
    font-weight:700;
    color:{text_color};
    margin-top:10px;
}}

.sub-title{{
    text-align:center;
    font-size:24px;
    color:{sub_text};
    margin-bottom:35px;
}}

/* Glass Card */
.glass{{
    background:{glass_bg};
    border-radius:24px;
    padding:24px;
    backdrop-filter: blur(12px);
    border:1px solid rgba(255,255,255,0.15);
    box-shadow:0 8px 32px rgba(0,0,0,0.35);
    margin-bottom:20px;
}}

/* Buttons */
.stButton>button{{
    width:100%;
    height:55px;
    border:none;
    border-radius:15px;
    background: linear-gradient(to right,#22c55e,#16a34a);
    color:white;
    font-size:20px;
    font-weight:600;
    transition:0.3s;
}}

.stButton>button:hover{{
    transform:scale(1.02);
}}

/* Metric */
.metric{{
    font-size:24px;
    font-weight:600;
    margin-bottom:12px;
}}

/* Footer Hide */
footer{{
    visibility:hidden;
}}

</style>
""", unsafe_allow_html=True)

# =========================================================
# DATABASE
# =========================================================

conn = sqlite3.connect("plastic_detection.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plastic_type TEXT,
    confidence REAL,
    eco_score INTEGER,
    detection_time TEXT
)
""")

conn.commit()

# =========================================================
# LOAD MODEL
# =========================================================

model = tf.keras.models.load_model("plastic_classifier.h5")

class_names = ['Others','PC','PE','PET','PP','PS']

# =========================================================
# PLASTIC INFORMATION
# =========================================================

plastic_info = {

    "PET":{
        "reusable":True,
        "recyclable":True,
        "harmful":False,
        "eco_base":90,
        "suggestion":"PET plastics are recyclable and reusable."
    },

    "PP":{
        "reusable":True,
        "recyclable":True,
        "harmful":False,
        "eco_base":85,
        "suggestion":"PP plastics are food-safe and reusable."
    },

    "PE":{
        "reusable":False,
        "recyclable":True,
        "harmful":False,
        "eco_base":65,
        "suggestion":"Reduce excessive PE plastic usage."
    },

    "PS":{
        "reusable":False,
        "recyclable":False,
        "harmful":True,
        "eco_base":25,
        "suggestion":"Avoid PS plastics."
    },

    "PC":{
        "reusable":True,
        "recyclable":False,
        "harmful":True,
        "eco_base":40,
        "suggestion":"Avoid heating PC plastics."
    },

    "Others":{
        "reusable":False,
        "recyclable":False,
        "harmful":False,
        "eco_base":50,
        "suggestion":"Unknown plastic category."
    }
}

# =========================================================
# HEADER
# =========================================================

st.markdown(f"""
<div class='main-title'>
♻️ AI Plastic Detection System
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class='sub-title'>
Deep Learning Based Smart Waste Classification Platform
</div>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================

mode = st.sidebar.radio(
    "Choose Input Method",
    ["Upload Image","Use Webcam"]
)

st.sidebar.markdown("---")

st.sidebar.success(
    "📌 Use clear plastic images for best accuracy."
)

# =========================================================
# AI PREDICTION FUNCTION
# =========================================================

def predict_image(image):

    img = image.resize((224,224))

    img = img.convert("RGB")

    img_array = np.array(img)

    img_array = img_array.astype("float32") / 255.0

    img_array = np.expand_dims(img_array,axis=0)

    prediction = model.predict(img_array, verbose=0)

    predicted_index = np.argmax(prediction)

    plastic_type = class_names[predicted_index]

    confidence = float(np.max(prediction)*100)

    return plastic_type, confidence

# =========================================================
# PDF REPORT FUNCTION
# =========================================================

def generate_pdf(plastic_type,confidence,eco_score,suggestion):

    pdf = FPDF()

    pdf.add_page()

    pdf.set_font("Arial",size=18)

    pdf.cell(200,10,txt="AI Plastic Detection Report",ln=True)

    pdf.ln(10)

    pdf.set_font("Arial",size=13)

    pdf.cell(200,10,txt=f"Plastic Type: {plastic_type}",ln=True)

    pdf.cell(200,10,txt=f"Confidence: {confidence:.2f}%",ln=True)

    pdf.cell(200,10,txt=f"Eco Score: {eco_score}/100",ln=True)

    pdf.multi_cell(0,10,txt=f"Suggestion: {suggestion}")

    filename = "plastic_report.pdf"

    pdf.output(filename)

    return filename

# =========================================================
# INPUT SECTION
# =========================================================

image = None

if mode == "Upload Image":

    uploaded_file = st.file_uploader(
        "📤 Upload Plastic Image",
        type=["jpg","jpeg","png"]
    )

    if uploaded_file:
        image = Image.open(uploaded_file)

else:

    camera_image = st.camera_input(
        "📸 Capture Plastic Image"
    )

    if camera_image:
        image = Image.open(camera_image)

# =========================================================
# ANALYSIS SECTION
# =========================================================

if image:

    col1, col2 = st.columns([1.3,1])

    with col1:

        st.image(
            image,
            caption="Plastic Image",
            use_container_width=True
        )

    with col2:

        st.markdown("""
        <div class='glass'>
        <h2>🤖 AI Detection Panel</h2>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Start AI Detection"):

            with st.spinner("Analyzing Plastic Material..."):

                time.sleep(2)

                plastic_type, confidence = predict_image(image)

            info = plastic_info[plastic_type]

            eco_score = info["eco_base"]

            cursor.execute("""
            INSERT INTO history(
            plastic_type,
            confidence,
            eco_score,
            detection_time
            )
            VALUES(?,?,?,?)
            """,(
                plastic_type,
                confidence,
                eco_score,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

            conn.commit()

            st.markdown(f"""
            <div class='glass'>
            <div class='metric'>♻️ Plastic Type Detected</div>
            <h1>{plastic_type}</h1>
            <h3>Confidence: {confidence:.2f}%</h3>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class='glass'>
            <div class='metric'>📋 Material Information</div>

            ✅ Reusable:
            {"Yes" if info["reusable"] else "No"}

            <br><br>

            ♻️ Recyclable:
            {"Yes" if info["recyclable"] else "No"}

            <br><br>

            ⚠️ Harmful:
            {"Yes" if info["harmful"] else "No"}

            </div>
            """, unsafe_allow_html=True)

            if eco_score >= 80:

                st.success("🌱 Eco Friendly Plastic")

            elif eco_score >= 50:

                st.warning("⚠ Moderate Environmental Impact")

            else:

                st.error("🚨 Harmful Plastic Material")

            st.subheader("📊 Confidence Meter")

            st.progress(int(confidence))

            st.write(f"Detection Confidence: {confidence:.2f}%")

            st.subheader("🌍 Environmental Eco Score")

            st.progress(eco_score)

            st.write(f"Eco Score: {eco_score}/100")

            st.markdown(f"""
            <div class='glass'>
            <div class='metric'>💡 Sustainability Suggestion</div>
            {info["suggestion"]}
            </div>
            """, unsafe_allow_html=True)

            pdf_file = generate_pdf(
                plastic_type,
                confidence,
                eco_score,
                info["suggestion"]
            )

            with open(pdf_file,"rb") as f:

                st.download_button(
                    "📄 Download AI Report",
                    f,
                    file_name="AI_Plastic_Report.pdf"
                )

# =========================================================
# ANALYTICS DASHBOARD
# =========================================================

st.markdown("---")

st.header("📈 AI Detection Analytics Dashboard")

df = pd.read_sql_query(
    "SELECT * FROM history",
    conn
)

if not df.empty:

    chart1 = px.bar(
        df,
        x="plastic_type",
        title="Plastic Detection Frequency",
        color="plastic_type"
    )

    st.plotly_chart(
        chart1,
        use_container_width=True
    )

    chart2 = px.pie(
        df,
        names="plastic_type",
        title="Plastic Distribution"
    )

    st.plotly_chart(
        chart2,
        use_container_width=True
    )

    st.subheader("🗂 Detection History")

    st.dataframe(df,use_container_width=True)

    st.write("")

    selected_id = st.selectbox(
        "Select Detection ID to Delete",
        df["id"]
    )

    if st.button("🗑 Delete Detection"):

        cursor.execute(
            "DELETE FROM history WHERE id=?",
            (int(selected_id),)
        )

        conn.commit()

        st.success("Detection deleted successfully.")

        st.rerun()

else:

    st.info("No detection history available.")

# =========================================================
# TECHNOLOGIES + FEATURES
# =========================================================

st.markdown("---")

colA, colB = st.columns(2)

with colA:

    st.markdown("""
    <div style="
        background: linear-gradient(135deg,#1e3a8a,#2563eb);
        padding:20px;
        border-radius:25px;
        height:100%;
        box-shadow:0 8px 25px rgba(0,0,0,0.35);
    ">

    <h1 style="
        color:white;
        font-size:30px;
        margin-bottom:20px;
        text-align:center;
    ">
    💻 Technologies Used
    </h1>

    <div style="
        color:white;
        font-size:18px;
        line-height:2;
        font-weight:500;
    ">

    ✅ Python <br>
    ✅ TensorFlow <br>
    ✅ Streamlit <br>
    ✅ OpenCV <br>
    ✅ CNN Deep Learning <br>
    ✅ Computer Vision <br>
    ✅ Plotly Dashboard

    </div>

    </div>
    """, unsafe_allow_html=True)

with colB:

    st.markdown("""
    <div style="
        background: linear-gradient(135deg,#065f46,#10b981);
        padding:20px;
        border-radius:25px;
        height:100%;
        box-shadow:0 8px 25px rgba(0,0,0,0.35);
    ">

    <h1 style="
        color:white;
        font-size:30px;
        margin-bottom:20px;
        text-align:center;
    ">
    🚀 Project Features
    </h1>

    <div style="
        color:white;
        font-size:18px;
        line-height:2;
        font-weight:500;
    ">

    ✅ Real-time Plastic Detection <br>
    ✅ AI Sustainability Analysis <br>
    ✅ Environmental Impact Scoring <br>
    ✅ Smart Waste Classification <br>
    ✅ Upload + Webcam Detection <br>
    ✅ PDF Report Generation <br>
    ✅ Analytics Dashboard

    </div>

    </div>
    """, unsafe_allow_html=True)

# =========================================================
# FOOTER
# =========================================================

st.write("")

st.markdown(f"""
<div style="
    text-align:center;
    color:{sub_text};
    font-size:20px;
    margin-top:20px;
    margin-bottom:20px;
">

Developed with ❤️ using Artificial Intelligence & Computer Vision<br>
<span style="
font-size:22px;
font-weight:600;
color:{text_color};
">
By: Soumita Das, Debanjana Sarkar, Rupa Kundu
</span>
</div>
""", unsafe_allow_html=True)