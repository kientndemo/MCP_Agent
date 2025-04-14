import streamlit as st
from mcp import StdioServerParameters
from utils.sql_tool import sql_query_handler
import os

# Default DB parameters (can be overridden by session_state)
DEFAULT_DB_PARAMS = {
    "host": "localhost",
    "port": 5432,
    "database": "airpollution",
    "user": "postgres",
    "password": "123456" # Consider storing sensitive info more securely
}

def get_server_params():
    """Constructs StdioServerParameters based on Streamlit session state."""
    # Get DB details from session_state, falling back to defaults
    db_host = st.session_state.get('db_host', DEFAULT_DB_PARAMS['host'])
    db_port = st.session_state.get('db_port', DEFAULT_DB_PARAMS['port'])
    db_name = st.session_state.get('db_name', DEFAULT_DB_PARAMS['database'])
    db_user = st.session_state.get('db_user', DEFAULT_DB_PARAMS['user'])
    db_password = st.session_state.get('db_password', DEFAULT_DB_PARAMS['password'])

    # Construct the database connection URL
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    # Return npx server parameters using the dynamic db_url
    return StdioServerParameters(
        command="npx",
        # Consider making the npx path configurable or detecting it
        # command="/opt/homebrew/bin/npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-postgres",
            db_url
        ]
    )


# server_params = StdioServerParameters(
#     command="npx",
#     args=["-y", "@executeautomation/playwright-mcp-server"],
#     env=None,
# )

# server_params = StdioServerParameters(
#     command="docker",
#     args=[
#         "run",
#         "-i",
#         "--rm",
#         "--mount", "type=bind,src=/Volumes/DATA/Graphrag,dst=/Volumes/DATA/Graphrag",
#         "--mount", "type=bind,src=/path/to/other/allowed/dir,dst=/projects/other/allowed/dir,ro",
#         "--mount", "type=bind,src=/path/to/file.txt,dst=/projects/path/to/file.txt",
#         "mcp/filesystem",
#         "/projects"
#     ],
#     env=None,
# )

# Thêm tool SQL mới vào danh sách các tool của MCP server.

# Cấu hình Postgres của bạn - NO LONGER USED DIRECTLY, see get_server_params()
# db_params = {
#     "host": "localhost",
#     "port": 5432,
#     "database": "airpollution",
#     "user": "postgres",
#     "password": "123456"
# }

########################################################################
# Lựa chọn 1: Sử dụng NPX server (Now configured dynamically)
########################################################################

# Hãy điều chỉnh đường dẫn thực tế và thư mục được phép mount tuỳ theo hệ thống của bạn
# Ví dụ: "/Users/username/Desktop" và "/path/to/other/allowed/dir"
# Ngoài ra, bạn có thể truyền db_params qua env nếu muốn dùng bên trong container.

# Tạo URL kết nối PostgreSQL từ db_params - MOVED TO get_server_params()
# db_url = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"

# npx_server_params = StdioServerParameters(
#     command="npx",
#     # command="/opt/homebrew/bin/npx",
#     args=[
#         "-y",
#         "@modelcontextprotocol/server-postgres",
#         db_url
#     ]
# )


########################################################################
# Lựa chọn 2: Sử dụng Docker server (Configuration remains static for now)
########################################################################

# Ví dụ docker run:
# --mount "type=bind,src=/Users/username/Desktop,dst=/projects/Desktop"
# --mount "type=bind,src=/path/to/other/allowed/dir,dst=/projects/other/allowed/dir,ro"
# v.v...
docker_server_params = StdioServerParameters(
    command="/usr/local/bin/docker", # Consider making this configurable
    args=[
        "run",
        "-i",
        "--rm",
        "mcp/postgres",
        "postgresql://admin:123456@host.docker.internal:5432/mydatabase" # Static example URL
    ],
)

# Tuỳ chọn server params mà bạn mong muốn:
# server_params = get_server_params() # Use the dynamic function for NPX
# server_params = docker_server_params # Or choose the static Docker config

# NOTE: The main application (main.py) will now call get_server_params()
#       so the direct assignment here is less relevant unless you want
#       to force a specific configuration (like Docker) globally.

# This dictionary seems unused based on the provided context.
# If it's needed elsewhere, ensure sql_query_handler gets the dynamic DB params.
registered_tools = {
    # Các tool khác của bạn...
    "sql_query": {
        # "description": "Thực hiện truy vấn SQL trên bảng air_quality",
        "description": "Lấy thông tin dữ liệu chất lượng không khí trong database airpollution",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Câu truy vấn SQL cần thực hiện"
                },
                "params": {
                    "type": "object",
                    "description": "Các tham số cho câu truy vấn",
                    "default": {}
                }
            },
            "required": ["query"],
        },
        "handler": sql_query_handler, # Handler might need dynamic DB config if used directly
    },
}
