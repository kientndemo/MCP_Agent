import streamlit as st
import json
import logging
import pandas as pd
from datetime import datetime
import os
from utils.agent import agent_loop, generate_sql_for_prompt
from utils.sql_tool import sql_query_handler
import openai

logger = logging.getLogger(__name__)

# Configure basic logging if not already configured elsewhere
# logging.basicConfig(level=logging.INFO) # Uncomment if needed

# Define the Excel log file path
LOG_FILE = "conversation_log.xlsx"

def log_conversation_to_excel(timestamp, user_question, bot_answer, model_name):
    """Appends a conversation entry to an Excel file."""
    new_log = pd.DataFrame({
        "Time": [timestamp.strftime("%Y-%m-%d %H:%M:%S")],
        "User Question": [user_question],
        "Answer from Chatbot": [bot_answer],
        "Model LLM for Chatbot": [model_name]
    })

    if os.path.exists(LOG_FILE):
        try:
            # Use a try-except block to handle potential file corruption or locking issues
            df = pd.read_excel(LOG_FILE)
            # Check if columns match to avoid errors when concatenating
            if list(df.columns) == list(new_log.columns):
                df = pd.concat([df, new_log], ignore_index=True)
            else:
                logger.warning(f"Log file {LOG_FILE} columns do not match expected format. Overwriting file.")
                df = new_log # Overwrite if columns don't match
        except Exception as e:
            logger.error(f"Error reading or processing log file {LOG_FILE}: {e}. Creating a new log file.")
            df = new_log # Create new df if reading fails
    else:
        df = new_log

    try:
        # Save the updated DataFrame back to Excel
        # Index=False prevents pandas from writing the DataFrame index as a column
        df.to_excel(LOG_FILE, index=False, engine='openpyxl')
        logger.info(f"Successfully logged conversation to {LOG_FILE}")
    except Exception as e:
        logger.error(f"Error writing to log file {LOG_FILE}: {e}")
        st.warning(f"Could not write conversation log to {LOG_FILE}: {e}") # Optional: Inform user

async def chat_ui(client, tools, selected_model):
    st.title("LLM Assistant with MCP Tools")
    st.write("Enter your query below to interact with the LLM and MCP tools.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display existing messages
    for message in st.session_state.messages:
        # Check if message is a dictionary and has a role
        if isinstance(message, dict) and "role" in message:
            with st.chat_message(message["role"]):
                # Only display content if it exists and is not None
                if message.get("content"):
                    st.markdown(message["content"])
                # Optionally, display something if there are tool calls but no content
                elif message.get("tool_calls"):
                    st.markdown(f"_Assistant requested tool calls..._ {message['tool_calls'][0]['function']['name']}") # Simple placeholder
        else:
            # Log unexpected message format
            logger.warning(f"Skipping rendering message due to unexpected format: {type(message)} - {message}")

    # Add a unique key to chat_input
    user_input = st.chat_input("Enter your prompt", key="chat_input_main")
    if user_input:
        # Add user message to state immediately
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)

        # Process the input
        if client:
            try:
                db_context = None
                sql_query_tool_schema = tools.get('sql_query', {}).get('schema')

                if sql_query_tool_schema:
                    logger.info(f"Attempting to generate SQL for query: '{user_input}'")
                    with st.spinner("Checking if database query is needed..."):
                        sql_params = await generate_sql_for_prompt(
                            user_input,
                            client,
                            selected_model,
                            sql_query_tool_schema
                        )
                        logger.info(f"SQL generation result (sql_params): {sql_params}")

                    if sql_params and sql_params.get('query'):
                        logger.info(f"Generated SQL query: {sql_params['query']}")
                        with st.spinner(f"Executing SQL query: `{sql_params['query']}`..."):
                            try:
                                sql_tool_callable = tools.get('sql_query', {}).get('callable')
                                if sql_tool_callable:
                                    logger.info(f"Executing SQL with callable: {sql_tool_callable}")
                                    db_results = await sql_tool_callable(**sql_params)
                                    db_context = json.dumps(db_results)
                                    st.info(f"Retrieved data from database based on your query.")
                                    logger.info(f"Database context fetched (first 500 chars): {db_context[:500]}...")
                                else:
                                    st.error("SQL query tool callable not found in tools configuration.")
                                    logger.error("SQL query tool callable not found.")
                            except Exception as e:
                                st.error(f"Failed to execute SQL query: {e}")
                                logger.error(f"Error executing SQL query {sql_params.get('query')}: {e}", exc_info=True)
                    else:
                        logger.info("No SQL query generated or needed for this prompt.")
                else:
                    logger.warning("'sql_query' tool schema not found in tools. Skipping SQL generation step.")

                logger.info(f"Calling agent_loop with db_context (present: {db_context is not None})")
                with st.spinner("Generating response..."):
                    response, messages = await agent_loop(
                        user_input,
                        tools,
                        client,
                        st.session_state.messages,
                        selected_model,
                        db_context=db_context
                    )
                    st.session_state.messages = messages

                with st.chat_message("assistant"):
                    st.markdown(response)

                # Log the interaction after getting the response
                try:
                    current_time = datetime.now()
                    log_conversation_to_excel(
                        timestamp=current_time,
                        user_question=user_input, # The latest user input
                        bot_answer=response, # The final response from the agent
                        model_name=selected_model # The model selected in the sidebar
                    )
                except Exception as log_e:
                    logger.error(f"Failed to log conversation: {log_e}", exc_info=True)
                    st.warning(f"Failed to save conversation log: {log_e}")

            except openai.APITimeoutError as e:
                logger.error(f"API call timed out: {e}", exc_info=True)
                st.error("The request to the AI assistant timed out. Please try again later.")

            except Exception as e:
                logger.error(f"An error occurred processing the prompt: {e}", exc_info=True)
                st.error(f"An unexpected error occurred: {e}")

        else:
            st.error("MCP Client not available.")
            logger.error("MCP Client not available when trying to process user input.")
