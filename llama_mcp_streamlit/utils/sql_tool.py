# utils/sql_tool.py
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection parameters
db_params = {
    "host": "localhost",
    "port": 5432,
    "database": "airpollution",
    "user": "postgres",
    "password": "123456"
}

async def sql_query_handler(params):
    """
    Hàm xử lý yêu cầu truy vấn SQL từ MCP server.
    
    Tham số:
      - params: dict chứa các tham số, trong đó bắt buộc có khóa "query" và tuỳ chọn "params"
    """
    query = params.get("query")
    query_params = params.get("params", {})

    def execute_query():
        with psycopg2.connect(**db_params, cursor_factory=RealDictCursor) as conn:
            with conn.cursor() as cur:
                cur.execute(query, query_params)
                return cur.fetchall()

    # Run the query in a thread pool to avoid blocking
    result = await asyncio.to_thread(execute_query)
    return result