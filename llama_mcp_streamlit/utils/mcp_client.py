import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Any, List

class MCPClient:

    def __init__(self, server_params: StdioServerParameters):
        self.server_params = server_params
        self.session = None
        self._client = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)

    async def connect(self):
        self._client = stdio_client(self.server_params)
        self.read, self.write = await self._client.__aenter__()
        session = ClientSession(self.read, self.write)
        self.session = await session.__aenter__()
        await self.session.initialize()

    async def get_available_tools(self) -> List[Any]:
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        # Assume list_tools() returns a ListToolsResult object
        result = await self.session.list_tools()
        # Access the 'tools' attribute of the result object
        tools_list = result.tools
        return tools_list

    def call_tool(self, tool_name: str) -> Any:
        if not self.session:
            raise RuntimeError("Not connected to MCP server")

        async def callable(*args, **kwargs):
            response = await self.session.call_tool(tool_name, arguments=kwargs)
            return response.content[0].text

        return callable

# import json
# from mcp import ClientSession, StdioServerParameters
# from mcp.client.stdio import stdio_client
# from typing import Any, List

# class MCPClient:

#     def __init__(self, server_params: StdioServerParameters):
#         self.server_params = server_params
#         self.session = None
#         self._client = None

#     async def __aenter__(self):
#         await self.connect()
#         return self

#     async def __aexit__(self, exc_type, exc_val, exc_tb):
#         if self.session:
#             await self.session.__aexit__(exc_type, exc_val, exc_tb)
#         if self._client:
#             await self._client.__aexit__(exc_type, exc_val, exc_tb)

#     async def connect(self):
#         self._client = stdio_client(self.server_params)
#         self.read, self.write = await self._client.__aenter__()
#         session = ClientSession(self.read, self.write)
#         self.session = await session.__aenter__()
#         await self.session.initialize()

#     async def get_available_tools(self) -> List[Any]:
#         if not self.session:
#             raise RuntimeError("Not connected to MCP server")

#         tools = await self.session.list_tools()
#         _, tools_list = tools
#         _, tools_list = tools_list
#         return tools_list

#     async def call_tool(self, tool_name: str, **kwargs) -> Any:
#         if not self.session:
#             raise RuntimeError("Not connected to MCP server")

#         # Gọi hàm bất đồng bộ và trả về kết quả
#         response = await self.session.call_tool(tool_name, arguments=kwargs)
#         return response.content[0].text


