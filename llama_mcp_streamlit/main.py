import asyncio
import streamlit as st
from ui.sidebar import sidebar
from ui.chat_ui import chat_ui
from utils.mcp_client import MCPClient
from utils.mcp_server import get_server_params, DEFAULT_DB_PARAMS

async def main():
    st.set_page_config(layout="wide")

    client, selected_model = sidebar()

    current_server_params = get_server_params()

    db_host = st.session_state.get('db_host', DEFAULT_DB_PARAMS['host'])
    db_port = st.session_state.get('db_port', DEFAULT_DB_PARAMS['port'])
    db_name = st.session_state.get('db_name', DEFAULT_DB_PARAMS['database'])
    st.sidebar.info(f"Attempting to connect to:\nHost: {db_host}\nPort: {db_port}\nDB: {db_name}")

    if client is None:
        st.error("API client failed to initialize. Please check API configuration in the sidebar.")
        return

    try:
        async with MCPClient(current_server_params) as mcp_client:
            try:
                mcp_tools = await mcp_client.get_available_tools()
                tools = {}
                for tool in mcp_tools:
                    if tool.name != "list_tables":
                        # Lấy thông tin gốc từ server
                        tool_description = tool.description
                        tool_input_schema = tool.inputSchema

                        # ====> SỬA DESCRIPTION Ở ĐÂY <====
                        if tool.name == "sql_query":
                            tool_description = "Lấy thông tin dữ liệu chất lượng không khí trong database airpollution" # Thay bằng mô tả bạn muốn

                        tools[tool.name] = {
                            "name": tool.name,
                            "callable": mcp_client.call_tool(tool.name),
                            "schema": {
                                "type": "function",
                                "function": {
                                    "name": tool.name,
                                    "description": tool_description, # Sử dụng description đã sửa
                                    "parameters": tool_input_schema,
                                },
                            },
                        }
                st.session_state.tools = tools
                st.sidebar.success("MCP Client connected and tools loaded.")
            except Exception as e:
                st.error(f"Failed to get available tools from MCP server: {e}")
                st.error(f"Attempted connection details:\nHost: {db_host}\nPort: {db_port}\nDB: {db_name}")
                st.error("Please ensure the database connection details are correct, the database is running, and the MCP server process (npx) can start.")
                tools = {}
                st.session_state.tools = tools

            await chat_ui(client, tools, selected_model)

    except Exception as e:
        st.error(f"Failed to initialize MCP Client: {e}")
        st.error(f"Attempted connection details:\nHost: {db_host}\nPort: {db_port}\nDB: {db_name}")
        st.error("Check database details, network connection, and npx server setup.")
        await chat_ui(client, {}, selected_model)

if __name__ == "__main__":
    if 'db_host' not in st.session_state:
        st.session_state.db_host = DEFAULT_DB_PARAMS['host']
    if 'db_port' not in st.session_state:
        st.session_state.db_port = DEFAULT_DB_PARAMS['port']
    if 'db_name' not in st.session_state:
        st.session_state.db_name = DEFAULT_DB_PARAMS['database']
    if 'db_user' not in st.session_state:
        st.session_state.db_user = DEFAULT_DB_PARAMS['user']
    if 'db_password' not in st.session_state:
        st.session_state.db_password = DEFAULT_DB_PARAMS['password']

    asyncio.run(main())
