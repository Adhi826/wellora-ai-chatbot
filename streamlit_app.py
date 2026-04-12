import streamlit as st
import requests
import uuid
import base64

# Configuration
API_URL = "https://wellora-ai-chatbot.onrender.com"

st.set_page_config(page_title="Wellora AI", page_icon="💊")

# Initialize session state variables
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
    
# --- Sidebar Auth & Settings ---
with st.sidebar:
    st.title("Wellora AI")
    if not st.session_state.logged_in:
        auth_mode = st.radio("Account", ["Login", "Sign Up"])
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button(auth_mode):
            endpoint = "/auth/login" if auth_mode == "Login" else "/auth/signup"
            try:
                res = requests.post(f"{API_URL}{endpoint}", json={"email": email, "password": password})
                if res.status_code == 200:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.success(f"{auth_mode} successful!")
                    st.rerun()
                else:
                    st.error("Authentication failed. Check credentials/duplicate email.")
            except Exception as e:
                st.error("Error connecting to server. Make sure backend is awake.")
    else:
        st.write(f"Logged in as: **{st.session_state.user_email}**")
        st.session_state.language = st.selectbox("Language", ["English", "Hindi", "Telugu"], index=["English", "Hindi", "Telugu"].index(st.session_state.language))
        
        if st.button("New Chat Session"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
            
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.messages = []
            st.rerun()

# --- Main Chat Interface ---
st.header("How can I help you today?")
st.caption("Wellora can make mistakes. Not a substitute for professional medical advice.")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image"):
            st.image(msg["image"], caption="Attached Image")
        st.markdown(msg["text"])

# Upload File (Placing it discreetly below history)
uploaded_img = st.file_uploader("Attach a medical image (Optional)", type=["png", "jpg", "jpeg", "webp"])
img_data_uri = None
if uploaded_img is not None:
    bytes_data = uploaded_img.getvalue()
    # Check size < 3MB
    if len(bytes_data) > 3 * 1024 * 1024:
        st.warning("Image is too large (Max 3 MB). Please upload a smaller image.")
    else:
        b64 = base64.b64encode(bytes_data).decode()
        mime_type = uploaded_img.type
        img_data_uri = f"data:{mime_type};base64,{b64}"
        st.image(uploaded_img, width=150)

# Chat Input
if prompt := st.chat_input("Message Wellora..."):
    # Text must be non-empty if no image is attached
    if not prompt.strip() and not img_data_uri:
        st.warning("Please enter a message or attach an image.")
    else:
        ui_text = prompt if prompt.strip() else "(image attached)"
        
        # Add user message to UI
        st.session_state.messages.append({"role": "user", "text": prompt, "image": img_data_uri if img_data_uri else None})
        with st.chat_message("user"):
            if img_data_uri:
                st.image(img_data_uri)
            st.markdown(prompt)

        # Call Backend API
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
                        
                        # Show Vision feedback if any
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
                except Exception as e:
                    err_msg = "Failed to connect to the backend server. Make sure the API is live."
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "text": err_msg})
