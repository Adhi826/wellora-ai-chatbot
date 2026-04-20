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
body {
    background-color: #f5f7fb;
}

/* Center container */
.main-container {
    display: flex;
    justify-content: center;
    align-items: center;
    padding-top: 5vh;
}

/* Card */
.card {
    background: white;
    padding: 30px;
    border-radius: 15px;
    box-shadow: 0px 5px 20px rgba(0,0,0,0.1);
    width: 100%;
    max-width: 400px;
    margin: auto;
}

/* Title */
.title {
    text-align: center;
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 10px;
}

/* Subtitle */
.subtitle {
    text-align: center;
    color: gray;
    margin-bottom: 20px;
}

/* Button */
.stButton>button {
    width: 100%;
    border-radius: 10px;
    height: 45px;
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# ------------------ LANDING ------------------
def landing_page():
    st.markdown('<div class="main-container"><div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="title">Wellora</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Your AI Healthcare Assistant</div>', unsafe_allow_html=True)

    if st.button("Get Started", type="primary"):
        st.session_state.page = "signup"
        st.rerun()

    if st.button("Sign In"):
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
    st.markdown('<div class="title">Welcome back</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Sign in to Wellora</div>', unsafe_allow_html=True)

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Continue", type="primary"):
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

    if st.button("Don't have an account? Sign up"):
        st.session_state.page = "signup"
        st.rerun()

    if st.button("⬅ Back"):
        st.session_state.page = "landing"
        st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)


# ------------------ SIGNUP ------------------
def signup_page():
    st.markdown('<div class="main-container"><div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="title">Create account</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Get started for free</div>', unsafe_allow_html=True)

    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Create Account", type="primary"):
        if not name or not email or not password:
            st.error("Please fill in all fields.")
        elif password != confirm:
            st.error("Passwords do not match.")
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

    if st.button("Already have an account? Sign in"):
        st.session_state.page = "login"
        st.rerun()

    if st.button("⬅ Back"):
        st.session_state.page = "landing"
        st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)


# ------------------ DASHBOARD ------------------
def dashboard():
    with st.sidebar:
        if st.session_state.logged_in:
            st.write(f"Logged in as: **{st.session_state.user_email.split('@')[0]}**")
        else:
            st.write("Logged in as: **Guest**")
            
        st.session_state.language = st.selectbox("Language", ["English", "Hindi", "Telugu"], index=["English", "Hindi", "Telugu"].index(st.session_state.language))
        
        if st.button("New Chat Session"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
        
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

    st.title("🩺 Wellora AI")
    st.caption("How can I help you today? (Not a substitute for professional medical advice)")

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("image"):
                st.image(msg["image"], caption="Attached Image")
            st.markdown(msg["text"])

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
            st.image(uploaded_img, width=150)

    # Chat Input
    if prompt := st.chat_input("Message Wellora..."):
        if not prompt.strip() and not img_data_uri:
            st.warning("Please enter a message or attach an image.")
        else:
            ui_text = prompt if prompt.strip() else "(image attached)"
            st.session_state.messages.append({"role": "user", "text": prompt, "image": img_data_uri if img_data_uri else None})
            
            with st.chat_message("user"):
                if img_data_uri:
                    st.image(img_data_uri)
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Connecting to medical intelligence core..."):
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
                                st.info("🔬 Visually Analyzed by Wellora Vision Models")
                                if glm.get("caption"):
                                    st.markdown(f"**Visual Summary:** {glm.get('caption')}")
                            
                            st.markdown(bot_text)
                            st.session_state.messages.append({"role": "assistant", "text": bot_text})
                        else:
                            try:
                                err_msg = response.json().get("detail", "An error occurred")
                            except:
                                err_msg = response.text
                            st.error(err_msg)
                            st.session_state.messages.append({"role": "assistant", "text": f"Error: {err_msg}"})
                    except Exception:
                        err_msg = "Failed to connect to backend server."
                        st.error(err_msg)
                        st.session_state.messages.append({"role": "assistant", "text": err_msg})

# ------------------ ROUTING LOGIC ------------------
if st.session_state.page == "landing":
    landing_page()
elif st.session_state.page == "login":
    login_page()
elif st.session_state.page == "signup":
    signup_page()
elif st.session_state.page == "dashboard":
    dashboard()
