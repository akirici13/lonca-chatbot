import streamlit as st
import asyncio
from PIL import Image
from helpers.image_utils import convert_image_to_base64, decode_base64_to_image
from services.chat_handler import ChatHandler

class LoncaGUI:
    def __init__(self):
        """Initialize the GUI with required session state variables."""
        self._initialize_session_state()
        self._setup_page_config()
        
    def _initialize_session_state(self):
        """Initialize all required session state variables."""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'region' not in st.session_state:
            st.session_state.region = None
        if 'chat_handler' not in st.session_state:
            st.session_state.chat_handler = ChatHandler()
        if 'input_key' not in st.session_state:
            st.session_state.input_key = 0
    
    def _setup_page_config(self):
        """Configure the Streamlit page settings."""
        st.set_page_config(
            page_title="Lonca Chatbot",
            page_icon="💬",
            layout="wide"
        )
    
    def _render_sidebar(self):
        """Render the sidebar with region selection."""
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
    
    def _render_chat_messages(self):
        """Render all chat messages in the conversation."""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if "image" in message:
                    image = decode_base64_to_image(message["image"])
                    st.image(image, caption="Uploaded Image")
                st.write(message["content"])
    
    def _render_input_area(self):
        """Render the input area with text input and image upload."""
        if st.session_state.region:
            input_container = st.container()
            
            with input_container:
                col1, col2 = st.columns([6, 1])
                
                with col1:
                    user_input = st.text_input(
                        "Type your message",
                        key=f"user_input_{st.session_state.input_key}",
                        placeholder="Type your message here..."
                    )
                
                with col2:
                    send_button = st.button("Send", use_container_width=True)
            
            uploaded_file = st.file_uploader("Upload an image (optional)", type=["jpg", "jpeg", "png"])
            
            return user_input, send_button, uploaded_file
        return None, None, None
    
    def _process_input(self, user_input, send_button, uploaded_file):
        """Process user input and handle image upload."""
        if send_button or user_input:
            message_data = {"role": "user", "content": user_input if user_input else "I'm searching for a product similar to this image."}
            context = {"region": st.session_state.region}
            
            if uploaded_file is not None:
                try:
                    image = Image.open(uploaded_file)
                    base64_image = convert_image_to_base64(image)
                    message_data["image"] = base64_image
                    context["image_data"] = base64_image
                    print("Image processed and added to context")
                except Exception as e:
                    print(f"Error processing image: {e}")
                    st.error(f"Error processing image: {e}")
            
            st.session_state.messages.append(message_data)
            
            with st.spinner("Thinking..."):
                try:
                    response = asyncio.run(st.session_state.chat_handler.process_message(
                        message_data["content"],
                        context=context
                    ))
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["choices"][0]["message"]["content"]
                    })
                except Exception as e:
                    print(f"Error processing message: {e}")
                    st.error(f"Error processing message: {e}")
            
            st.session_state.input_key += 1
            st.rerun()
    
    def _add_custom_css(self):
        """Add custom CSS styles to the interface."""
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
    
    def run(self):
        """Run the main GUI application."""
        st.title("Lonca Chatbot 💬")
        
        self._render_sidebar()
        self._render_chat_messages()
        
        user_input, send_button, uploaded_file = self._render_input_area()
        if user_input is not None:
            self._process_input(user_input, send_button, uploaded_file)
        else:
            st.info("Please select your region from the sidebar to start chatting.")
        
        self._add_custom_css() 