import streamlit as st
from mcp import StdioServerParameters
from utils.sql_tool import sql_query_handler
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default DB parameters (least priority)
DEFAULT_DB_PARAMS = {
    "host": "localhost", # Default to container localhost
    "port": 5432,
    "database": "airpollution",
    "user": "postgres",
    "password": "" # Default password should be empty or a placeholder
}

def get_server_params():
    """Constructs StdioServerParameters based on environment variables, session state, or defaults."""
    # Get DB details prioritizing Env -> Session State -> Defaults
    db_host = os.environ.get('DB_HOST', st.session_state.get('db_host', DEFAULT_DB_PARAMS['host']))
    db_port = os.environ.get('DB_PORT', st.session_state.get('db_port', DEFAULT_DB_PARAMS['port']))
    db_name = os.environ.get('DB_NAME', st.session_state.get('db_name', DEFAULT_DB_PARAMS['database']))
    db_user = os.environ.get('DB_USER', st.session_state.get('db_user', DEFAULT_DB_PARAMS['user']))
    db_password = os.environ.get('DB_PASSWORD', st.session_state.get('db_password', DEFAULT_DB_PARAMS['password']))

    # Construct the database connection URL
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    # Ensure npx command exists and is executable if needed, or adjust path
    npx_command = "npx" # Consider adding logic to find npx path if necessary

    return StdioServerParameters(
        command=npx_command,
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
