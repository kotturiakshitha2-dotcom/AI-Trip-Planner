import streamlit as st
import requests
from planner import generate_trip_plan

from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as PDFImage
)
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch

from xml.sax.saxutils import escape

import re
import base64
from io import BytesIO


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Trip Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = (
    BASE_DIR
    / "assets"
    / "images"
)

BANGALORE_IMAGE = (
    ASSETS_DIR
    / "bangalore_iskcon.png"
)

PLANS_DIR = (
    BASE_DIR
    / "generated_plans"
)

PLANS_DIR.mkdir(
    exist_ok=True
)


# =========================================================
# INDIAN STATES + UNION TERRITORIES
# =========================================================

INDIAN_STATES_UTS = {

    # STATES

    "andhra pradesh": "Tirumala Tirupati Temple",
    "arunachal pradesh": "Tawang Monastery",
    "assam": "Kaziranga National Park",
    "bihar": "Mahabodhi Temple Bodh Gaya",
    "chhattisgarh": "Chitrakote Falls",

    "goa": "Baga Beach Goa",

    "gujarat": "Statue of Unity",
    "haryana": "Sultanpur National Park",
    "himachal pradesh": "Rohtang Pass Manali",
    "jharkhand": "Dassam Falls Ranchi",

    # KARNATAKA
    "karnataka": "ISKCON Temple Bangalore",

    "kerala": "Alleppey Backwaters",
    "madhya pradesh": "Khajuraho Temples",
    "maharashtra": "Gateway of India Mumbai",
    "manipur": "Loktak Lake",
    "meghalaya": "Living Root Bridges Meghalaya",
    "mizoram": "Aizawl Mizoram",
    "nagaland": "Dzukou Valley",
    "odisha": "Jagannath Temple Puri",
    "punjab": "Golden Temple Amritsar",
    "rajasthan": "Hawa Mahal Jaipur",
    "sikkim": "Tsomgo Lake Gangtok",
    "tamil nadu": "Meenakshi Amman Temple Madurai",
    "telangana": "Charminar Hyderabad",
    "tripura": "Ujjayanta Palace Agartala",
    "uttar pradesh": "Taj Mahal Agra",
    "uttarakhand": "Naini Lake Nainital",
    "west bengal": "Victoria Memorial Kolkata",

    # UNION TERRITORIES

    "andaman and nicobar islands":
        "Radhanagar Beach Andaman",

    "andaman":
        "Radhanagar Beach Andaman",

    "chandigarh":
        "Rock Garden Chandigarh",

    "dadra and nagar haveli and daman and diu":
        "Daman Beach",

    "daman":
        "Daman Beach",

    "delhi":
        "India Gate Delhi",

    "new delhi":
        "India Gate Delhi",

    "jammu and kashmir":
        "Dal Lake Srinagar",

    "kashmir":
        "Dal Lake Srinagar",

    "ladakh":
        "Pangong Lake Ladakh",

    "lakshadweep":
        "Bangaram Island Lakshadweep",

    "puducherry":
        "Promenade Beach Pondicherry",

    "pondicherry":
        "Promenade Beach Pondicherry"
}


# =========================================================
# POPULAR CITIES
# =========================================================

CITY_LANDMARKS = {

    "hyderabad": "Charminar Hyderabad",
    "secunderabad": "Hussain Sagar Hyderabad",

    # BANGALORE
    "bangalore": "ISKCON Temple Bangalore",
    "bengaluru": "ISKCON Temple Bangalore",
    "banglore": "ISKCON Temple Bangalore",

    "mumbai": "Gateway of India Mumbai",

    "delhi": "India Gate Delhi",
    "new delhi": "India Gate Delhi",

    "kolkata": "Victoria Memorial Kolkata",

    "chennai": "Marina Beach Chennai",

    "pune": "Shaniwar Wada Pune",

    "ahmedabad": "Sabarmati Ashram Ahmedabad",

    "surat": "Dumas Beach Surat",

    "visakhapatnam": "RK Beach Visakhapatnam",
    "vizag": "RK Beach Visakhapatnam",

    "vijayawada": "Prakasam Barrage Vijayawada",

    "tirupati": "Tirumala Tirupati Temple",

    "warangal": "Warangal Fort",

    "rajahmundry": "Godavari River Rajahmundry",

    "kakinada": "Kakinada Beach",

    "nellore": "Pulicat Lake Nellore",

    "coimbatore": "Marudamalai Temple",

    "madurai": "Meenakshi Amman Temple Madurai",

    "kochi": "Fort Kochi",

    "alleppey": "Alleppey Backwaters",

    "alappuzha": "Alleppey Backwaters",

    "munnar": "Munnar Tea Gardens",

    "mysore": "Mysore Palace",

    "mysuru": "Mysore Palace",

    "goa": "Baga Beach Goa",

    "panaji": "Dona Paula Goa",

    "jaipur": "Hawa Mahal Jaipur",

    "udaipur": "Lake Pichola Udaipur",

    "jodhpur": "Mehrangarh Fort Jodhpur",

    "jaisalmer": "Jaisalmer Fort",

    "agra": "Taj Mahal Agra",

    "varanasi": "Varanasi Ghats",

    "lucknow": "Bara Imambara Lucknow",

    "ayodhya": "Ram Mandir Ayodhya",

    "mathura": "Krishna Janmabhoomi Mathura",

    "vrindavan": "Banke Bihari Temple Vrindavan",

    "amritsar": "Golden Temple Amritsar",

    "manali": "Solang Valley Manali",

    "shimla": "Mall Road Shimla",

    "dharamshala": "McLeod Ganj Dharamshala",

    "rishikesh": "Rishikesh Ganga",

    "mussoorie": "Mall Road Mussoorie",

    "dehradun": "Robber's Cave Dehradun",

    "nainital": "Naini Lake Nainital",

    "srinagar": "Dal Lake Srinagar",

    "leh": "Pangong Lake Ladakh",

    "gangtok": "Tsomgo Lake Gangtok",

    "darjeeling": "Tiger Hill Darjeeling",

    "shillong": "Umiam Lake Shillong",

    "guwahati": "Kamakhya Temple Guwahati",

    "bhubaneswar": "Lingaraj Temple Bhubaneswar",

    "puri": "Jagannath Temple Puri",

    "ranchi": "Dassam Falls Ranchi",

    "bhopal": "Upper Lake Bhopal",

    "indore": "Rajwada Palace Indore",

    "nagpur": "Deekshabhoomi Nagpur",

    "nashik": "Godavari River Nashik",

    "aurangabad": "Ajanta Caves",

    "patna": "Golghar Patna",

    "bodh gaya": "Mahabodhi Temple Bodh Gaya",

    "raipur": "Nandan Van Raipur",

    "aizawl": "Aizawl Mizoram",

    "kohima": "Kisama Heritage Village",

    "imphal": "Loktak Lake",

    "agartala": "Ujjayanta Palace Agartala",

    "port blair": "Radhanagar Beach Andaman"
}


# =========================================================
# WORDS TO AVOID IN ONLINE IMAGES
# =========================================================

PEOPLE_WORDS = [
    "people",
    "person",
    "persons",
    "man",
    "men",
    "woman",
    "women",
    "boy",
    "girl",
    "child",
    "children",
    "crowd",
    "tourist",
    "tourists",
    "portrait",
    "selfie",
    "family",
    "human",
    "humans",
    "face",
    "faces",
    "photographer",
    "pilgrim",
    "pilgrims"
]


# =========================================================
# SCENIC WORDS
# =========================================================

SCENIC_WORDS = [
    "landmark",
    "monument",
    "palace",
    "fort",
    "temple",
    "lake",
    "waterfall",
    "beach",
    "mountain",
    "valley",
    "garden",
    "architecture",
    "landscape",
    "scenery",
    "heritage"
]


# =========================================================
# LOAD LOCAL BANGALORE IMAGE
# =========================================================

@st.cache_data(show_spinner=False)
def load_bangalore_background():

    if not BANGALORE_IMAGE.exists():
        return None

    try:

        with open(
            BANGALORE_IMAGE,
            "rb"
        ) as image_file:

            image_bytes = (
                image_file.read()
            )

        encoded_image = (
            base64.b64encode(
                image_bytes
            ).decode("utf-8")
        )

        return (
            "data:image/png;base64,"
            + encoded_image
        )

    except Exception as error:

        print(
            "Bangalore image loading error:",
            error
        )

        return None


# =========================================================
# WIKIMEDIA IMAGE SEARCH
# =========================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False
)
def search_wikimedia_images(
    search_text,
    width=1600,
    limit=20
):

    api_url = (
        "https://commons.wikimedia.org/w/api.php"
    )

    headers = {
        "User-Agent":
            "AITripPlanner/1.0 "
            "(educational travel planner project)"
    }

    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": search_text,
        "gsrnamespace": 6,
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": width
    }

    try:

        response = requests.get(
            api_url,
            params=params,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        pages = (
            data
            .get("query", {})
            .get("pages", {})
        )

        results = []

        for page in pages.values():

            title = page.get(
                "title",
                ""
            )

            image_info = page.get(
                "imageinfo",
                []
            )

            if not image_info:
                continue

            info = image_info[0]

            image_url = info.get(
                "thumburl"
            )

            if not image_url:

                image_url = info.get(
                    "url"
                )

            if not image_url:
                continue

            metadata = info.get(
                "extmetadata",
                {}
            )

            description = (
                metadata
                .get(
                    "ImageDescription",
                    {}
                )
                .get(
                    "value",
                    ""
                )
            )

            combined_text = (
                f"{title} {description}"
            ).lower()

            results.append({
                "url": image_url,
                "title": title,
                "description": description,
                "text": combined_text
            })

        return results

    except Exception as error:

        print(
            f"Wikimedia search error: {error}"
        )

        return []


# =========================================================
# CHOOSE IMAGE
# =========================================================

def choose_no_human_image(
    candidates
):

    if not candidates:
        return None

    clean_candidates = []

    for item in candidates:

        text = item["text"]

        has_people_word = any(
            word in text
            for word in PEOPLE_WORDS
        )

        if not has_people_word:

            clean_candidates.append(
                item
            )

    if clean_candidates:

        candidates = clean_candidates

    best_candidate = None
    best_score = -1

    for item in candidates:

        text = item["text"]

        score = 0

        for word in SCENIC_WORDS:

            if word in text:
                score += 2

        if "landmark" in text:
            score += 3

        if "landscape" in text:
            score += 3

        if "scenery" in text:
            score += 3

        if "architecture" in text:
            score += 2

        if score > best_score:

            best_score = score
            best_candidate = item

    if best_candidate:

        return best_candidate["url"]

    return candidates[0]["url"]


# =========================================================
# GET DESTINATION LANDMARK
# =========================================================

def get_destination_landmark(
    destination
):

    name = (
        destination
        .strip()
        .lower()
    )

    # SPECIAL BANGALORE RULE

    if name in [
        "bangalore",
        "bengaluru",
        "banglore"
    ]:

        return "ISKCON Temple Bangalore"

    if name in CITY_LANDMARKS:

        return CITY_LANDMARKS[name]

    if name in INDIAN_STATES_UTS:

        return INDIAN_STATES_UTS[name]

    for city, landmark in CITY_LANDMARKS.items():

        if (
            city in name
            or name in city
        ):

            return landmark

    for state, landmark in INDIAN_STATES_UTS.items():

        if (
            state in name
            or name in state
        ):

            return landmark

    return (
        f"{destination} India "
        f"famous landmark"
    )


# =========================================================
# GET BACKGROUND IMAGE
# =========================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False
)
def get_background_image(
    destination
):

    name = (
        destination
        .strip()
        .lower()
    )

    # =====================================================
    # BANGALORE
    #
    # USE THE EXACT PHOTO PROVIDED BY THE USER
    # =====================================================

    if name in [
        "bangalore",
        "bengaluru",
        "banglore"
    ]:

        local_image = (
            load_bangalore_background()
        )

        if local_image:

            return local_image

        return None

    # =====================================================
    # OTHER DESTINATIONS
    # =====================================================

    landmark = (
        get_destination_landmark(
            destination
        )
    )

    queries = [

        f"{landmark}",

        f"{landmark} India",

        f"{destination} India famous landmark",

        f"{destination} India tourist place",

        f"{destination} India scenery"
    ]

    for query in queries:

        candidates = (
            search_wikimedia_images(
                query,
                width=1800,
                limit=30
            )
        )

        if not candidates:
            continue

        image = (
            choose_no_human_image(
                candidates
            )
        )

        if image:

            return image

    return None


# =========================================================
# GET PLACE IMAGE
# =========================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False
)
def get_place_image(
    place,
    destination
):

    queries = [

        f"{place} {destination} India",

        f"{place} {destination} landmark",

        f"{place} {destination} scenic"
    ]

    for query in queries:

        candidates = (
            search_wikimedia_images(
                query,
                width=1000,
                limit=20
            )
        )

        image = (
            choose_no_human_image(
                candidates
            )
        )

        if image:

            return image

    return None


# =========================================================
# DOWNLOAD IMAGE FOR PDF
# =========================================================

def download_image_for_pdf(
    image_url
):

    try:

        response = requests.get(
            image_url,
            headers={
                "User-Agent":
                    "AITripPlanner/1.0"
            },
            timeout=20
        )

        response.raise_for_status()

        return BytesIO(
            response.content
        )

    except Exception as error:

        print(
            f"PDF image download error: {error}"
        )

        return None


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
<style>

.stApp {
    background-color: #ffffff;
}

[data-testid="stAppViewContainer"] {
    background: transparent !important;
}

.block-container {
    max-width: 1150px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.stApp h1 {
    color: #173b27 !important;
    font-weight: 800 !important;
}

.stApp h2 {
    color: #1d5738 !important;
}

.stApp h3 {
    color: #1d5738 !important;
}

.stMarkdown p {
    color: #17251d;
}

label {
    color: #173b27 !important;
    font-weight: 700 !important;
}

.stTextInput input,
.stNumberInput input {
    background-color: rgba(255,255,255,0.97) !important;
    color: #17251d !important;
    -webkit-text-fill-color: #17251d !important;
}

.stTextInput > div > div,
.stNumberInput > div > div {
    background-color: rgba(255,255,255,0.97) !important;
    border-radius: 12px !important;
}

.stSelectbox [data-baseweb="select"] {
    background-color: rgba(255,255,255,0.97) !important;
    border-radius: 12px !important;
}

.stSelectbox [data-baseweb="select"] * {
    color: #17251d !important;
}

.stButton > button {
    background-color: #26734d !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    padding: 13px !important;
    box-shadow: 0 5px 15px rgba(0,0,0,0.16);
}

.stButton > button p {
    color: white !important;
}

.stButton > button:hover {
    background-color: #185b3a !important;
}

[data-testid="stAlert"] {
    background-color: rgba(255,255,255,0.94) !important;
    border-radius: 14px !important;
}

[data-testid="stAlert"] p {
    color: #174d32 !important;
}

.place-card {
    background-color: rgba(255,255,255,0.96);
    border-radius: 18px;
    padding: 10px;
    border: 1px solid #d0ddd5;
    box-shadow: 0 5px 18px rgba(0,0,0,0.12);
}

.place-name {
    color: #123c27 !important;
    text-align: center;
    font-size: 16px;
    font-weight: 800;
}

[data-testid="stImage"] {
    border-radius: 15px;
    overflow: hidden;
}

.metric-box {
    background-color: rgba(255,255,255,0.96);
    border-radius: 18px;
    padding: 18px;
    text-align: center;
    border: 1px solid #d0ddd5;
    box-shadow: 0 5px 18px rgba(0,0,0,0.12);
}

.metric-title {
    color: #52645a !important;
    font-size: 13px;
}

.metric-value {
    color: #123c27 !important;
    font-size: 19px;
    font-weight: 800;
}

.plan-box {
    background-color: rgba(255,255,255,0.96);
    border-radius: 20px;
    padding: 25px;
    border: 1px solid #d0ddd5;
    box-shadow: 0 6px 20px rgba(0,0,0,0.12);
}

.stDownloadButton > button {
    background-color: white !important;
    color: #174d32 !important;
    border: 1px solid #aebfb4 !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
}

.stDownloadButton > button p {
    color: #174d32 !important;
}

hr {
    border-top: 1px solid #b9c8be !important;
}

.stCaption {
    color: #52645a !important;
}

</style>
""",
    unsafe_allow_html=True
)


# =========================================================
# TITLE
# =========================================================

st.title(
    "✈️ AI Trip Planner"
)

st.subheader(
    "Plan • Explore • Discover • Travel"
)

st.write(
    "Your personal AI travel assistant powered by Ollama + Llama 3.2."
)

st.divider()


# =========================================================
# INPUT SECTION
# =========================================================

st.markdown(
    "## 🌍 Tell us about your trip"
)

col1, col2 = st.columns(2)


with col1:

    destination = st.text_input(
        "📍 Destination",
        placeholder=(
            "Example: Bangalore, Goa, Hyderabad, "
            "Kerala, Jaipur..."
        )
    )

    days = st.number_input(
        "📅 Number of Days",
        min_value=1,
        max_value=30,
        value=3
    )

    travelers = st.number_input(
        "👥 Number of Travelers",
        min_value=1,
        max_value=20,
        value=2
    )


with col2:

    budget = st.number_input(
        "💰 Total Budget (₹)",
        min_value=1000,
        value=20000,
        step=1000
    )

    travel_style = st.selectbox(
        "🎒 Travel Style",
        [
            "Budget",
            "Standard",
            "Luxury"
        ]
    )

    st.info(
        "💡 Enter any Indian state, "
        "UT or city. The app will find "
        "a famous destination picture automatically."
    )


# =========================================================
# DESTINATION BACKGROUND
# =========================================================

if destination.strip():

    with st.spinner(
        "🌄 Loading your destination picture..."
    ):

        background_image = (
            get_background_image(
                destination.strip()
            )
        )

    if background_image:

        st.markdown(
            f"""
            <style>

            .stApp {{

                background-image:
                    linear-gradient(
                        rgba(255,255,255,0.72),
                        rgba(255,255,255,0.72)
                    ),
                    url("{background_image}");

                background-size:
                    cover;

                background-position:
                    center;

                background-attachment:
                    fixed;

                background-repeat:
                    no-repeat;

            }}

            [data-testid="stAppViewContainer"] {{

                background:
                    transparent !important;

            }}

            </style>
            """,
            unsafe_allow_html=True
        )

    else:

        st.warning(
            "🌿 Background picture could not be loaded. "
            "For Bangalore, make sure "
            "'assets/images/bangalore_iskcon.png' "
            "exists."
        )


st.write("")


# =========================================================
# GENERATE BUTTON
# =========================================================

generate = st.button(
    "✨ Generate My Dream Trip",
    use_container_width=True
)


# =========================================================
# EXTRACT PLACES FROM AI RESPONSE
# =========================================================

def extract_places(text):

    places = []

    lines = text.split("\n")

    inside_places = False

    for line in lines:

        clean_line = line.strip()

        if not clean_line:
            continue

        upper_line = clean_line.upper()

        if upper_line.startswith(
            "PLACES"
        ):

            inside_places = True

            continue

        if (
            inside_places
            and any(
                upper_line.startswith(section)
                for section in [
                    "BUDGET",
                    "ITINERARY",
                    "TIPS",
                    "TRIP OVERVIEW"
                ]
            )
        ):

            break

        if inside_places:

            place = re.sub(
                r"^[\-\*\d\.\)\s]+",
                "",
                clean_line
            ).strip()

            if " - " in place:

                place = place.split(
                    " - "
                )[0].strip()

            if ":" in place:

                place = place.split(
                    ":"
                )[0].strip()

            if (
                len(place) > 2
                and len(place) < 100
            ):

                duplicate = any(
                    place.lower()
                    == existing.lower()
                    for existing in places
                )

                if not duplicate:

                    places.append(
                        place
                    )

        if len(places) >= 5:

            break

    return places[:5]


# =========================================================
# CREATE PDF
# =========================================================

def create_pdf(
    text,
    pdf_path,
    place_images,
    destination
):

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#245c3c"),
        spaceAfter=15
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=15,
        leading=20,
        textColor=colors.HexColor("#245c3c"),
        spaceBefore=10,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#333333"),
        spaceAfter=6
    )

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    story = []

    story.append(
        Paragraph(
            "AI Trip Planner",
            title_style
        )
    )

    story.append(
        Paragraph(
            f"Trip to {escape(destination)}",
            heading_style
        )
    )

    story.append(
        Spacer(1, 10)
    )

    if place_images:

        story.append(
            Paragraph(
                "Places to Visit",
                heading_style
            )
        )

        for place, image_data in place_images:

            story.append(
                Paragraph(
                    f"📍 {escape(place)}",
                    heading_style
                )
            )

            if image_data:

                try:

                    image_data.seek(0)

                    image = PDFImage(
                        image_data
                    )

                    max_width = (
                        6.4 * inch
                    )

                    max_height = (
                        3.5 * inch
                    )

                    image_width = (
                        image.imageWidth
                    )

                    image_height = (
                        image.imageHeight
                    )

                    scale = min(
                        max_width /
                        image_width,
                        max_height /
                        image_height
                    )

                    image.drawWidth = (
                        image_width * scale
                    )

                    image.drawHeight = (
                        image_height * scale
                    )

                    story.append(
                        image
                    )

                    story.append(
                        Spacer(1, 10)
                    )

                except Exception as error:

                    print(
                        f"PDF image error: {error}"
                    )

    story.append(
        Paragraph(
            "Your AI Itinerary",
            heading_style
        )
    )

    for line in text.split("\n"):

        line = line.strip()

        if not line:
            continue

        upper_line = line.upper()

        if upper_line in [
            "TRIP OVERVIEW",
            "PLACES",
            "BUDGET",
            "ITINERARY",
            "TIPS"
        ]:

            story.append(
                Paragraph(
                    escape(line),
                    heading_style
                )
            )

        else:

            story.append(
                Paragraph(
                    escape(line),
                    body_style
                )
            )

    document.build(
        story
    )


# =========================================================
# GENERATE TRIP
# =========================================================

if generate:

    if not destination.strip():

        st.warning(
            "📍 Please enter a destination first."
        )

    else:

        prompt = f"""
Create a practical {days}-day travel itinerary for {destination}.

Travelers: {travelers}
Budget: ₹{budget}
Style: {travel_style}

Return ONLY these sections:

TRIP OVERVIEW
- Destination
- Days
- Travelers
- Travel style

PLACES
Give exactly 5 famous and useful places to visit in {destination}.
Write ONLY the place name on each line.
Do not add descriptions.
Do not number the places.

BUDGET
- Hotel
- Food
- Transport
- Activities
- Miscellaneous
- Total

ITINERARY

For each day:

Morning:
Afternoon:
Evening:

TIPS
- 5 useful travel tips

Keep everything practical,
short and easy to understand.
"""

        with st.spinner(
            "🤖 Creating your personalized trip..."
        ):

            try:

                result = generate_trip_plan(
                    prompt
                )

                places = extract_places(
                    result
                )

                timestamp = (
                    datetime.now()
                    .strftime(
                        "%Y%m%d_%H%M%S"
                    )
                )

                safe_destination = re.sub(
                    r"[^a-zA-Z0-9_-]",
                    "_",
                    destination
                )

                txt_filename = (
                    f"{safe_destination}_"
                    f"{timestamp}.txt"
                )

                pdf_filename = (
                    f"{safe_destination}_"
                    f"{timestamp}.pdf"
                )

                txt_path = (
                    PLANS_DIR
                    / txt_filename
                )

                pdf_path = (
                    PLANS_DIR
                    / pdf_filename
                )

                # =================================================
                # SAVE TXT
                # =================================================

                with open(
                    txt_path,
                    "w",
                    encoding="utf-8"
                ) as file:

                    file.write(
                        result
                    )

                # =================================================
                # FAMOUS PLACES
                # =================================================

                st.markdown(
                    "## 📸 Famous Places to Visit"
                )

                place_images = []

                if places:

                    image_columns = (
                        st.columns(
                            len(places)
                        )
                    )

                    for index, place in enumerate(
                        places
                    ):

                        with image_columns[index]:

                            st.markdown(
                                f"""
                                <div class="place-card">
                                    <div class="place-name">
                                        📍 {escape(place)}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            with st.spinner(
                                "Finding photo..."
                            ):

                                image_url = (
                                    get_place_image(
                                        place,
                                        destination
                                    )
                                )

                            if image_url:

                                st.image(
                                    image_url,
                                    use_container_width=True
                                )

                                image_data = (
                                    download_image_for_pdf(
                                        image_url
                                    )
                                )

                                place_images.append(
                                    (
                                        place,
                                        image_data
                                    )
                                )

                            else:

                                st.info(
                                    "Photo unavailable"
                                )

                                place_images.append(
                                    (
                                        place,
                                        None
                                    )
                                )

                else:

                    st.info(
                        "No clear place names "
                        "were returned by the AI."
                    )

                st.divider()

                # =================================================
                # CREATE PDF
                # =================================================

                create_pdf(
                    result,
                    pdf_path,
                    place_images,
                    destination
                )

                # =================================================
                # TRIP SUMMARY
                # =================================================

                st.markdown(
                    "## 🧳 Your Trip"
                )

                metric1, metric2, metric3, metric4 = (
                    st.columns(4)
                )

                with metric1:

                    st.markdown(
                        f"""
                        <div class="metric-box">

                            <div class="metric-title">
                                📍 Destination
                            </div>

                            <div class="metric-value">
                                {escape(destination)}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with metric2:

                    st.markdown(
                        f"""
                        <div class="metric-box">

                            <div class="metric-title">
                                📅 Days
                            </div>

                            <div class="metric-value">
                                {days}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with metric3:

                    st.markdown(
                        f"""
                        <div class="metric-box">

                            <div class="metric-title">
                                👥 Travelers
                            </div>

                            <div class="metric-value">
                                {travelers}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                with metric4:

                    st.markdown(
                        f"""
                        <div class="metric-box">

                            <div class="metric-title">
                                💰 Budget
                            </div>

                            <div class="metric-value">
                                ₹{budget:,}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                st.write("")

                # =================================================
                # AI ITINERARY
                # =================================================

                st.markdown(
                    "## 🗺️ Your AI Itinerary"
                )

                st.markdown(
                    '<div class="plan-box">',
                    unsafe_allow_html=True
                )

                st.markdown(
                    result
                )

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True
                )

                st.write("")

                # =================================================
                # DOWNLOAD SECTION
                # =================================================

                st.markdown(
                    "## 💾 Save Your Trip"
                )

                download1, download2 = (
                    st.columns(2)
                )

                with download1:

                    st.download_button(
                        label="📥 Download Trip TXT",
                        data=result,
                        file_name=txt_filename,
                        mime="text/plain",
                        use_container_width=True
                    )

                with download2:

                    with open(
                        pdf_path,
                        "rb"
                    ) as pdf_file:

                        pdf_data = (
                            pdf_file.read()
                        )

                    st.download_button(
                        label="📄 Download Trip PDF",
                        data=pdf_data,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        use_container_width=True
                    )

                st.success(
                    "✅ Your trip and PDF "
                    "have been created successfully!"
                )

                st.info(
                    f"📁 Files saved in: "
                    f"{PLANS_DIR}"
                )

            except Exception as error:

                st.error(
                    f"❌ Something went wrong: "
                    f"{error}"
                )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "✈️ AI Trip Planner • "
    "Plan • Explore • Discover • Travel • "
    "Powered by Ollama + Llama 3.2"
)