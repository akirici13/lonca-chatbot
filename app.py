import streamlit as st
import asyncio
from services.chat_handler import ChatHandler
from PIL import Image
from helpers.image_utils import convert_image_to_base64, decode_base64_to_image

# Initialize session state for messages and region
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'region' not in st.session_state:
    st.session_state.region = None
if 'chat_handler' not in st.session_state:
    st.session_state.chat_handler = ChatHandler()
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# Page config
st.set_page_config(
    page_title="Lonca Chatbot",
    page_icon="💬",
    layout="wide"
)

# Sidebar for region selection
with st.sidebar:
    st.title("Settings")
    if not st.session_state.region:
        region = st.selectbox(
            "Select your region",
            ["Europe", "Turkey", "Other", "Own"],
            index=None,
            placeholder="Choose your region..."
        )
        if region:
            st.session_state.region = region
            st.success(f"Region set to: {region}")
    else:
        st.info(f"Current region: {st.session_state.region}")
        if st.button("Change Region"):
            st.session_state.region = None
            st.rerun()

# Main chat interface
st.title("Lonca Chatbot 💬")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image" in message:
            # Display image from base64 string
            image = decode_base64_to_image(message["image"])
            st.image(image, caption="Uploaded Image")
        st.write(message["content"])

# Input area
if st.session_state.region:
    # Create a container for the input area
    input_container = st.container()
    
    with input_container:
        # Create two columns for text input and send button
        col1, col2 = st.columns([6, 1])
        
        with col1:
            # Text input with unique key
            user_input = st.text_input(
                "Type your message",
                key=f"user_input_{st.session_state.input_key}",
                placeholder="Type your message here..."
            )
        
        with col2:
            # Send button
            send_button = st.button("Send", use_container_width=True)
    
    # Image upload
    uploaded_file = st.file_uploader("Upload an image (optional)", type=["jpg", "jpeg", "png"])
    
    # Process input when send button is clicked or Enter is pressed
    if (send_button or user_input) and user_input:
        # Add user message to chat
        message_data = {"role": "user", "content": user_input}
        if uploaded_file:
            # Convert uploaded file to image and then to base64
            image = Image.open(uploaded_file)
            message_data["image"] = convert_image_to_base64(image)
        st.session_state.messages.append(message_data)
        
        # Get AI response
        with st.spinner("Thinking..."):
            response = asyncio.run(st.session_state.chat_handler.process_message(
                user_input,
                context={"region": st.session_state.region}
            ))
            
            # Add assistant response to chat
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["choices"][0]["message"]["content"]
            })
        
        # Increment input key to clear the input
        st.session_state.input_key += 1
        st.rerun()
else:
    st.info("Please select your region from the sidebar to start chatting.")

# Add some custom CSS
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .stChatMessage[data-testid="stChatMessage"] {
        background-color: #f0f2f6;
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #e6f3ff;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
    }
    .stTextInput>div>div>input {
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True) 