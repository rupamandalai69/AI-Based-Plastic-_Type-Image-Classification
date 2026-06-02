import os
import time
import requests
import base64
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from PIL import Image
import textwrap

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="EcoSort AI",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# INITIALIZE SESSION STATE & QUERY PARAMETERS ROUTING
# =========================================================
# Query parameters act as the single source of truth for page and theme
if "page" not in st.query_params:
    st.query_params["page"] = "home"
if "theme" not in st.query_params:
    st.query_params["theme"] = "dark"

st.session_state.page = st.query_params["page"]
st.session_state.theme = st.query_params["theme"]

if "user_phone" not in st.session_state:
    st.session_state.user_phone = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "sim_users" not in st.session_state:
    st.session_state.sim_users = {
        "9999999991": {"name": "Rohan Sharma", "weight": 320.0, "coins": 3200},
        "9999999992": {"name": "Priya Patel", "weight": 285.0, "coins": 2850},
        "9999999993": {"name": "Amit Kumar", "weight": 210.0, "coins": 2100},
        "9999999994": {"name": "Debanjana Sarkar", "weight": 185.0, "coins": 1850},
        "9999999995": {"name": "Soumita Das", "weight": 150.0, "coins": 1500}
    }

if "sim_weight" not in st.session_state:
    st.session_state.sim_weight = 0.0
if "sim_coins" not in st.session_state:
    st.session_state.sim_coins = 0
if "sim_leaderboard" not in st.session_state:
    st.session_state.sim_leaderboard = [
        {"name": "Rohan Sharma", "coins": 3200},
        {"name": "Priya Patel", "coins": 2850},
        {"name": "Amit Kumar", "coins": 2100},
        {"name": "Debanjana Sarkar", "coins": 1850},
        {"name": "Soumita Das", "coins": 1500}
    ]
if "api_online" not in st.session_state:
    st.session_state.api_online = True

# =========================================================
# DATA DEFINITIONS (MIGRATED FROM REACT FRONTEND)
# =========================================================
IMPACT_SECTIONS = [
    {
        "title": "Plastic and Oceans",
        "icon": "🌊",
        "image_file": "ocean_plastic.png",
        "stats": "8 Million Tons/Year",
        "details": "By 2050, the mass of plastic waste in the oceans is projected to exceed the mass of all fish. Marine currents concentrate these materials into massive rotating garbage patches.",
        "highlight": "Great Pacific Garbage Patch covers over 1.6 million square kilometers."
    },
    {
        "title": "Plastic and Rivers",
        "icon": "💧",
        "image_file": "river_plastic.png",
        "stats": "80% of Ocean Entry",
        "details": "Most ocean plastic waste originates from land, carried by major river arteries. Rivers function as conveyer belts that transport city waste directly to the sea.",
        "highlight": "10 rivers carry over 90% of the global river-based plastic burden."
    },
    {
        "title": "Plastic and Soil",
        "icon": "🌱",
        "image_file": "soil_plastic.png",
        "stats": "4x Land Pollution",
        "details": "Microplastics in agricultural soils disrupt the soil structure, restrict water retention, and damage earthworm populations, reducing global crop yields.",
        "highlight": "Sewage sludge used as agricultural fertilizer deposits tons of microplastics annually."
    },
    {
        "title": "Plastic and Wildlife",
        "icon": "🐟",
        "image_file": "wildlife_plastic.png",
        "stats": "100k+ Deaths Annually",
        "details": "Sea turtles mistake plastic bags for jellyfish, and albatrosses feed floating debris to their chicks. Debris causing physical blockages or entrapment claims hundreds of thousands of lives.",
        "highlight": "Over 700 species of marine animals have been documented eating or getting entangled in plastic."
    },
    {
        "title": "Plastic and Human Health",
        "icon": "❤️",
        "image_file": "health_plastic.png",
        "stats": "5 grams consumed weekly",
        "details": "Microplastics are now found in drinking water, seafood, table salt, and even human lungs and placenta. Leached chemical additives act as endocrine disruptors and carcinogens.",
        "highlight": "Humans ingest roughly a credit card's weight in microplastics every single week."
    }
]

CRITICAL_TOPICS = [
    {
        "title": "Microplastics",
        "desc": "Particles under 5mm that result from the breakdown of larger plastics. They absorb heavy metals and pesticide runoffs, making them toxic capsules that enter biological systems."
    },
    {
        "title": "Food Contamination",
        "desc": "Plastics bioaccumulate up the food chain. When fish ingest microplastics, the chemical toxins dissolve into their fat tissue, which is subsequently eaten by humans."
    },
    {
        "title": "Cancer & Toxicity Risks",
        "desc": "Compounds like BPA in polycarbonates and phthalates in PVC are known endocrine disruptors linked to developmental defects, obesity, reproductive issues, and cancers."
    },
    {
        "title": "Climate & CO2 Impact",
        "desc": "Plastics are derived from fossil fuels. From extraction and refining to incineration, the lifecycle of plastics emits billions of tons of greenhouse gases annually."
    }
]

INITIATIVES = [
    {
        "id": "rules",
        "title": "Plastic Waste Management Rules (2016 - 2024)",
        "effectiveness": "75%",
        "stats": "Banned plastics under 120 microns, increasing recycling mandates.",
        "video": "https://www.youtube.com/watch?v=_KqA3sU4G6A",
        "desc": "Enacted by the Ministry of Environment, Forest and Climate Change, these rules establish a regulatory framework. They mandate local authorities to set up sorting facilities, ban thin carrier bags, and promote the use of plastic waste in road construction."
    },
    {
        "id": "sbm",
        "title": "Swachh Bharat Mission (Clean India Campaign)",
        "effectiveness": "88%",
        "stats": "Over 100 million toilets built; 100% door-to-door trash pick-up in major municipalities.",
        "video": "https://www.youtube.com/watch?v=Z0oYvVw1EwM",
        "desc": "Launched in 2014, SBM is a country-wide campaign to clean up streets, roads, and cities. SBM-Urban 2.0 specifically focuses on 'Garbage-Free Cities' through source-segregation, scientific processing of solid waste, and remediation of legacy landfills."
    },
    {
        "id": "ban",
        "title": "Single-Use Plastic Ban (July 2022)",
        "effectiveness": "65%",
        "stats": "Banned 19 high-utility, low-recyclability items like plastic cutlery, earbuds, and flags.",
        "video": "https://www.youtube.com/watch?v=XqC94Ncl-fI",
        "desc": "A watershed federal directive banning the manufacturing, import, stocking, distribution, sale, and use of identified single-use plastic items that possess high littering potential and minimal recycling utility."
    },
    {
        "id": "epr",
        "title": "Extended Producer Responsibility (EPR)",
        "effectiveness": "70%",
        "stats": "Registered 22,000+ PIBOs (Producers, Importers & Brand Owners) under the national portal.",
        "video": "https://www.youtube.com/watch?v=d3W47zMvY4Q",
        "desc": "EPR makes producers responsible for the environmental impacts of their products throughout the product life cycle. Under the guidelines, brand owners are legally bound to meet minimum recycling targets for their post-consumer packaging."
    }
]

TIMELINE = [
    {"year": "2014", "event": "Launch of Swachh Bharat Mission (Clean India Campaign)", "details": "Initiated a massive public focus on basic sanitation and waste management."},
    {"year": "2016", "event": "Plastic Waste Management Rules codified", "details": "Introduced thickness limits of 50 microns for bags and introduced EPR frameworks."},
    {"year": "2021", "event": "Plastic waste thickness increased to 75 microns", "details": "Phased tightening of plastic regulations, restricting thin single-use items."},
    {"year": "2022", "event": "Total Ban on 19 Single-Use Plastic Items", "details": "Enforced structural bans on plastic cutlery, straws, wrapping films, etc."},
    {"year": "2023", "event": "Bag thickness limit raised to 120 microns", "details": "Forced shift towards thicker, reusable carrier bags or fabric alternatives."},
    {"year": "2024+", "event": "Mandatory Circular Economy targets for EPR", "details": "PIBOs required to achieve 100% recovery and recycling certificates."}
]

BADGES = [
    {"name": "Eco Initiate", "desc": "Recycle your first piece of plastic.", "minWeight": 0.1, "color": "#94a3b8"},
    {"name": "Green Warrior", "desc": "Recycled over 10 kg of plastic.", "minWeight": 10.0, "color": "#4ade80"},
    {"name": "Ocean Saver", "desc": "Recycled over 50 kg of plastic.", "minWeight": 50.0, "color": "#38bdf8"},
    {"name": "Circular Champion", "desc": "Recycled over 100 kg of plastic.", "minWeight": 100.0, "color": "#a855f7"},
    {"name": "Zero-Waste Legend", "desc": "Recycled over 300 kg of plastic.", "minWeight": 300.0, "color": "#fbbf24"}
]

TEAM_DATA = [
    {
        "name": "Rupa Kundu",
        "role": "AI Lead & Backend Architect",
        "skills": ["TensorFlow", "Keras", "Python", "Flask", "SQLite"],
        "contributions": "Implemented the CNN classification model, set up training datasets, built the Flask backend API, and designed the database logging logic.",
        "image_key": "rupa"
    },
    {
        "name": "Debanjana Sarkar",
        "role": "Frontend Engineer & UI Designer",
        "skills": ["React", "JavaScript", "HTML5", "CSS3", "Matplotlib"],
        "contributions": "Designed the glassmorphic sustainability theme, structured navigation, and built interactive scanner visual widgets and PDF reports.",
        "image_key": "debanjana"
    },
    {
        "name": "Soumita Das",
        "role": "Policy Researcher & Product Manager",
        "skills": ["EPR Policy", "SBM Guidelines", "Data Visuals", "Documentation"],
        "contributions": "Curated research regarding government directives, Swachh Bharat campaigns, and mapped ecotoxical materials properties details.",
        "image_key": "soumita"
    }
]

PLASTIC_INFO_LOCAL = {
    "PET": {
        "name": "Polyethylene Terephthalate (PET)",
        "code": "1",
        "harmfulness": "Low (for single use)",
        "env_risk": 35,
        "carbon_footprint": "2.15 kg CO2/kg",
        "decomp_time": "450 Years",
        "recyclability": "90%",
        "disposal": "Rinse and place in blue recycling bins. Do not reuse single-use bottles.",
        "health_risk": "Can leach antimony (a potential carcinogen) if exposed to heat or stored long-term.",
        "river_impact": "Extremely high. Floats easily and is the most common plastic bottle litter in waterways.",
        "wildlife_impact": "Frequently ingested by marine life and large birds, causing digestive tract blockages.",
        "alternatives": "Glass bottles, Stainless steel flasks, copper vessels, reusable aluminum containers."
    },
    "HDPE": {
        "name": "High-Density Polyethylene (HDPE)",
        "code": "2",
        "harmfulness": "Very Low",
        "env_risk": 20,
        "carbon_footprint": "1.60 kg CO2/kg",
        "decomp_time": "100-300 Years",
        "recyclability": "85%",
        "disposal": "Place in recycling bins. HDPE is highly valued by recyclers.",
        "health_risk": "One of the safest plastics; low risk of chemical leaching into food or drinks.",
        "river_impact": "Moderate to High. Breakdown into microplastics that poison aquatic life.",
        "wildlife_impact": "Physical entrapment and choking risk for small river animals.",
        "alternatives": "Glass jars, metal containers, silicone bags, reusable cotton bags."
    },
    "PVC": {
        "name": "Polyvinyl Chloride (PVC)",
        "code": "3",
        "harmfulness": "Extremely High",
        "env_risk": 95,
        "carbon_footprint": "3.10 kg CO2/kg",
        "decomp_time": "Infinite (does not biodegrade)",
        "recyclability": "0% (Rarely recycled)",
        "disposal": "Dispose of in landfill or hazardous waste collection. Do NOT burn PVC.",
        "health_risk": "Leaches toxic chemicals (phthalates, dioxins, lead, cadmium) known to cause hormone disruption and cancer.",
        "river_impact": "Critical. Heavy and sinks, releasing toxic additives directly into riverbeds and sediments.",
        "wildlife_impact": "Releases toxic chemicals into water, poisoning aquatic species and disrupting reproduction.",
        "alternatives": "Bamboo poles, clay pipes, wooden structures, metal pipes, organic fabric."
    },
    "LDPE": {
        "name": "Low-Density Polyethylene (LDPE)",
        "code": "4",
        "harmfulness": "Low",
        "env_risk": 45,
        "carbon_footprint": "1.80 kg CO2/kg",
        "decomp_time": "500-1000 Years",
        "recyclability": "30%",
        "disposal": "Check local guidelines. Often accepted at supermarket film collection points.",
        "health_risk": "Relatively safe, but can leach estrogenic chemicals under high temperatures.",
        "river_impact": "Severe. Lightweight plastic bags easily block water channels, drains, and catchments.",
        "wildlife_impact": "Frequently ingested by marine turtles and land mammals who mistake bags for jellyfish or food.",
        "alternatives": "Canvas shopping bags, beeswax wraps, glass storage containers."
    },
    "PP": {
        "name": "Polypropylene (PP)",
        "code": "5",
        "harmfulness": "Low",
        "env_risk": 30,
        "carbon_footprint": "1.70 kg CO2/kg",
        "decomp_time": "20-30 Years (low compared to others)",
        "recyclability": "40%",
        "disposal": "Accepted in most curbside recycling programs. Ensure it is clean of food remnants.",
        "health_risk": "High heat tolerance makes it safe for hot food/drinks. Low risk of chemical leaching.",
        "river_impact": "Moderate. Tends to break down into microplastic fibers that bioaccumulate in river fish.",
        "wildlife_impact": "Microplastics ingested by filter feeders, moving up the food chain to predators.",
        "alternatives": "Stainless steel lunchboxes, ceramic mugs, wooden utensils, cloth packaging."
    },
    "PS": {
        "name": "Polystyrene (PS / Styrofoam)",
        "code": "6",
        "harmfulness": "Very High",
        "env_risk": 85,
        "carbon_footprint": "2.50 kg CO2/kg",
        "decomp_time": "500 Years",
        "recyclability": "1%",
        "disposal": "Landfill waste. Avoid using as it breaks into tiny particles easily.",
        "health_risk": "Leaches styrene, a suspected carcinogen and neurotoxin, especially when heated with hot food/drinks.",
        "river_impact": "Disastrous. Breaks into thousands of tiny buoyant balls that cover river surfaces.",
        "wildlife_impact": "Fish and birds eat the white foam balls, leading to starvation due to stomach blockage.",
        "alternatives": "Paper cups, bagasse (sugarcane fiber) plates, mushroom-based packaging, cardboard."
    },
    "Other": {
        "name": "Other (PC, Nylon, Acrylic, etc.)",
        "code": "7",
        "harmfulness": "High",
        "env_risk": 75,
        "carbon_footprint": "2.80 kg CO2/kg",
        "decomp_time": "500-1000 Years",
        "recyclability": "5%",
        "disposal": "Generally not recyclable. Toss in standard trash bins.",
        "health_risk": "Polycarbonates leach BPA (Bisphenol A), a potent endocrine disruptor that causes reproductive issues.",
        "river_impact": "High. Toxic chemical runoff from landfill leaching makes its way into local rivers.",
        "wildlife_impact": "Bioaccumulation of BPA and plasticizers affects the development of aquatic wildlife.",
        "alternatives": "BPA-free bottles, bio-plastics (PLA - but compostable only), glass, metal."
    }
}

# =========================================================
# HELPER FUNCTIONS FOR ASSETS AND API
# =========================================================
def get_circle_avatar(image_filename, initials):
    """
    Loads an image from the assets directory, crops it to a circle, resizes it,
    and returns a PIL Image object with transparent background and a border outline.
    If the image file does not exist, it dynamically generates a beautiful solid background
    circle with initials in the center using system fonts.
    """
    path = os.path.join(os.path.dirname(__file__), "assets", image_filename) if image_filename else ""
    size = 200
    
    if path and os.path.exists(path):
        try:
            img = Image.open(path).convert("RGBA")
            width, height = img.size
            crop_size = min(width, height)
            left = (width - crop_size) // 2
            top = (height - crop_size) // 2
            img = img.crop((left, top, left + crop_size, top + crop_size))
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Create a circular mask
            mask = Image.new("L", (size, size), 0)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)
            
            # Create a new image with transparent background
            output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            output.paste(img, (0, 0), mask=mask)
            
            # Draw a beautiful accent border around the circle
            draw_border = ImageDraw.Draw(output)
            border_color = (34, 197, 94, 255) # Green accent
            draw_border.ellipse((2, 2, size-2, size-2), outline=border_color, width=4)
            
            return output
        except Exception:
            pass
            
    # Generate placeholder circular image with initials
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(output)
    
    # Draw background circle with solid green fill
    draw.ellipse((2, 2, size-2, size-2), fill=(34, 197, 94, 255))
    # Draw border
    draw.ellipse((2, 2, size-2, size-2), outline=(16, 185, 129, 255), width=3)
    
    # Try to load Arial font from standard Windows path
    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    font = None
    if os.path.exists(font_path):
        try:
            from PIL import ImageFont
            font = ImageFont.truetype(font_path, 72)
        except Exception:
            pass
            
    if font:
        try:
            bbox = draw.textbbox((0, 0), initials, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
        except AttributeError:
            w, h = draw.textsize(initials, font=font) if hasattr(draw, 'textsize') else (60, 60)
            
        draw.text(((size - w)//2, (size - h)//2 - 10), initials, fill=(255, 255, 255, 255), font=font)
    else:
        try:
            draw.text((size//2 - 10, size//2 - 10), initials, fill=(255, 255, 255, 255))
        except Exception:
            pass
            
    return output

# Local Asset Paths (requires no internet and loads instantly)
assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
eco_hero_path = os.path.join(assets_dir, "eco_hero.png")
ai_workflow_path = os.path.join(assets_dir, "ai_workflow.png")
eco_impact_path = os.path.join(assets_dir, "eco_impact.png")
eco_rewards_path = os.path.join(assets_dir, "eco_rewards.png")

def check_backend():
    try:
        response = requests.get("http://localhost:5000/statistics", timeout=1.5)
        if response.status_code == 200:
            st.session_state.api_online = True
        else:
            st.session_state.api_online = False
    except Exception:
        st.session_state.api_online = False

def trigger_confetti():
    confetti_html = """
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <script>
        var duration = 2.5 * 1000;
        var animationEnd = Date.now() + duration;
        var defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

        function randomInRange(min, max) {
          return Math.random() * (max - min) + min;
        }

        var interval = setInterval(function() {
          var timeLeft = animationEnd - Date.now();

          if (timeLeft <= 0) {
            return clearInterval(interval);
          }

          var particleCount = 50 * (timeLeft / duration);
          confetti(Object.assign({}, defaults, { 
            particleCount: particleCount, 
            origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } 
          }));
          confetti(Object.assign({}, defaults, { 
            particleCount: particleCount, 
            origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } 
          }));
        }, 250);
    </script>
    """
    st.components.v1.html(confetti_html, height=1)

def render_html(html_str):
    clean_lines = [line.strip() for line in html_str.splitlines()]
    st.markdown("\n".join(clean_lines), unsafe_allow_html=True)

# Check API health
check_backend()

# Load current wallet details globally for sidebar and widgets
weight_val = 0.0
coins_val = 0
leaderboard_data = []

if st.session_state.api_online:
    try:
        phone = st.session_state.get("user_phone", "")
        url = f"http://localhost:5000/reward?phone={phone}" if phone else "http://localhost:5000/reward"
        response = requests.get(url, timeout=1.5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                weight_val = float(data.get("total_weight", 0.0))
                coins_val = int(data.get("total_coins", 0))
                leaderboard_data = data.get("leaderboard", [])
    except Exception:
        pass
else:
    # Local Simulation Mode
    phone = st.session_state.get("user_phone", "")
    if phone and phone in st.session_state.sim_users:
        user_data = st.session_state.sim_users[phone]
        weight_val = float(user_data.get("weight", 0.0))
        coins_val = int(user_data.get("coins", 0))
    
    # Dynamic leaderboard from sim_users
    leaderboard_data = sorted(
        [{"name": u["name"], "coins": u["coins"]} for u in st.session_state.sim_users.values()],
        key=lambda x: x["coins"],
        reverse=True
    )

# =========================================================
# THEME CONTROLS & DYNAMIC NAV INJECTION
# =========================================================
# Force premium Dark Mode as the single unified theme for EcoSort AI
st.session_state.theme = "dark"
st.query_params["theme"] = "dark"

bg_gradient = "linear-gradient(135deg, #020617 0%, #0f172a 40%, #052e16 100%)"
card_bg = "rgba(15, 23, 42, 0.45)"
card_border = "rgba(34, 197, 94, 0.2)"
text_main = "#f8fafc"
text_sub = "#94a3b8"
accent = "#22c55e"
accent_rgb = "34, 197, 94"
shadow = "0 8px 32px 0 rgba(0, 0, 0, 0.5)"
input_bg = "rgba(30, 41, 59, 0.6)"
nav_bg = "rgba(15, 23, 42, 0.7)"

# Inject Custom CSS (includes hiding default Streamlit sidebar elements and aligning width)
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
    font-family: 'Poppins', sans-serif !important;
    background: {bg_gradient} !important;
    color: {text_main} !important;
}}

h1, h2, h3, h4, h5, h6, [data-testid="stHeader"] {{
    font-family: 'Outfit', sans-serif !important;
    color: {text_main} !important;
}}

/* Style Streamlit sidebar as a premium Glass Panel */
[data-testid="stSidebar"] {{
    background: {nav_bg} !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid {card_border} !important;
}}

/* Hide collapse button to lock the sidebar in place like a native panel */
[data-testid="stSidebarCollapseButton"] {{
    display: none !important;
}}

/* Expand page wrapper to maximum 1280px width */
[data-testid="stAppViewBlockContainer"] {{
    max-width: 1280px !important;
    padding: 20px 20px 40px 20px !important;
}}

div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {card_bg} !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid {card_border} !important;
    box-shadow: {shadow} !important;
    border-radius: 16px !important;
    padding: 18px 22px !important;
    margin-bottom: 16px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    border-color: rgba({accent_rgb}, 0.45) !important;
    box-shadow: 0 12px 36px 0 rgba({accent_rgb}, 0.18) !important;
}}

/* Custom non-border generic container class for HTML embedding */
.glass-panel-html {{
    background: {card_bg};
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid {card_border};
    box-shadow: {shadow};
    border-radius: 16px;
    padding: 16px 20px;
    margin-bottom: 14px;
}}

/* Reduce vertical block gap in Streamlit globally */
div[data-testid="stVerticalBlock"] {{
    gap: 12px !important;
}}

/* Gradient and Text styling utilities */
.text-gradient {{
    background: linear-gradient(135deg, #4ade80 0%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
}}

.text-glow-green {{
    text-shadow: 0 0 20px rgba(34, 197, 94, 0.4);
}}

.text-sub {{
    color: {text_sub} !important;
}}

/* Hide standard Streamlit footer and link icons */
footer {{
    visibility: hidden !important;
}}

/* Primary Buttons */
div.stButton > button:first-child {{
    background: linear-gradient(135deg, {accent} 0%, #10b981 100%) !important;
    color: white !important;
    border: none !important;
    padding: 12px 24px !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba({accent_rgb}, 0.3) !important;
    width: 100%;
}}

div.stButton > button:first-child:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba({accent_rgb}, 0.5) !important;
    filter: brightness(1.1) !important;
}}

/* Streamlit Inputs */
div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea {{
    background-color: {input_bg} !important;
    color: {text_main} !important;
    border: 1px solid {card_border} !important;
    border-radius: 10px !important;
}}

/* Metrics */
[data-testid="stMetricValue"] {{
    color: {text_main} !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 800 !important;
}}
[data-testid="stMetricLabel"] {{
    color: {text_sub} !important;
}}

/* Fullscreen Confetti Iframe Override */
iframe[height="1"] {{
    position: fixed !important;
    top: 0px !important;
    left: 0px !important;
    width: 100vw !important;
    height: 100vh !important;
    pointer-events: none !important;
    z-index: 999999 !important;
    border: none !important;
}}

/* Animations */
@keyframes float {{
    0% {{ transform: translateY(0px); }}
    50% {{ transform: translateY(-10px); }}
    100% {{ transform: translateY(0px); }}
}}

.animate-float {{
    animation: float 4s ease-in-out infinite;
}}

@keyframes pulse-glow {{
    0%, 100% {{ opacity: 0.6; }}
    50% {{ opacity: 1; }}
}}

.pulse-glow {{
    animation: pulse-glow 2s ease-in-out infinite;
}}

/* Style radio option labels in Streamlit sidebar - make it larger and premium */
div[data-testid="stRadio"] label p {{
    font-size: 18px !important;
    font-weight: 600 !important;
    color: {text_main} !important;
    padding: 6px 0 !important;
    transition: all 0.2s ease !important;
}}

div[data-testid="stRadio"] label:hover p {{
    color: {accent} !important;
    transform: translateX(4px) !important;
}}

/* Custom styling to clean up selected item icon alignment if needed */
div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {{
    font-size: 18px !important;
}}
</style>
""", unsafe_allow_html=True)

# Define navigation items matching React App.jsx structure
nav_items = [
    {"id": "home", "label": "Home", "icon": "🌱"},
    {"id": "scanner", "label": "Plastic Scanner", "icon": "♻️"},
    {"id": "impact", "label": "Environmental Impact", "icon": "📊"},
    {"id": "initiatives", "label": "Govt Initiatives", "icon": "🏛️"},
    {"id": "rewards", "label": "Rewards", "icon": "🪙"},
    {"id": "team", "label": "About Team", "icon": "👥"},
    {"id": "thankyou", "label": "Thank You", "icon": "🤝"}
]

# =========================================================
# SIDEBAR NAVIGATION
# =========================================================
with st.sidebar:
    # Logo matching React brand structure
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 25px; margin-top: 10px;">
        <div style="background: #22c55e; padding: 6px; border-radius: 10px; display: flex; justify-content: center; align-items: center; width: 32px; height: 32px;">
            <span style="font-size: 16px; color: white;">🌱</span>
        </div>
        <span style="font-size: 20px; font-weight: 800; font-family: 'Outfit'; color: {text_main} !important;">
            EcoSort <span style="color: #22c55e;">AI</span>
        </span>
    </div>
    """, unsafe_allow_html=True)





    # Navigation Section
    st.markdown(f"""
    <div style="margin-top: 25px; margin-bottom: 8px;">
        <span style="font-size: 11px; text-transform: uppercase; color: {text_sub}; font-weight: 700; letter-spacing: 1px;">🧭 Navigation</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Radio Menu items with exact icons and labels
    page_options = {
        "home": "🌱 Home",
        "scanner": "♻️ Plastic Scanner",
        "impact": "📊 Environmental Impact",
        "initiatives": "🏛️ Govt Initiatives",
        "rewards": "🪙 Rewards",
        "team": "👥 About Team",
        "thankyou": "🤝 Thank You"
    }
    
    current_page = st.session_state.page
    option_list = list(page_options.keys())
    default_idx = option_list.index(current_page) if current_page in option_list else 0
    
    selected_label = st.radio(
        "Pages",
        options=list(page_options.values()),
        index=default_idx,
        label_visibility="collapsed"
    )
    
    selected_page = [k for k, v in page_options.items() if v == selected_label][0]
    if selected_page != st.session_state.page:
        st.session_state.page = selected_page
        st.query_params["page"] = selected_page
        st.rerun()
        
    # Flask Backend Connection Status indicator
    if not st.session_state.api_online:
        st.markdown(f"""
        <div style="background: rgba(234, 179, 8, 0.1); border: 1px solid rgba(234, 179, 8, 0.3); padding: 12px; border-radius: 12px; margin-top: 30px; display: flex; align-items: flex-start; gap: 8px;">
            <span style="font-size: 16px; margin-top: 2px;">⚠️</span>
            <span style="color: #eab308; font-size: 12.5px; font-weight: 600; line-height: 1.4;">Flask API Offline (Using Simulation Mode)</span>
        </div>
        """, unsafe_allow_html=True)


# =========================================================
# PAGE 1: HOME
# =========================================================
def show_home():
    # Hero Section using st.container(border=True) styled as glass card
    with st.container(border=True):
        col_text, col_img = st.columns([1.2, 0.8], gap="large")
        
        with col_text:
            st.markdown(f"""
            <div style="background: rgba(34, 197, 94, 0.1); padding: 8px 18px; border-radius: 50px; display: inline-flex; align-items: center; gap: 8px; margin-bottom: 20px; border: 1px solid rgba(34, 197, 94, 0.3);">
                <span style="color: {accent}; font-size: 13px; font-weight: 600;">♻️ Introducing EcoSort AI v2.0</span>
            </div>
            <h1 style="font-size: 3.5rem; font-weight: 800; line-height: 1.15; margin-bottom: 20px; font-family: 'Outfit', sans-serif;">
                Smart AI Plastic <span class="text-gradient">Sustainability</span> Platform
            </h1>
            <p style="font-size: 1.25rem; color: {text_sub}; margin-bottom: 35px; line-height: 1.7; font-family: 'Poppins', sans-serif;">
                Harnessing advanced computer vision and deep neural networks to accurately identify, categorize, and track plastic materials to protect our global environment.
            </p>
            """, unsafe_allow_html=True)
            
            # Streamlit buttons in equal-sized columns for identical dimensions
            c_btn1, c_btn2 = st.columns([1, 1], gap="medium")
            with c_btn1:
                if st.button("Launch Plastic Scanner 🚀", key="hero_scanner_btn"):
                    st.query_params["page"] = "scanner"
                    st.rerun()
            with c_btn2:
                if st.button("Explore Impact 📊", key="hero_impact_btn"):
                    st.query_params["page"] = "impact"
                    st.rerun()

        with col_img:
            # Standalone image without double container margins to reduce white space
            st.image(eco_hero_path, use_container_width=True)

    # Dynamic Ocean Plastic Counter Card
    current_time = time.time()
    start_of_year = datetime(datetime.now().year, 1, 1).timestamp()
    elapsed = current_time - start_of_year
    initial_count = 12845320.45 + (elapsed * 0.357)

    with st.container(border=True):
        st.markdown(f"""
        <div style="text-align: center; border-left: 5px solid #ef4444; padding: 5px 0 5px 15px; margin-bottom: 10px;">
            <h3 style="text-transform: uppercase; letter-spacing: 2px; font-size: 14px; color: #ef4444; margin: 0; font-weight: 700;">
                🚨 Global Plastic Waste Counter 🚨
            </h3>
        </div>
        """, unsafe_allow_html=True)

        counter_html = f"""
        <div style="text-align: center; font-family: monospace; font-size: 2.5rem; font-weight: 800; color: #ef4444; text-shadow: 0 0 10px rgba(239, 68, 68, 0.2); padding: 5px 0;">
            <span id="counter">{initial_count:,.3f}</span>
        </div>
        <script>
            let count = {initial_count};
            const counterEl = document.getElementById('counter');
            setInterval(() => {{
                count += 0.0357; 
                counterEl.innerText = count.toLocaleString(undefined, {{ minimumFractionDigits: 3, maximumFractionDigits: 3 }});
            }}, 100);
        </script>
        """
        st.iframe(counter_html, height=60)
        
        st.markdown(f"""
        <p style="text-align: center; color: {text_sub}; margin: 5px 0 0 0; font-size: 14px;">
            Tons of plastic waste dumped into our oceans globally this year alone.
        </p>
        """, unsafe_allow_html=True)

    # Stats and Highlights Row
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown(f"""
            <div style="display: flex; flex-direction: column; gap: 15px; min-height: 200px;">
                <div style="background: rgba(34, 197, 94, 0.1); padding: 12px; border-radius: 12px; width: fit-content; font-size: 28px; line-height: 1;">
                    ♻️
                </div>
                <h3 style="font-size: 20px; font-weight: 700; margin: 0;">Smart Recycling</h3>
                <p style="color: {text_sub}; font-size: 13.5px; line-height: 1.6; margin: 0;">
                    Identifies plastic items from codes 1-7 instantly, giving you instructions on how to wash and sort each resin category.
                </p>
            </div>
            """, unsafe_allow_html=True)
    with col2:
        with st.container(border=True):
            st.markdown(f"""
            <div style="display: flex; flex-direction: column; gap: 15px; min-height: 200px;">
                <div style="background: rgba(14, 165, 233, 0.1); padding: 12px; border-radius: 12px; width: fit-content; font-size: 28px; line-height: 1;">
                    🪙
                </div>
                <h3 style="font-size: 20px; font-weight: 700; margin: 0;">EcoCoin Rewards</h3>
                <p style="color: {text_sub}; font-size: 13.5px; line-height: 1.6; margin: 0;">
                    Convert sorted plastic into EcoCoins. Gain badges, unlock milestones, and top the leaderboard to secure discount rewards.
                </p>
            </div>
            """, unsafe_allow_html=True)
    with col3:
        with st.container(border=True):
            st.markdown(f"""
            <div style="display: flex; flex-direction: column; gap: 15px; min-height: 200px;">
                <div style="background: rgba(239, 68, 68, 0.1); padding: 12px; border-radius: 12px; width: fit-content; font-size: 28px; line-height: 1;">
                    ⚠️
                </div>
                <h3 style="font-size: 20px; font-weight: 700; margin: 0;">Hazard Detection</h3>
                <p style="color: {text_sub}; font-size: 13.5px; line-height: 1.6; margin: 0;">
                    Flag highly toxic compounds like PVC (Code 3) or PS (Code 6) to keep carcinogenic microplastics out of food and water.
                </p>
            </div>
            """, unsafe_allow_html=True)

    # CNN Model Architecture details
    with st.container(border=True):
        col_c1, col_c2 = st.columns([1.2, 0.8])
        with col_c1:
            st.markdown(f"""
            <h3 style="font-size: 20px; font-weight: 800; margin-bottom: 20px;">
                🧠 Deep Learning CNN Classifier Architecture
            </h3>
            <div style="font-size: 14px; line-height: 1.7; color: {text_sub};">
                <p style="margin-bottom: 15px;">
                    Our platform runs a custom <b>Convolutional Neural Network (CNN)</b> built in TensorFlow & Keras. CNNs are highly effective for computer vision tasks as they automatically detect edges, textures, and shape features to classify materials.
                </p>
                <ul style="padding-left: 20px; display: flex; flex-direction: column; gap: 8px; margin-bottom: 15px;">
                    <li><b>Convolutional Layers:</b> 3 Conv2D layers (32, 64, and 128 filter kernels) to extract hierarchical visual features.</li>
                    <li><b>Pooling Layers:</b> MaxPooling2D to downsample spatial dimensions and reduce computational complexity.</li>
                    <li><b>Dense Classifier:</b> Fully connected layers with 128 hidden units mapping to a 6-node Softmax output layer.</li>
                    <li><b>Performance:</b> Achieved a training validation accuracy of <b>~79.46%</b> over 10 epochs using the Adam Optimizer.</li>
                </ul>
                <p style="margin: 0;">
                    When a user captures or uploads a photo, the image is resized to <b>224x224 pixels</b>, normalized, and evaluated in real-time by the inference engine to map the item to its respective circular economy recycling codes.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_c2:
            st.image(ai_workflow_path, use_container_width=True)

    # Facts Carousel
    with st.container(border=True):
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
            <span style="font-size: 20px; color: {accent};">❓</span>
            <span style="font-size: 14px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: {accent};">Did You Know?</span>
        </div>
        """, unsafe_allow_html=True)
        
        facts_carousel_html = """
        <div id="carousel-container" style="font-family: 'Poppins', sans-serif; color: #cbd5e1; min-height: 80px; transition: all 0.5s ease; padding: 0 20px; display: flex; align-items: center; justify-content: center;">
            <p id="fact-text" style="font-size: 1.15rem; line-height: 1.7; margin: 0; font-style: italic; text-align: center; color: #cbd5e1;"></p>
        </div>
        <script>
            const facts = [
              "More than 8 million tons of plastic enter our oceans every year, equal to dumping a garbage truck full of plastic every minute.",
              "Plastic packaging is designed for single-use, but the plastic material itself takes up to 1000 years to decompose in landfills.",
              "Recycling one ton of plastic saves approximately 5,774 kilowatt-hours of energy and 16.3 barrels of oil.",
              "Over 90% of all seabirds have plastic pieces in their stomachs, disrupting marine food chains globally.",
              "By 2050, it is estimated that there will be more plastic by weight in the oceans than fish.",
              "Many everyday items, like fleece jackets and carpets, can be manufactured from recycled plastic bottles (PET)."
            ];
            let idx = 0;
            const textEl = document.getElementById('fact-text');
            function rotateFact() {
                textEl.innerText = `"${facts[idx]}"`;
                idx = (idx + 1) % facts.length;
            }
            rotateFact();
            setInterval(rotateFact, 6000);
        </script>
        """
        st.iframe(facts_carousel_html, height=90)

# =========================================================
# PAGE 2: PLASTIC SCANNER
# =========================================================
def show_scanner():
    st.markdown(f"""
    <h2 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 10px;">
        ♻️ AI Plastic <span class="text-gradient">Scanner</span>
    </h2>
    <p style="color: {text_sub}; margin-bottom: 40px;">
        Provide a plastic item photo via webcam or file upload to run the CNN classifier.
    </p>
    """, unsafe_allow_html=True)

    input_mode = st.radio(
        "Choose Input Method",
        ["Upload Image", "Use Webcam"],
        horizontal=True,
        label_visibility="collapsed"
    )

    col_left, col_right = st.columns([1, 1])

    image_to_detect = None
    image_bytes = None

    with col_left:
        with st.container(border=True):
            if input_mode == "Upload Image":
                uploaded_file = st.file_uploader(
                    "Upload Plastic Image",
                    type=["jpg", "jpeg", "png"],
                    label_visibility="collapsed"
                )
                if uploaded_file:
                    image_to_detect = Image.open(uploaded_file)
                    image_bytes = uploaded_file.getvalue()
                    st.image(image_to_detect, caption="Preview Image", use_container_width=True)
            else:
                camera_image = st.camera_input("Capture Plastic Image")
                if camera_image:
                    image_to_detect = Image.open(camera_image)
                    image_bytes = camera_image.getvalue()

    prediction = None

    with col_right:
        with st.container(border=True):
            # Scanner trigger
            if image_to_detect is not None:
                if st.button("🚀 Start AI Detection", use_container_width=True):
                    with st.spinner("Analyzing Chemical Composition..."):
                        if st.session_state.api_online:
                            try:
                                files = {"image": ("scan.jpg", image_bytes, "image/jpeg")}
                                response = requests.post("http://localhost:5000/predict", files=files)
                                if response.status_code == 200:
                                    prediction = response.json()
                                    if not prediction.get("success"):
                                        st.error(f"Detection Error: {prediction.get('error')}")
                                        prediction = None
                                else:
                                    st.error("Inference endpoint returned error.")
                            except Exception as e:
                                st.error(f"Connection failure: {e}")
                        
                        if prediction is None:
                            time.sleep(1.5)
                            p_key = np.random.choice(['PET', 'HDPE', 'PVC', 'LDPE', 'PP', 'PS', 'Other'])
                            confidence = float(np.random.uniform(78.5, 99.2))
                            details = PLASTIC_INFO_LOCAL[p_key]
                            prediction = {
                                "success": True,
                                "plastic_type": p_key,
                                "confidence": confidence,
                                "details": details,
                                "image_id": "simulated"
                            }
                        
                        st.session_state.current_prediction = prediction

            current_pred = st.session_state.get("current_prediction")
            if not current_pred:
                st.markdown(f"""
                <div style="text-align: center; color: {text_sub}; padding: 40px 0;">
                    <span style="font-size: 55px;">📊</span>
                    <h3 style="margin-top: 15px;">Awaiting Scanner Input</h3>
                    <p style="font-size: 13px; margin-top: 5px;">Upload or capture an image and click "Start AI Detection" to see chemical details and ecological impact charts.</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                details = current_pred["details"]
                p_type = current_pred["plastic_type"]
                conf = current_pred["confidence"]

                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid {card_border}; padding-bottom: 15px; margin-bottom: 15px;">
                    <div>
                        <span style="text-transform: uppercase; font-size: 11px; font-weight: 800; letter-spacing: 1.5px; color: {accent};">Detection Success</span>
                        <h3 style="font-size: 22px; font-weight: 800; margin: 0;">{details['name']}</h3>
                    </div>
                    <div style="background: rgba({accent_rgb}, 0.1); border: 1px solid {accent}; padding: 5px 12px; border-radius: 50px;">
                        <span style="font-size: 13px; color: {accent}; font-weight: 700;">Code {details['code']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    with st.container(border=True):
                        st.markdown(f"""
                        <span style="font-size: 12px; color: {text_sub};">Confidence Score</span>
                        <h4 style="font-size: 20px; font-weight: 700; margin: 4px 0 0 0;">{conf:.2f}%</h4>
                        """, unsafe_allow_html=True)
                with c2:
                    hrisk = details['harmfulness']
                    hcolor = "#ef4444" if details['env_risk'] > 60 else "#22c55e"
                    with st.container(border=True):
                        st.markdown(f"""
                        <span style="font-size: 12px; color: {text_sub};">Harmfulness Level</span>
                        <h4 style="font-size: 20px; font-weight: 700; color: {hcolor}; margin: 4px 0 0 0;">{hrisk}</h4>
                        """, unsafe_allow_html=True)

                st.markdown(f"""
                <div style="display: flex; flex-direction: column; gap: 10px; font-size: 13px; margin-bottom: 20px; margin-top: 15px;">
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <span style="color: {text_sub}; font-weight: 500;">Carbon Footprint Estimate:</span>
                        <span style="font-weight: 600;">{details['carbon_footprint']}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <span style="color: {text_sub}; font-weight: 500;">Estimated Decomposition:</span>
                        <span style="font-weight: 600;">{details['decomp_time']}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                        <span style="color: {text_sub}; font-weight: 500;">Recyclability Rate:</span>
                        <span style="font-weight: 600; color: {accent};">{details['recyclability']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_act1, col_act2 = st.columns(2)
                with col_act1:
                    if current_pred.get("image_id") != "simulated" and st.session_state.api_online:
                        pdf_url = f"http://localhost:5000/report?type={p_type}&confidence={conf}&image_id={current_pred.get('image_id')}"
                    else:
                        pdf_url = "#"
                    
                    if pdf_url != "#":
                        st.markdown(f'<a href="{pdf_url}" target="_blank"><button style="background: linear-gradient(135deg, {accent} 0%, #10b981 100%); color: white; border: none; padding: 12px 24px; border-radius: 12px; font-weight: 600; cursor: pointer; width: 100%; box-shadow: 0 4px 15px rgba({accent_rgb}, 0.3);">📄 Download PDF Report</button></a>', unsafe_allow_html=True)
                    else:
                        if st.button("📄 Simulation Report (N/A)"):
                            st.info("Direct PDF generation is simulated. Run the local backend to download actual reports.")
                with col_act2:
                    st.iframe(f'<button style="background: transparent; color: {text_main}; border: 2px solid {card_border}; padding: 12px; border-radius: 12px; cursor: pointer; width: 100%; font-weight: 600; font-family: sans-serif;" onclick="window.parent.print()">🖨️ Print</button>', height=50)

    current_pred = st.session_state.get("current_prediction")
    if current_pred:
        st.markdown('<div style="margin-top: 40px;"></div>', unsafe_allow_html=True)
        st.markdown('<h3 style="font-size: 20px; font-weight: 800; margin-bottom: 20px;">📊 Environmental Profile Visualizations</h3>', unsafe_allow_html=True)

        c_chart1, c_chart2, c_chart3 = st.columns(3)
        p_type = current_pred["plastic_type"]
        details = current_pred["details"]

        with c_chart1:
            with st.container(border=True):
                st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
                    <span style="font-size: 13px; font-weight: 600; color: {text_sub}; margin-bottom: 10px;">Carbon Footprint (kg CO2 / kg)</span>
                </div>
                """, unsafe_allow_html=True)
                
                p_keys = ['PET', 'HDPE', 'PVC', 'LDPE', 'PP', 'PS', 'Other']
                footprints = [2.15, 1.60, 3.10, 1.80, 1.70, 2.50, 2.80]
                colors = [accent if pk == p_type else 'rgba(128,128,128,0.2)' for pk in p_keys]

                fig1 = go.Figure(data=[go.Bar(
                    x=p_keys,
                    y=footprints,
                    marker_color=colors,
                    hoverinfo='y+x'
                )])
                fig1.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color=text_main, family='Poppins'),
                    height=180,
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
                )
                st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

        with c_chart2:
            env_risk = details['env_risk']
            with st.container(border=True):
                st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
                    <span style="font-size: 13px; font-weight: 600; color: {text_sub}; margin-bottom: 10px;">Environmental Risk Score</span>
                </div>
                """, unsafe_allow_html=True)

                gauge_color = "#ef4444" if env_risk > 60 else "#22c55e"
                fig2 = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=env_risk,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [None, 100], 'tickcolor': text_main, 'tickwidth': 1},
                        'bar': {'color': gauge_color},
                        'bgcolor': "rgba(255,255,255,0.05)",
                        'borderwidth': 1,
                        'bordercolor': "rgba(255,255,255,0.1)",
                    }
                ))
                fig2.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color=text_main, family='Poppins'),
                    height=180,
                    margin=dict(l=30, r=30, t=20, b=10)
                )
                st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

        with c_chart3:
            with st.container(border=True):
                st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
                    <span style="font-size: 13px; font-weight: 600; color: {text_sub}; margin-bottom: 10px;">Recyclability Rate Donut</span>
                </div>
                """, unsafe_allow_html=True)

                recyclability_val = int(details['recyclability'].replace('%', ''))
                fig3 = go.Figure(data=[go.Pie(
                    labels=['Recyclable', 'Non-Recyclable'],
                    values=[recyclability_val, 100 - recyclability_val],
                    hole=.6,
                    marker=dict(colors=[accent, 'rgba(128,128,128,0.1)']),
                    textinfo='none',
                    hoverinfo='label+percent'
                )])
                fig3.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color=text_main, family='Poppins'),
                    showlegend=False,
                    height=180,
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

        st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
        col_dmg1, col_dmg2 = st.columns(2)
        
        with col_dmg1:
            with st.container(border=True):
                st.markdown(f"""
                <h4 style="font-size: 17px; font-weight: 700; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; color: {gauge_color} !important;">
                    ⚠️ Environmental Damage Factors
                </h4>
                <p style="font-size: 13.5px; line-height: 1.6;">
                    🌊 <b>River Pollution:</b> {details.get('river_impact', 'N/A')}
                </p>
                <p style="font-size: 13.5px; line-height: 1.6; margin-top: 10px;">
                    🦆 <b>Wildlife Impact:</b> {details.get('wildlife_impact', 'N/A')}
                </p>
                """, unsafe_allow_html=True)

        with col_dmg2:
            with st.container(border=True):
                st.markdown(f"""
                <h4 style="font-size: 17px; font-weight: 700; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; color: #eab308 !important;">
                    ⚠️ Human Health Concerns
                </h4>
                <p style="font-size: 13.5px; line-height: 1.6;">
                    💊 <b>Toxicity Profile:</b> {details.get('health_risk', 'N/A')}
                </p>
                """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown(f"""
            <h3 style="font-size: 18px; font-weight: 800; margin-bottom: 15px;">💡 Eco-Disposal & Sustainability Recommendations</h3>
            <p style="font-size: 14px; line-height: 1.6;">
                ♻️ <b>Recommended Disposal Protocol:</b> {details.get('disposal', 'N/A')}
            </p>
            <p style="font-size: 14px; line-height: 1.6; margin-top: 12px;">
                🌱 <b>Sustainable Alternative Materials:</b> {details.get('alternatives', 'N/A')}
            </p>
            """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; gap: 10px;">
            <span style="font-weight: 600; color: {text_main}; font-size: 14px; text-align: center;">
                "Every piece of plastic correctly recycled helps protect nature."
            </span>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# PAGE 3: ENVIRONMENTAL IMPACT
# =========================================================
def show_impact():
    with st.container(border=True):
        col_img, col_text = st.columns([1.0, 2.0], gap="medium")
        with col_img:
            st.image(eco_impact_path, use_container_width=True)
        with col_text:
            st.markdown(f"""
            <h2 style="font-size: 3.2rem; font-weight: 800; margin-bottom: 8px;">
                🌍 Environmental <span class="text-gradient">Impact Dashboard</span>
            </h2>
            <p style="color: {text_sub}; line-height: 1.7; font-size: 19px; margin: 0;">
                Explore how plastics degrade ecosystems, enter the human food supply, and contribute to global climate change. Microplastics and toxic additives endanger land, freshwater, and marine biodiversity.
            </p>
            """, unsafe_allow_html=True)

    for sec in IMPACT_SECTIONS:
        with st.container(border=True):
            col_img, col_content = st.columns([1.3, 1.7], gap="medium")
            with col_img:
                img_path = os.path.join(assets_dir, sec["image_file"])
                if os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                else:
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.03); border: 1px solid {card_border}; padding: 15px; border-radius: 15px; display: flex; justify-content: center; align-items: center; font-size: 48px; height: 180px;">
                        {sec['icon']}
                    </div>
                    """, unsafe_allow_html=True)
            with col_content:
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 8px; gap: 10px;">
                    <h3 style="font-size: 25px; font-weight: 800; margin: 0; display: flex; align-items: center; gap: 8px;">
                        <span>{sec['icon']}</span> {sec['title']}
                    </h3>
                    <span style="font-size: 16px; font-weight: 800; background: rgba(239, 68, 68, 0.1); color: #ef4444; padding: 6px 14px; border-radius: 50px; border: 1px solid rgba(239,68,68,0.2);">
                        {sec['stats']}
                    </span>
                </div>
                <p style="color: {text_sub}; font-size: 18px; line-height: 1.7; margin-bottom: 10px;">
                    {sec['details']}
                </p>
                <div style="background: rgba({accent_rgb}, 0.05); padding: 12px 18px; border-radius: 12px; font-size: 16px; border-left: 4px solid {accent}; color: {text_main}; font-weight: 500; line-height: 1.6;">
                    💡 <b>Highlight:</b> {sec['highlight']}
                </div>
                """, unsafe_allow_html=True)

    st.markdown('<h3 style="font-size: 28px; font-weight: 800; margin-top: 25px; margin-bottom: 15px;">⚠️ Critical Planetary Boundary Warnings</h3>', unsafe_allow_html=True)
    
    col_t1, col_t2 = st.columns(2)
    for i, topic in enumerate(CRITICAL_TOPICS):
        target_col = col_t1 if i % 2 == 0 else col_t2
        with target_col:
            with st.container(border=True):
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                    <span style="font-size: 22px; color: #ef4444;">⚠️</span>
                    <h4 style="font-size: 20px; font-weight: 700; margin: 0;">{topic['title']}</h4>
                </div>
                <p style="color: {text_sub}; font-size: 16px; line-height: 1.7; margin: 0;">
                    {topic['desc']}
                </p>
                """, unsafe_allow_html=True)

    st.markdown('<h3 style="font-size: 28px; font-weight: 800; margin-top: 25px; margin-bottom: 15px;">🎥 Educational Documentaries</h3>', unsafe_allow_html=True)
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        with st.container(border=True):
            st.markdown("""
            <div style="padding: 10px 0;">
                <h4 style="font-size: 20px; font-weight: 700; margin-bottom: 8px; color: #f8fafc;">How Microplastics Affect the Human Body</h4>
                <p style="color: #94a3b8; font-size: 16px; line-height: 1.6; margin-bottom: 18px;">
                    Learn about chemical exposure vectors, microplastic absorption in internal organs, and the long-term toxicity profiles on human health.
                </p>
                <a href="https://www.youtube.com/watch?v=gGh0L9LTTA0" target="_blank" style="text-decoration: none;">
                    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); padding: 8px 16px; border-radius: 8px; display: inline-flex; align-items: center; gap: 8px; color: #ef4444; font-weight: 600; font-size: 14px;">
                        🎥 Watch Documentary on YouTube ↗
                    </div>
                </a>
            </div>
            """, unsafe_allow_html=True)
        
    with col_v2:
        with st.container(border=True):
            st.markdown("""
            <div style="padding: 10px 0;">
                <h4 style="font-size: 20px; font-weight: 700; margin-bottom: 8px; color: #f8fafc;">The Plastic Crisis in Ocean Ecosystems</h4>
                <p style="color: #94a3b8; font-size: 16px; line-height: 1.6; margin-bottom: 18px;">
                    Visualizing the Great Pacific Garbage Patch, biological entanglement of marine wildlife, and the breakdown of marine food webs.
                </p>
                <a href="https://www.youtube.com/watch?v=HQTUWK7CM-Y" target="_blank" style="text-decoration: none;">
                    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); padding: 8px 16px; border-radius: 8px; display: inline-flex; align-items: center; gap: 8px; color: #ef4444; font-weight: 600; font-size: 14px;">
                        🎥 Watch Documentary on YouTube ↗
                    </div>
                </a>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# PAGE 4: GOVT INITIATIVES
# =========================================================
def show_initiatives():
    st.markdown(f"""
    <h2 style="font-size: 3.0rem; font-weight: 800; margin-bottom: 8px;">
        🏛️ Government <span class="text-gradient">Policies & Initiatives</span>
    </h2>
    <p style="color: {text_sub}; margin-bottom: 20px; font-size: 19px; line-height: 1.7;">
        Understand India's national environmental protocols, recycling regulations, and campaigns working toward a circular economy.
    </p>
    """, unsafe_allow_html=True)

    tab_names = [init["title"].split(' (')[0] for init in INITIATIVES]
    tabs = st.tabs(tab_names)

    for idx, tab in enumerate(tabs):
        init = INITIATIVES[idx]
        with tab:
            st.markdown(f"""
            <h3 style="font-size: 26px; font-weight: 800; margin-top: 10px; margin-bottom: 10px; color: {text_main};">🏛️ {init['title']}</h3>
            <p style="color: {text_sub}; font-size: 17.5px; line-height: 1.7; margin-bottom: 15px;">
                {init['desc']}
            </p>
            <p style="font-size: 16px; font-weight: 600; margin: 15px 0 6px 0; color: {text_main};">Official Effectiveness Index: {init['effectiveness']}</p>
            """, unsafe_allow_html=True)

            st.progress(int(init['effectiveness'].replace('%', '')))
            
            col_metric, col_video_btn = st.columns([1.3, 0.7], gap="medium")
            with col_metric:
                st.markdown(f"""
                <div style="background: rgba({accent_rgb}, 0.05); border: 1px solid {card_border}; padding: 12px 18px; border-radius: 12px; margin-top: 15px;">
                    <span style="font-size: 13px; color: {text_sub}; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; display: block; margin-bottom: 4px;">Key Impact Metric</span>
                    <p style="font-size: 16.5px; font-weight: 700; margin: 0; color: {accent};">{init['stats']}</p>
                </div>
                """, unsafe_allow_html=True)
            with col_video_btn:
                st.markdown(f"""
                <div style="background: rgba(239, 68, 68, 0.03); border: 1px solid rgba(239, 68, 68, 0.2); padding: 12px 18px; border-radius: 12px; margin-top: 15px; display: flex; flex-direction: column; justify-content: center; height: calc(100% - 15px);">
                    <span style="font-size: 13px; color: {text_sub}; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; display: block; margin-bottom: 6px;">Campaign Media</span>
                    <a href="{init['video']}" target="_blank" style="text-decoration: none;">
                        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); padding: 8px 14px; border-radius: 8px; display: inline-flex; align-items: center; gap: 8px; color: #ef4444; font-weight: 600; font-size: 14px; width: 100%; justify-content: center;">
                            🎥 View on YouTube ↗
                        </div>
                    </a>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('<h3 style="font-size: 24px; font-weight: 800; margin-top: 25px; margin-bottom: 15px;">⏳ Policy Timeline & Milestones</h3>', unsafe_allow_html=True)
    
    timeline_items_html = ""
    for item in TIMELINE:
        timeline_items_html += f"""
        <div style="position: relative; margin-bottom: 10px;">
            <div style="position: absolute; left: -23px; top: 12px; width: 10px; height: 10px; border-radius: 50%; background: {accent}; box-shadow: 0 0 10px rgba({accent_rgb}, 0.8);"></div>
            <div class="glass-panel-html" style="padding: 12px 18px; background: rgba(255,255,255,0.02); margin-bottom: 0;">
                <div style="display: flex; gap: 15px; align-items: center; flex-wrap: wrap;">
                    <span style="font-size: 20px; font-weight: 800; color: {accent}; font-family: monospace;">{item['year']}</span>
                    <div>
                        <h4 style="font-size: 16.5px; font-weight: 700; margin: 0; color: {text_main};">{item['event']}</h4>
                        <p style="color: {text_sub}; font-size: 14px; margin: 2px 0 0 0;">{item['details']}</p>
                    </div>
                </div>
            </div>
        </div>
        """

    timeline_html = f"""
    <div style="display: flex; flex-direction: column; gap: 12px; position: relative; padding-left: 30px;">
        <div style="position: absolute; left: 12px; top: 18px; bottom: 18px; width: 2px; background: {card_border};"></div>
        {timeline_items_html}
    </div>
    """
    render_html(timeline_html)

# =========================================================
# PAGE 5: REWARDS
# =========================================================
def show_rewards():
    with st.container(border=True):
        col_text, col_img = st.columns([1.4, 0.6])
        with col_text:
            st.markdown(f"""
            <h2 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 10px;">
                🪙 EcoCoin <span class="text-gradient">Rewards Center</span>
            </h2>
            <p style="color: {text_sub}; margin-bottom: 20px; line-height: 1.6; font-size: 15px;">
                Turn your sorted plastic waste into EcoCoins! Redeem coins for cash, track achievements, and lead the community.
            </p>
            """, unsafe_allow_html=True)
            
            # Get current numbers
            weight_val = 0.0
            coins_val = 0
            leaderboard_data = []

            if st.session_state.api_online:
                try:
                    phone = st.session_state.get("user_phone", "")
                    url = f"http://localhost:5000/reward?phone={phone}" if phone else "http://localhost:5000/reward"
                    response = requests.get(url, timeout=1.5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("success"):
                            weight_val = float(data.get("total_weight", 0.0))
                            coins_val = int(data.get("total_coins", 0))
                            leaderboard_data = data.get("leaderboard", [])
                except Exception:
                    pass
            else:
                # Local Simulation Mode
                phone = st.session_state.get("user_phone", "")
                if phone and phone in st.session_state.sim_users:
                    user_data = st.session_state.sim_users[phone]
                    weight_val = float(user_data.get("weight", 0.0))
                    coins_val = int(user_data.get("coins", 0))
                
                leaderboard_data = sorted(
                    [{"name": u["name"], "coins": u["coins"]} for u in st.session_state.sim_users.values()],
                    key=lambda x: x["coins"],
                    reverse=True
                )

            current_badge = "Novice Recycler"
            for badge in BADGES:
                if weight_val >= badge["minWeight"]:
                    current_badge = badge["name"]
            
            st.markdown(f"""
            <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(251, 191, 36, 0.1); padding: 6px 15px; border-radius: 50px; border: 1px solid rgba(251, 191, 36, 0.3); font-size: 13px; font-weight: 600;">
                <span>Current Rank: <strong style="color: #fbbf24;">{current_badge}</strong></span>
            </div>
            """, unsafe_allow_html=True)

        with col_img:
            with st.container(border=True):
                st.image(eco_rewards_path, use_container_width=True)

    # Quick EcoWallet Access Panel
    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(f"""
        <h3 style="font-size: 18px; font-weight: 800; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
            🔑 Quick EcoWallet Access
        </h3>
        """, unsafe_allow_html=True)
        
        if st.session_state.get("user_phone"):
            st.markdown(f"""
            <div style="background: rgba(34, 197, 94, 0.1); padding: 12px 18px; border-radius: 12px; border: 1px solid rgba(34, 197, 94, 0.3); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;">
                <div>
                    <span style="font-size: 11px; color: {text_sub}; display: block;">Active Wallet Profile</span>
                    <span style="font-size: 16px; font-weight: 700; color: {text_main};">👤 {st.session_state.user_name} (Phone: {st.session_state.user_phone})</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Logout / Switch Wallet", key="btn_logout", use_container_width=True):
                st.session_state.user_phone = ""
                st.session_state.user_name = ""
                st.success("Logged out successfully!")
                time.sleep(0.5)
                st.rerun()
        else:
            st.markdown(f"""
            <p style="font-size: 13.5px; color: {text_sub}; margin-bottom: 15px;">
                Access your existing EcoWallet by typing your Phone Number. New users: enter your Name as well to register!
            </p>
            """, unsafe_allow_html=True)
            c_acc1, c_acc2 = st.columns(2)
            with c_acc1:
                access_phone = st.text_input("Phone Number", placeholder="e.g. 9876543210", key="access_phone_input")
            with c_acc2:
                access_name = st.text_input("Name (New Users)", placeholder="e.g. Rupa Kundu", key="access_name_input")
            
            if st.button("Access My EcoWallet 🚀", key="btn_access_wallet", use_container_width=True):
                if access_phone.strip():
                    phone_clean = access_phone.strip()
                    name_clean = access_name.strip()
                    
                    fetched_name = ""
                    if st.session_state.api_online:
                        try:
                            res = requests.get(f"http://localhost:5000/reward?phone={phone_clean}", timeout=1.5)
                            if res.status_code == 200:
                                data = res.json()
                                if data.get("success") and data.get("name"):
                                    fetched_name = data.get("name")
                        except Exception:
                            pass
                    else:
                        if phone_clean in st.session_state.sim_users:
                            fetched_name = st.session_state.sim_users[phone_clean]["name"]
                            
                    st.session_state.user_phone = phone_clean
                    if fetched_name:
                        st.session_state.user_name = fetched_name
                        st.success(f"Welcome back, {fetched_name}! EcoWallet loaded.")
                    else:
                        st.session_state.user_name = name_clean if name_clean else f"User {phone_clean[-4:]}"
                        st.success(f"EcoWallet profile set for {st.session_state.user_name}!")
                    
                    time.sleep(1.0)
                    st.rerun()
                else:
                    st.error("Please enter a valid phone number.")

    # Metrics Row
    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        with st.container(border=True):
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 20px;">
                <div style="background: rgba(251, 191, 36, 0.1); padding: 15px; border-radius: 15px; font-size: 32px; line-height: 1;">🪙</div>
                <div>
                    <span style="font-size: 13px; color: {text_sub};">EcoCoin Balance</span>
                    <h2 style="font-size: 28px; font-weight: 800; margin: 0;">{coins_val} Coins</h2>
                    <span style="font-size: 13px; color: {accent}; font-weight: 600;">(Rs. {coins_val * 0.10:.2f} INR)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    with c_m2:
        with st.container(border=True):
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 20px;">
                <div style="background: rgba(34, 197, 94, 0.1); padding: 15px; border-radius: 15px; font-size: 32px; line-height: 1;">⚖️</div>
                <div>
                    <span style="font-size: 13px; color: {text_sub};">Total Weight Recycled</span>
                    <h2 style="font-size: 28px; font-weight: 800; margin: 0;">{weight_val:.2f} kg</h2>
                </div>
            </div>
            """, unsafe_allow_html=True)
    with c_m3:
        with st.container(border=True):
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 20px;">
                <div style="background: rgba(168, 85, 247, 0.1); padding: 15px; border-radius: 15px; font-size: 32px; line-height: 1;">🏆</div>
                <div>
                    <span style="font-size: 13px; color: {text_sub};">Current Level</span>
                    <h3 style="font-size: 18px; font-weight: 800; margin: 0;">{current_badge}</h3>
                </div>
            </div>
            """, unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    with col_left:
        with st.container(border=True):
            st.markdown(f"""
            <h3 style="font-size: 20px; font-weight: 800; margin-bottom: 20px; display: flex; align-items: center; gap: 8px;">
                ⚖️ Log Plastic Disposal Transaction
            </h3>
            """, unsafe_allow_html=True)
            
            # Prefill details if logged in
            default_phone = st.session_state.get("user_phone", "")
            default_name = st.session_state.get("user_name", "")
            
            tx_phone = st.text_input("Phone Number", value=default_phone, placeholder="e.g. 9876543210", key="tx_deposit_phone")
            tx_name = st.text_input("Name", value=default_name, placeholder="e.g. Rupa Kundu", key="tx_deposit_name")
            
            weight_input = st.number_input(
                "Plastic Weight (in kg)",
                min_value=0.0,
                step=0.1,
                format="%.2f",
                key="weight_tx_input"
            )
            
            # Dynamic Live Conversion Preview
            preview_coins = 0
            if weight_input >= 300:
                preview_coins = 5000
            elif weight_input >= 100:
                preview_coins = 1500
            elif weight_input >= 50:
                preview_coins = 700
            elif weight_input >= 10:
                preview_coins = 120
            elif weight_input > 0:
                preview_coins = int(weight_input * 10)
            
            preview_cash = preview_coins * 0.10
            
            if weight_input > 0:
                st.markdown(f"""
                <div style="background: rgba({accent_rgb}, 0.05); padding: 12px; border-radius: 12px; border: 1px dashed {card_border}; margin-top: 10px; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-size: 13px; color: {text_sub};">Coins to Earn:</span>
                        <span style="font-size: 14px; font-weight: 700; color: #fbbf24;">{preview_coins} Coins</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 13px; color: {text_sub};">Equivalent Cash Value:</span>
                        <span style="font-size: 14px; font-weight: 700; color: {accent};">Rs. {preview_cash:.2f} INR</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("Deposit & Earn Coins", key="btn_deposit"):
                phone_clean = tx_phone.strip()
                name_clean = tx_name.strip()
                
                if not phone_clean:
                    st.error("Phone number is required to log transactions.")
                elif weight_input <= 0.0:
                    st.error("Please enter a valid weight larger than 0.")
                else:
                    with st.spinner("Processing transaction..."):
                        success_tx = False
                        earned_coins = 0
                        
                        if st.session_state.api_online:
                            try:
                                payload = {
                                    "phone": phone_clean,
                                    "name": name_clean,
                                    "weight": weight_input
                                }
                                res = requests.post("http://localhost:5000/reward", json=payload, timeout=2.0)
                                if res.status_code == 200:
                                    data = res.json()
                                    if data.get("success"):
                                        success_tx = True
                                        earned_coins = data.get("coins_earned")
                                        if data.get("name"):
                                            st.session_state.user_name = data.get("name")
                            except Exception:
                                pass
                        
                        if not success_tx:
                            # Local Simulation Mode
                            earned_coins = preview_coins
                            if phone_clean not in st.session_state.sim_users:
                                if not name_clean:
                                    name_clean = f"User {phone_clean[-4:]}" if len(phone_clean) >= 4 else "New User"
                                st.session_state.sim_users[phone_clean] = {
                                    "name": name_clean,
                                    "weight": weight_input,
                                    "coins": earned_coins
                                }
                            else:
                                user_data = st.session_state.sim_users[phone_clean]
                                if name_clean:
                                    user_data["name"] = name_clean
                                user_data["weight"] = user_data.get("weight", 0.0) + weight_input
                                user_data["coins"] = user_data.get("coins", 0) + earned_coins
                            
                            st.session_state.user_name = st.session_state.sim_users[phone_clean]["name"]
                            
                        # Save session profile
                        st.session_state.user_phone = phone_clean
                        
                        st.success(f"Transaction completed! Recycled {weight_input} kg, earned {earned_coins} EcoCoins!")
                        trigger_confetti()
                        time.sleep(1.0)
                        st.rerun()

            # Milestone Level Progress
            next_badge = None
            for badge in BADGES:
                if weight_val < badge["minWeight"]:
                    next_badge = badge
                    break
            
            st.markdown('<div style="margin-top: 30px;">', unsafe_allow_html=True)
            if next_badge:
                p_idx = BADGES.index(next_badge) - 1
                prev_min = BADGES[p_idx]["minWeight"] if p_idx >= 0 else 0.0
                range_val = next_badge["minWeight"] - prev_min
                prog_val = weight_val - prev_min
                prog_pct = min(100, int((prog_val / range_val) * 100))
                
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px;">
                    <span>Progress to next rank: <b>{next_badge['name']}</b></span>
                    <span>{weight_val:.2f} / {next_badge['minWeight']:.1f} kg</span>
                </div>
                """, unsafe_allow_html=True)
                st.progress(prog_pct)
            else:
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 8px;">
                    <span>Progress to next rank: <b>Zero-Waste Legend (Max)</b></span>
                    <span>{weight_val:.2f} kg / 300.0 kg</span>
                </div>
                """, unsafe_allow_html=True)
                st.progress(100)
            st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        with st.container(border=True):
            st.markdown(f"""
            <h3 style="font-size: 20px; font-weight: 800; margin-bottom: 20px; display: flex; align-items: center; gap: 8px;">
                🏛️ Cash Conversion Wallet
            </h3>
            <div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 12px; font-size: 13px; border: 1px solid {card_border}; margin-bottom: 15px;">
                <b>Conversion Rate:</b> 100 EcoCoins = Rs. 10.00 INR
            </div>
            """, unsafe_allow_html=True)
            
            # Prefill details if logged in
            default_phone = st.session_state.get("user_phone", "")
            default_name = st.session_state.get("user_name", "")
            
            conv_phone = st.text_input("Phone Number", value=default_phone, placeholder="e.g. 9876543210", key="tx_convert_phone")
            conv_name = st.text_input("Name", value=default_name, placeholder="e.g. Rupa Kundu", key="tx_convert_name")

            coins_input = st.number_input(
                "Coins to Convert",
                min_value=0,
                step=50,
                key="coins_conv_input"
            )
            
            cash_est = (coins_input / 10.0) if coins_input > 0 else 0.0
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; margin-bottom: 15px;">
                <span style="font-size: 14px; color: {text_sub};">Estimated cash value:</span>
                <span style="font-size: 22px; font-weight: 800; color: {accent}; font-family: Outfit;">Rs. {cash_est:.2f} INR</span>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Convert to Direct Cash", key="btn_convert"):
                phone_clean = conv_phone.strip()
                name_clean = conv_name.strip()
                
                if not phone_clean:
                    st.error("Phone number is required for conversion.")
                elif coins_input <= 0:
                    st.error("Please enter a valid amount of coins.")
                else:
                    # Validate coins_val
                    curr_user_coins = coins_val
                    if not st.session_state.api_online:
                        if phone_clean in st.session_state.sim_users:
                            curr_user_coins = st.session_state.sim_users[phone_clean]["coins"]
                        else:
                            curr_user_coins = 0
                            
                    if coins_input > curr_user_coins:
                        st.error(f"Insufficient coins. Available balance: {curr_user_coins} Coins")
                    else:
                        with st.spinner("Processing conversion..."):
                            success_tx = False
                            if st.session_state.api_online:
                                try:
                                    payload = {
                                        "phone": phone_clean,
                                        "name": name_clean,
                                        "convert_coins": coins_input
                                    }
                                    res = requests.post("http://localhost:5000/reward", json=payload, timeout=2.0)
                                    if res.status_code == 200:
                                        data = res.json()
                                        if data.get("success"):
                                            success_tx = True
                                            if data.get("name"):
                                                st.session_state.user_name = data.get("name")
                                except Exception:
                                    pass
                            
                            if not success_tx:
                                # Local Simulation Mode
                                if phone_clean in st.session_state.sim_users:
                                    st.session_state.sim_users[phone_clean]["coins"] -= coins_input
                                    st.session_state.user_name = st.session_state.sim_users[phone_clean]["name"]
                                    success_tx = True
                                else:
                                    st.error("User profile not found in simulation. Please deposit plastic first.")
                                    
                            if success_tx:
                                # Save session profile
                                st.session_state.user_phone = phone_clean
                                st.success(f"Transfer of Rs. {cash_est:.2f} to linked bank account was initiated successfully!")
                                time.sleep(1.0)
                                st.rerun()

    # Badges & Leaderboard Row
    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
    c_badges, c_leaderboard = st.columns(2)

    with c_badges:
        with st.container(border=True):
            st.markdown(f"""
            <h3 style="font-size: 20px; font-weight: 800; margin-bottom: 20px; display: flex; align-items: center; gap: 8px;">
                🏆 Earned Achievements
            </h3>
            """, unsafe_allow_html=True)
            
            for badge in BADGES:
                earned = weight_val >= badge["minWeight"]
                opacity_val = "1" if earned else "0.4"
                badge_color = badge['color']
                st.markdown(f"""
                <div class="glass-panel-html" style="padding: 15px; display: flex; align-items: center; gap: 15px; margin-bottom: 12px; background: rgba(255,255,255,0.015); opacity: {opacity_val};">
                    <span style="font-size: 28px; color: {badge_color};">🏅</span>
                    <div>
                        <h4 style="font-size: 14.5px; font-weight: 700; margin: 0; color: {text_main};">{badge['name']} { '✅' if earned else ''}</h4>
                        <p style="font-size: 11.5px; color: {text_sub}; margin: 2px 0 0 0;">{badge['desc']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with c_leaderboard:
        with st.container(border=True):
            st.markdown(f"""
            <h3 style="font-size: 20px; font-weight: 800; margin-bottom: 20px; display: flex; align-items: center; gap: 8px;">
                🏆 Top Community Leaders
            </h3>
            """, unsafe_allow_html=True)

            for idx, user in enumerate(leaderboard_data):
                is_you = "You" in user["name"]
                bg_color = "rgba(34, 197, 94, 0.1)" if is_you else "rgba(255,255,255,0.01)"
                border_col = accent if is_you else "transparent"
                num_color = "#fbbf24" if idx == 0 else "#cbd5e1" if idx == 1 else "#b45309" if idx == 2 else text_sub

                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 15px; border-radius: 12px; background: {bg_color}; border: 1px solid {border_col}; margin-bottom: 10px;">
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <span style="font-size: 14px; font-weight: 800; width: 20px; color: {num_color};">
                            #{idx + 1}
                        </span>
                        <span style="font-size: 14.5px; font-weight: 600;">{user['name']}</span>
                    </div>
                    <span style="font-size: 14.5px; font-weight: 800; color: {accent};">{user['coins']} Coins</span>
                </div>
                """, unsafe_allow_html=True)

    # Locate recycling centers
    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(f"""
        <h3 style="font-size: 18px; font-weight: 800; margin-bottom: 15px; text-align: center;">📍 Locate Nearest Recycling Centers</h3>
        <p style="color: {text_sub}; font-size: 13.5px; max-width: 600px; margin: 0 auto 20px; text-align: center;">
            Locate city waste sorting collection centers that buy plastic materials back to feed state industrial recycling chains.
        </p>
        <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
            <div class="glass-panel-html" style="padding: 15px; width: 220px; background: rgba(255,255,255,0.02); margin-bottom: 0; text-align: center;">
                <h4 style="font-size: 14.5px; font-weight: 700; margin: 0; color: {text_main};">Center Kolkata 1</h4>
                <p style="font-size: 11.5px; color: {text_sub}; margin-top: 4px; margin-bottom: 0;">Salt Lake Sector 5, Kolkata</p>
            </div>
            <div class="glass-panel-html" style="padding: 15px; width: 220px; background: rgba(255,255,255,0.02); margin-bottom: 0; text-align: center;">
                <h4 style="font-size: 14.5px; font-weight: 700; margin: 0; color: {text_main};">Center Kolkata 2</h4>
                <p style="font-size: 11.5px; color: {text_sub}; margin-top: 4px; margin-bottom: 0;">Ruby Crossing, EM Bypass, Kolkata</p>
            </div>
            <div class="glass-panel-html" style="padding: 15px; width: 220px; background: rgba(255,255,255,0.02); margin-bottom: 0; text-align: center;">
                <h4 style="font-size: 14.5px; font-weight: 700; margin: 0; color: {text_main};">Center Kolkata 3</h4>
                <p style="font-size: 11.5px; color: {text_sub}; margin-top: 4px; margin-bottom: 0;">Gariahat Main Road, Kolkata</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# PAGE 6: ABOUT TEAM
# =========================================================
def show_team():
    with st.container(border=True):
        st.markdown(f"""
        <div style="text-align: center; padding: 15px 0;">
            <h2 style="font-size: 2.5rem; font-weight: 800; margin-bottom: 10px;">
                👥 About the <span class="text-gradient">Project Team</span>
            </h2>
            <p style="color: {text_sub}; max-width: 600px; margin: 0 auto; font-size: 15px;">
                Meet the developers and researchers behind <b>EcoSort AI</b>, a smart waste sorting platform developed for national environmental competitions.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div style="margin-top: 40px; border-top: 1px dashed var(--card-border); padding-top: 20px;"></div>', unsafe_allow_html=True)
    st.markdown('<h3 style="font-size: 20px; font-weight: 800; margin-bottom: 25px; text-align: center;">👥 Project Developers & Researchers</h3>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]

    for idx, member in enumerate(TEAM_DATA):
        with cols[idx]:
            skills_html = ""
            for skill in member["skills"]:
                skills_html += f'<span style="font-size: 11px; background: rgba(255,255,255,0.03); border: 1px solid {card_border}; padding: 4px 10px; border-radius: 50px; font-weight: 500; color: {text_main}; margin-bottom: 5px; display: inline-block;">{skill}</span> '
            
            # DEVELOPER IMAGES CONFIGURATION
            # 1. To set or update developer images, save the file (PNG/JPG) in the 'frontend2/assets' folder.
            # 2. Map the corresponding file name below.
            # 3. For Soumita Das, replace 'soumita.png' below with the actual uploaded image name (e.g. 'soumita_das.jpg').
            image_filename = "WhatsApp Image 2026-05-31 at 5.28.10 PM.jpeg" if member["image_key"] == "rupa" else "WhatsApp Image 2026-05-31 at 5.31.38 PM.jpeg" if member["image_key"] == "debanjana" else "WhatsApp Image 2026-05-31 at 6.10.45 PM.jpeg"
            initials = "RK" if member["image_key"] == "rupa" else "DS" if member["image_key"] == "debanjana" else "SD"
            
            with st.container(border=True):
                c_av1, c_av2, c_av3 = st.columns([1, 1.5, 1])
                with c_av2:
                    avatar = get_circle_avatar(image_filename, initials)
                    st.image(avatar, use_container_width=True)
                
                st.markdown(f"""
                <div style="text-align: center; margin-top: 15px; display: flex; flex-direction: column; gap: 20px;">
                    <div>
                        <h3 style="font-size: 22px; font-weight: 800; margin: 0; color: {text_main};">{member['name']}</h3>
                    </div>
                    <div>
                        <span style="font-size: 11px; text-transform: uppercase; color: {text_sub}; font-weight: 700; letter-spacing: 1px; display: block; margin-bottom: 8px;">
                            Skills & Tech
                        </span>
                        <div style="display: flex; gap: 6px; flex-wrap: wrap; justify-content: center;">
                            {skills_html}
                        </div>
                    </div>
                    <div style="text-align: left; margin-top: 10px;">
                        <span style="font-size: 11px; text-transform: uppercase; color: {text_sub}; font-weight: 700; letter-spacing: 1px; display: block; margin-bottom: 8px; text-align: center;">
                            Key Contributions
                        </span>
                        <p style="font-size: 13.5px; color: {text_sub}; line-height: 1.6; margin: 0;">
                            {member['contributions']}
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Mentorship Card (Removed as requested)

# =========================================================
# PAGE 7: THANK YOU
# =========================================================
def show_thankyou():
    col_left, col_center, col_right = st.columns([1, 6, 1])
    with col_center:
        with st.container(border=True):
            render_html(f"""
            <div class="animate-float" style="padding: 40px 20px; position: relative; overflow: hidden; text-align: center; min-height: 60vh; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                
                <!-- Floating background blobs -->
                <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; opacity: 0.15; pointer-events: none;">
                    <div style="position: absolute; top: 10%; left: 10%; width: 150px; height: 150px; border-radius: 50%; background: {accent}; filter: blur(30px);"></div>
                    <div style="position: absolute; bottom: 10%; right: 10%; width: 150px; height: 150px; border-radius: 50%; background: #0ea5e9; filter: blur(30px);"></div>
                </div>

                <div style="position: relative; z-index: 2; width: 100%;">
                    <div style="display: flex; justify-content: center; margin-bottom: 25px;">
                        <div style="background: rgba(34, 197, 94, 0.1); border: 2px solid {accent}; padding: 20px; border-radius: 50%; width: 92px; height: 92px; display: flex; justify-content: center; align-items: center; margin: 0 auto;" class="pulse-glow">
                            <span style="font-size: 48px; line-height: 1;">🌱</span>
                        </div>
                    </div>

                    <h1 style="font-size: 3.5rem; font-weight: 800; line-height: 1.2; margin-bottom: 15px; color: {text_main};">
                        Thank <span class="text-gradient">You!</span>
                    </h1>
                    
                    <h2 style="font-size: 1.8rem; font-weight: 700; color: {accent}; margin-bottom: 30px;" class="text-glow-green">
                        "Together We Can Build A Plastic-Free Future"
                    </h2>

                    <p style="color: {text_sub}; font-size: 15px; line-height: 1.7; max-width: 600px; margin: 0 auto 40px;">
                        Thank you for exploring <b>EcoSort AI</b>. Circular economies begin with individual choices. By sorting and recycling your waste correctly, you keep microplastics out of our oceans and land.
                    </p>

                    <div style="border-top: 1px solid {card_border}; padding-top: 30px; text-align: center; margin-bottom: 35px;">
                        <span style="font-size: 12px; text-transform: uppercase; color: {text_sub}; font-weight: 700; letter-spacing: 1px; display: block; margin-bottom: 6px;">
                            Project Team
                        </span>
                        <span style="font-size: 16px; font-weight: 600; color: {text_main};">
                            Rupa Kundu, Debanjana Sarkar, Soumita Das
                        </span>
                    </div>

                    <div style="display: flex; justify-content: center; gap: 20px;">
                        <a href="#" class="glass-panel-html" style="padding: 12px; border-radius: 50%; color: {text_main}; display: flex; align-items: center; width: 44px; height: 44px; justify-content: center; text-decoration: none; margin-bottom: 0; background: {card_bg}; border: 1px solid {card_border}; box-shadow: {shadow}; transition: all 0.3s ease;">
                            <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="20" width="20" xmlns="http://www.w3.org/2000/svg">
                              <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"></path>
                              <path d="M9 18c-4.51 2-5-2-7-2"></path>
                            </svg>
                        </a>
                        <a href="#" class="glass-panel-html" style="padding: 12px; border-radius: 50%; color: {text_main}; display: flex; align-items: center; width: 44px; height: 44px; justify-content: center; text-decoration: none; margin-bottom: 0; background: {card_bg}; border: 1px solid {card_border}; box-shadow: {shadow}; transition: all 0.3s ease;">
                            <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="20" width="20" xmlns="http://www.w3.org/2000/svg">
                              <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                              <rect width="4" height="12" x="2" y="9"></rect>
                              <circle cx="4" cy="4" r="2"></circle>
                            </svg>
                        </a>
                        <a href="#" class="glass-panel-html" style="padding: 12px; border-radius: 50%; color: {text_main}; display: flex; align-items: center; width: 44px; height: 44px; justify-content: center; text-decoration: none; margin-bottom: 0; background: {card_bg}; border: 1px solid {card_border}; box-shadow: {shadow}; transition: all 0.3s ease;">
                            <svg stroke="currentColor" fill="none" stroke-width="2" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" height="20" width="20" xmlns="http://www.w3.org/2000/svg">
                              <rect width="20" height="16" x="2" y="4" rx="2"></rect>
                              <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
                            </svg>
                        </a>
                    </div>
                    
                    <p style="margin-top: 30px; font-size: 12px; color: {text_sub}; display: flex; align-items: center; gap: 4px; justify-content: center; margin-bottom: 0;">
                        Made with <span style="color: #ef4444;">❤️</span> in India
                    </p>
                </div>
            </div>
            """)
    trigger_confetti()

# =========================================================
# ROUTING CONTROLLER
# =========================================================
if st.session_state.page == "home":
    show_home()
elif st.session_state.page == "scanner":
    show_scanner()
elif st.session_state.page == "impact":
    show_impact()
elif st.session_state.page == "initiatives":
    show_initiatives()
elif st.session_state.page == "rewards":
    show_rewards()
elif st.session_state.page == "team":
    show_team()
elif st.session_state.page == "thankyou":
    show_thankyou()

# =========================================================
# SYSTEM WIDE FOOTER
# =========================================================
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 20px 0 10px 0; display: flex; flex-direction: column; gap: 10px; align-items: center;">
  <div style="display: flex; align-items: center; gap: 8px;">
    <span style="color: {accent}; font-size: 16px;">🌱</span>
    <span style="font-size: 15px; font-weight: 800;">EcoSort AI</span>
  </div>
  <!-- Developed for national level competition -->
  <p style="font-size: 11px; color: {text_sub}; margin: 0;">
    © {datetime.now().year} EcoSort AI Team (Rupa Kundu, Debanjana Sarkar, Soumita Das). All rights reserved.
  </p>
</div>
""", unsafe_allow_html=True)
