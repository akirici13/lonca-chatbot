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
        if 'processing' not in st.session_state:
            st.session_state.processing = False
    
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
        """Render all chat messages in the conversation with modern messaging app style."""
        chat_container = st.container()
        with chat_container:
            # Create a scrollable container for messages
            for message in st.session_state.messages:
                # Create columns for message alignment
                col1, col2, col3 = st.columns([1, 4, 1])
                
                # Determine message alignment and styling
                if message["role"] == "user":
                    # User messages on the right
                    with col2:
                        st.markdown(f"""
                        <div style="
                            background-color: #007AFF;
                            color: white;
                            padding: 10px 15px;
                            border-radius: 15px;
                            margin: 5px 0;
                            max-width: 80%;
                            margin-left: auto;
                            text-align: left;
                        ">
                            {message["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                            
                        if "image" in message:
                            image = decode_base64_to_image(message["image"])
                            st.image(image, caption="", width=200, use_column_width=False)
                else:
                    # Assistant messages on the left
                    with col2:
                        st.markdown(f"""
                        <div style="
                            background-color: #E9ECEF;
                            color: black;
                            padding: 10px 15px;
                            border-radius: 15px;
                            margin: 5px 0;
                            max-width: 80%;
                            margin-right: auto;
                            text-align: left;
                        ">
                            {message["content"]}
                        </div>
                        """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    def _render_input_area(self):
        """Render the input area with text input and image upload side by side."""
        if st.session_state.region:
            # Create a container for the input area
            input_container = st.container()
            
            with input_container:
                # First row: Text input and send button
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    # Text input with unique key
                    user_input = st.text_input(
                        "Type your message",
                        key=f"user_input_{st.session_state.input_key}",
                        placeholder="Type your message here...",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    # Send button
                    send_button = st.button("Send", use_container_width=True)
                
                # Second row: Image uploader
                uploaded_file = st.file_uploader(
                    label="🔗",
                    type=["jpg", "jpeg", "png"],
                    label_visibility="collapsed",
                    key=f"file_uploader_{st.session_state.input_key}"
                )
            
            return user_input, send_button, uploaded_file
        return None, None, None
    
    def _process_input(self, user_input, send_button, uploaded_file):
        """Process user input and handle image upload."""
        if (send_button or user_input) and not st.session_state.processing:
            st.session_state.processing = True
            
            message_data = {"role": "user", "content": user_input if user_input else "I'm searching for a product similar to this image."}
            context = {
                "region": st.session_state.region
            }
            
            if uploaded_file is not None:
                try:
                    image = Image.open(uploaded_file)
                    base64_image = convert_image_to_base64(image)
                    message_data["image"] = base64_image
                    context["image_data"] = base64_image
                except Exception as e:
                    st.error(f"Error processing image: {e}")
                    st.session_state.processing = False
                    return
            
            st.session_state.messages.append(message_data)
            
            try:
                with st.spinner("Thinking..."):
                    response = asyncio.run(st.session_state.chat_handler.process_message(
                        message_data["content"],
                        context=context
                    ))
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["choices"][0]["message"]["content"]
                    })
                    
            except Exception as e:
                st.error(f"Error processing message: {e}")
            finally:
                st.session_state.processing = False
                st.session_state.input_key += 1
            
            st.rerun()
    
    def _add_custom_css(self):
        """Add custom CSS styles to the interface."""
        st.markdown("""
        <style>
            /* Main container styles */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            
            /* Input area styles */
            .stTextInput>div>div>input {
                border-radius: 20px;
                padding: 10px 15px;
                border: 1px solid #E0E0E0;
            }
            
            /* Button styles */
            .stButton>button {
                border-radius: 20px;
                height: 3em;
                background-color: #007AFF;
                color: white;
                border: none;
                font-weight: 500;
            }
            
            /* Chat container styles */
            .chat-container {
                padding: 20px;
                background-color: #F8F9FA;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            
            /* Hide Streamlit's default elements */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* Scrollbar styles */
            ::-webkit-scrollbar {
                width: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #555;
            }
        </style>
        """, unsafe_allow_html=True)
    
    def run(self):
        """Run the main GUI application."""
        st.title("Lonca Chatbot 💬")
        
        self._render_sidebar()
        
        # Create a container for the chat area
        chat_container = st.container()
        with chat_container:
            self._render_chat_messages()
        
        # Create a container for the input area
        input_container = st.container()
        if not st.session_state.region:
            st.info("Please select your region from the sidebar to start chatting.")
            return

        with input_container:
            user_input, send_button, uploaded_file = self._render_input_area()
            self._process_input(user_input, send_button, uploaded_file)
        
        self._add_custom_css() 