import streamlit as st
import asyncio
from PIL import Image
from helpers.image_utils import convert_image_to_base64, decode_base64_to_image
from services.chat_handler import ChatHandler
from services.message_service import MultiMessageBuffer
import time

class LoncaGUI:
    def __init__(self):
        """Initialize the GUI with required session state variables."""
        self._initialize_session_state()
        self._setup_page_config()
        # Add MultiMessageBuffer to session state if not present
        if 'multi_message_buffer' not in st.session_state:
            st.session_state.multi_message_buffer = MultiMessageBuffer(
                debounce_seconds=10,
                process_callback=self._process_combined_message
            )
        
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
        if 'message_buffer' not in st.session_state:
            st.session_state.message_buffer = []
        if 'last_input_time' not in st.session_state:
            st.session_state.last_input_time = None
        if 'debounce_seconds' not in st.session_state:
            st.session_state.debounce_seconds = 10
    
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
    
    async def _process_combined_message(self, combined_message, context):
        """Callback to process the combined message after debounce."""
        message_data = {"role": "user", "content": combined_message}
        if "image_data" in context:
            message_data["image"] = context["image_data"]
        st.session_state.messages.append(message_data)
        try:
            with st.spinner("Thinking..."):
                response = await st.session_state.chat_handler.process_message(
                    message_data["content"],
                    context=context
                )
                if response and "choices" in response and response["choices"]:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["choices"][0]["message"]["content"]
                    })
                    st.rerun()
                else:
                    st.error("Received invalid response format from chat handler")
        except Exception as e:
            st.error(f"Error processing message: {e}")
        finally:
            st.session_state.processing = False
            st.session_state.input_key += 1
    
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
        self._add_custom_css()
        self._render_sidebar()
        self._render_chat_messages()
        user_input, send_button, uploaded_file = self._render_input_area()
        now = time.time()
        processed_this_run = False
        # Debounce: process buffer if enough time has passed
        if st.session_state.last_input_time and now - st.session_state.last_input_time > st.session_state.debounce_seconds:
            if st.session_state.message_buffer:
                combined_message = "\n".join(st.session_state.message_buffer)
                base64_image = None
                if 'last_uploaded_image' in st.session_state:
                    base64_image = st.session_state.last_uploaded_image
                context = {"region": st.session_state.region}
                if base64_image:
                    context["image_data"] = base64_image
                # Process the combined message
                message_data = {"role": "user", "content": combined_message}
                if base64_image:
                    message_data["image"] = base64_image
                st.session_state.messages.append(message_data)
                try:
                    with st.spinner("Thinking..."):
                        response = asyncio.run(st.session_state.chat_handler.process_message(
                            message_data["content"],
                            context=context
                        ))
                        if response and "choices" in response and response["choices"]:
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response["choices"][0]["message"]["content"]
                            })
                            st.rerun()
                        else:
                            st.error("Received invalid response format from chat handler")
                except Exception as e:
                    st.error(f"Error processing message: {e}")
                finally:
                    st.session_state.processing = False
                st.session_state.message_buffer = []
                # Only clear last_input_time if buffer is empty
                if not st.session_state.message_buffer:
                    st.session_state.last_input_time = None
                st.session_state.last_uploaded_image = None
                processed_this_run = True

        # On user input, buffer and update last_input_time
        if st.session_state.region and (send_button or user_input):
            base64_image = None
            if uploaded_file is not None:
                try:
                    image = Image.open(uploaded_file)
                    base64_image = convert_image_to_base64(image)
                    st.session_state.last_uploaded_image = base64_image
                except Exception as e:
                    st.error(f"Error processing image: {e}")
                    return
            # Immediately show the user message in the chat
            message_data = {"role": "user", "content": user_input if user_input else "I'm searching for a product similar to this image."}
            if base64_image:
                message_data["image"] = base64_image
            st.session_state.messages.append(message_data)
            st.session_state.message_buffer.append(user_input if user_input else "I'm searching for a product similar to this image.")
            st.session_state.last_input_time = now
            st.session_state.input_key += 1 