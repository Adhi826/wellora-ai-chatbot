import streamlit as st
import requests
import uuid
import base64

# Configuration
API_URL = "https://wellora-ai-chatbot.onrender.com"

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Wellora", layout="centered", initial_sidebar_state="collapsed", page_icon="💊")

# ------------------ SESSION INITIALIZATION ------------------
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "language" not in st.session_state:
    st.session_state.language = "English"

# ------------------ CSS ------------------
st.markdown("""
<style>
/* Hide default Streamlit UI elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Background */
body {
    background: linear-gradient(135deg, #eef2ff, #f8fafc);
}

/* Center container */
.block-container {
    padding-top: 0rem;
}

/* Auth Pages Centering container */
.main-container {
    display: flex;
    justify-content: center;
    align-items: center;
    padding-top: 10vh;
}

/* Card layout matching ChatGPT-like style */
.card {
    background: white;
    padding: 40px;
    border-radius: 18px;
    box-shadow: 0px 8px 30px rgba(0,0,0,0.08);
    width: 380px;
    margin: auto;
    margin-top: 50px;
    transition: 0.3s;
}

.card:hover {
    transform: translateY(-5px);
}

/* Title */
.title {
    text-align: center;
    font-size: 32px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 5px;
}

/* Subtitle */
.subtitle {
    text-align: center;
    color: #6b7280;
    margin-bottom: 25px;
}

/* Input fields */
div[data-baseweb="input"] input {
    border-radius: 10px !important;
    padding: 10px !important;
}

/* Buttons */
div.stButton > button {
    width: 100%;
    height: 45px;
    border-radius: 10px;
    font-size: 16px;
    border: none;
    margin-top: 10px;
    transition: 0.3s;
}

/* Hover */
div.stButton > button:hover {
    transform: scale(1.02);
}

/* Dashboard input */
.chat-input input {
    border-radius: 20px !important;
}

/* Chat bubbles (ChatGPT style) */
.user {
    background: #2563eb;
    color: white;
    padding: 12px 18px;
    border-radius: 18px 18px 0px 18px;
    margin: 8px 0;
    text-align: right;
    width: fit-content;
    max-width: 80%;
    margin-left: auto;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    font-size: 15px;
}

.bot {
    background: #e5e7eb;
    color: #111827;
    padding: 12px 18px;
    border-radius: 18px 18px 18px 0px;
    margin: 8px 0;
    text-align: left;
    width: fit-content;
    max-width: 80%;
    margin-right: auto;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    font-size: 15px;
}
</style>
""", unsafe_allow_html=True)


# ------------------ LANDING ------------------
def landing_page():
    st.markdown('<div class="main-container"><div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="title">Wellora</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">AI Healthcare Assistant</div>', unsafe_allow_html=True)

    if st.button("🚀 Get Started", type="primary"):
        st.session_state.page = "signup"
        st.rerun()

    if st.button("🔐 Sign In"):
        st.session_state.page = "login"
        st.rerun()

    st.markdown('<br>', unsafe_allow_html=True)
    if st.button("Continue as Guest"):
        st.session_state.page = "dashboard"
        st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)


# ------------------ LOGIN ------------------
def login_page():
    st.markdown('<div class="main-container"><div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="title">Welcome Back</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Login to continue</div>', unsafe_allow_html=True)

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login", type="primary"):
        if not email or not password:
            st.error("Please fill in all fields.")
        else:
            try:
                res = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
                if res.status_code == 200:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
            except Exception:
                st.error("Error connecting to server. Make sure backend is live.")

    if st.button("Create new account"):
        st.session_state.page = "signup"
        st.rerun()

    if st.button("⬅ Back"):
        st.session_state.page = "landing"
        st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)


# ------------------ SIGNUP ------------------
def signup_page():
    st.markdown('<div class="main-container"><div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="title">Create Account</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Join Wellora</div>', unsafe_allow_html=True)

    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Sign Up", type="primary"):
        if not name or not email or not password:
            st.error("Please fill in all fields.")
        else:
            try:
                res = requests.post(f"{API_URL}/auth/signup", json={"email": email, "password": password})
                if res.status_code == 200:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("Account already exists or invalid data.")
            except Exception:
                st.error("Error connecting to server.")

    if st.button("Already have an account? Login"):
        st.session_state.page = "login"
        st.rerun()

    if st.button("⬅ Back"):
        st.session_state.page = "landing"
        st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)


# ------------------ DASHBOARD ------------------
def dashboard():
    # Helper to load history
    def load_session(s_id):
        try:
            res = requests.get(f"{API_URL}/history/{s_id}")
            if res.status_code == 200:
                history = res.json().get("history", [])
                st.session_state.messages = []
                for m in history:
                    st.session_state.messages.append({
                        "role": "assistant" if m["role"] == "assistant" else "user",
                        "text": m["content"]
                    })
        except:
            pass

    # Sidebar (History)
    with st.sidebar:
        st.title("Wellora AI")
        if st.session_state.logged_in:
            st.write(f"User: **{st.session_state.user_email.split('@')[0]}**")
        else:
            st.write("User: **Guest**")
            
        st.session_state.language = st.selectbox("Language", ["English", "Hindi", "Telugu"], index=["English", "Hindi", "Telugu"].index(st.session_state.language))
        
        st.markdown("### 💬 Chats")
        if st.button("➕ New Chat"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
            
        # Fetch actual chat history from backend if logged in
        if st.session_state.logged_in:
            try:
                res = requests.get(f"{API_URL}/sessions?user_email={st.session_state.user_email}")
                if res.status_code == 200:
                    sessions = res.json()
                    for idx, s in enumerate(sessions):
                        title = s.get("title", f"Chat {idx+1}")
                        if st.button(title, key=f"sess_{s['id']}"):
                            st.session_state.session_id = s['id']
                            load_session(s['id'])
                            st.rerun()
            except:
                pass
        
        st.markdown("---")
        if st.session_state.logged_in:
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.user_email = ""
                st.session_state.messages = []
                st.session_state.page = "landing"
                st.rerun()
        else:
            if st.button("Sign In / Sign Up"):
                st.session_state.page = "landing"
                st.rerun()

    # Chat area
    st.title("🩺 Wellora AI")
    st.caption("How can I help you today?")

    # Display chat history with bubbles
    for msg in st.session_state.messages:
        img_html = ""
        if msg.get("image"):
            img_html = f'<img src="{msg["image"]}" style="max-width:200px; border-radius:10px; margin-bottom:8px;"><br>'
        
        if msg["role"] == "user":
            st.markdown(f'<div class="user">{img_html}{msg["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot">{img_html}{msg["text"]}</div>', unsafe_allow_html=True)

    # Blank space so inputs don't cover the last message fully
    st.write("<br><br>", unsafe_allow_html=True)

    # Upload File 
    uploaded_img = st.file_uploader("Attach a medical image (Optional)", type=["png", "jpg", "jpeg", "webp"])
    img_data_uri = None
    if uploaded_img is not None:
        bytes_data = uploaded_img.getvalue()
        if len(bytes_data) > 3 * 1024 * 1024:
            st.warning("Image is too large (Max 3 MB).")
        else:
            b64 = base64.b64encode(bytes_data).decode()
            mime_type = uploaded_img.type
            img_data_uri = f"data:{mime_type};base64,{b64}"
            st.image(uploaded_img, width=120)

    # Chat Input
    if prompt := st.chat_input("Ask something..."):
        if not prompt.strip() and not img_data_uri:
            st.warning("Please enter a message or attach an image.")
        else:
            ui_text = prompt if prompt.strip() else "(image attached)"
            
            # Immediately add and display User Bubble
            st.session_state.messages.append({"role": "user", "text": prompt, "image": img_data_uri if img_data_uri else None})
            
            # Display visually before network call by rerendering quickly or manual write
            img_html = f'<img src="{img_data_uri}" style="max-width:200px; border-radius:10px; margin-bottom:8px;"><br>' if img_data_uri else ""
            st.markdown(f'<div class="user">{img_html}{prompt}</div>', unsafe_allow_html=True)

            with st.spinner("Analyzing..."):
                payload = {
                    "session_id": st.session_state.session_id,
                    "message": ui_text,
                    "is_logged_in": st.session_state.logged_in,
                    "user_email": st.session_state.user_email,
                    "language": st.session_state.language,
                    "image": img_data_uri
                }
                try:
                    response = requests.post(f"{API_URL}/chat", json=payload)
                    if response.status_code == 200:
                        data = response.json()
                        bot_text = data.get("response", "No response received.")
                        glm = data.get("glm_analysis")
                        
                        if glm and glm.get("status") == "success":
                            if glm.get("caption"):
                                bot_text = f"**🔬 Vision Analysis:** {glm.get('caption')}\n\n{bot_text}"
                        
                        st.session_state.messages.append({"role": "assistant", "text": bot_text})
                    else:
                        err_msg = response.json().get("detail", "Error")
                        st.session_state.messages.append({"role": "assistant", "text": f"Error: {err_msg}"})
                except Exception:
                    st.session_state.messages.append({"role": "assistant", "text": "Failed to connect to backend server."})
            
            st.rerun()

# ------------------ ROUTING LOGIC ------------------
if st.session_state.page == "landing":
    landing_page()
elif st.session_state.page == "login":
    login_page()
elif st.session_state.page == "signup":
    signup_page()
elif st.session_state.page == "dashboard":
    dashboard()
