import streamlit as st
from openai import AsyncOpenAI
from config import AVAILABLE_MODELS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def sidebar():
    with st.sidebar:
        st.title("Configuration")

        # Available Tools
        st.subheader("Available Tools")
        if "tools" in st.session_state:
            with st.expander("Tool List", expanded=False):
                for tool_name, tool_details in st.session_state.tools.items():
                    st.markdown(f"- *{tool_name}*: {tool_details['schema']['function']['description']}")
        else:
            st.write("Tools loading... Please wait.")

        # Model Selection
        st.subheader("Model Selection")
        selected_model = st.selectbox("Select Model", AVAILABLE_MODELS)

        # Add Model Input
        new_model = st.text_input("Add New Model")
        if st.button("Add Model"):
            if new_model not in AVAILABLE_MODELS and new_model.strip():
                AVAILABLE_MODELS.append(new_model)
                st.experimental_rerun()

        # API Configuration
        st.subheader("API Configuration")
        api_endpoint = st.text_input("API Endpoint", os.getenv("API_ENDPOINT", "http://localhost:8000/v1"))
        api_key = st.text_input("API Key", os.getenv("API_KEY", "dummy-key"), type="password")

        # Database Configuration
        st.subheader("Database Configuration")
        st.session_state.db_host = st.text_input("DB Host", st.session_state.get('db_host', 'localhost'))
        st.session_state.db_port = st.number_input("DB Port", value=st.session_state.get('db_port', 5432), min_value=1, max_value=65535)
        st.session_state.db_name = st.text_input("DB Name", st.session_state.get('db_name', 'airpollution'))
        st.session_state.db_user = st.text_input("DB User", st.session_state.get('db_user', 'postgres'))
        st.session_state.db_password = st.text_input("DB Password", st.session_state.get('db_password', '123456'), type="password")

        # Initialize OpenAI client
        try:
            client = AsyncOpenAI(
                base_url=api_endpoint,
                api_key=api_key,
            )
        except Exception as e:
            st.error(f"Failed to initialize API client: {e}")
            client = None

    return client, selected_model
