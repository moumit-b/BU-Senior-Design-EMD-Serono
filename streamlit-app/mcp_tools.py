"""
MCP Tools module - Connects to MCP servers and exposes their tools to LangChain.
"""

import asyncio
from typing import List, Dict, Any, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
try:
    from langchain_core.tools import Tool
except ImportError:
    from langchain.tools import Tool
from pydantic import BaseModel, Field
import json


class MCPToolWrapper:
    """Wrapper to manage MCP server connections and expose tools to LangChain."""

    def __init__(self, server_config: Dict[str, Any]):
        """
        Initialize the MCP tool wrapper.

        Args:
            server_config: Configuration dict with 'command', 'args', and 'description'
        """
        self.server_config = server_config
        self.session: Optional[ClientSession] = None
        self.read_stream = None
        self.write_stream = None
        self._tools_cache: List[Any] = []
        self._context_manager = None

    async def connect(self):
        """Establish connection to the MCP server."""
        server_params = StdioServerParameters(
            command=self.server_config["command"],
            args=self.server_config["args"]
        )

        # Create stdio client connection using async context manager
        self._context_manager = stdio_client(server_params)
        self.read_stream, self.write_stream = await self._context_manager.__aenter__()

        # Initialize session
        self.session = ClientSession(self.read_stream, self.write_stream)
        await self.session.__aenter__()

        # Initialize the session
        await self.session.initialize()

        # Fetch available tools
        response = await self.session.list_tools()
        self._tools_cache = response.tools if hasattr(response, 'tools') else []

    async def disconnect(self):
        """Close the MCP server connection."""
        if self.session:
            await self.session.__aexit__(None, None, None)

        if self._context_manager:
            await self._context_manager.__aexit__(None, None, None)

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            String result from the tool execution
        """
        if not self.session:
            return "Error: MCP session not initialized"

        try:
            result = await self.session.call_tool(tool_name, arguments)
            # Extract text content from result
            if hasattr(result, 'content') and result.content:
                # Handle list of content items
                if isinstance(result.content, list):
                    text_parts = []
                    for item in result.content:
                        if hasattr(item, 'text'):
                            text_parts.append(item.text)
                        elif isinstance(item, dict) and 'text' in item:
                            text_parts.append(item['text'])
                    return '\n'.join(text_parts) if text_parts else str(result.content)
                return str(result.content)
            return json.dumps(result, default=str, indent=2)
        except Exception as e:
            return f"Error calling tool {tool_name}: {str(e)}"

    def get_langchain_tools(self) -> List[Tool]:
        """
        Convert MCP tools to LangChain tools.

        Returns:
            List of LangChain Tool objects
        """
        langchain_tools = []

        for mcp_tool in self._tools_cache:
            tool_name = mcp_tool.name
            tool_description = mcp_tool.description or "No description available"

            # Create a closure to capture the tool_name and self
            def make_tool_func(name: str, wrapper_instance):
                def tool_func(arguments: str) -> str:
                    """Execute the MCP tool."""
                    try:
                        # Parse arguments if they're a JSON string
                        if isinstance(arguments, str):
                            args_dict = json.loads(arguments)
                        else:
                            args_dict = arguments
                    except json.JSONDecodeError:
                        # Try to extract simple key-value
                        args_dict = {"query": arguments}

                    # Run the async call in the event loop
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Create a new event loop in a thread
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(
                                    lambda: asyncio.run(wrapper_instance.call_tool(name, args_dict))
                                )
                                result = future.result(timeout=30)
                                return result
                        else:
                            result = loop.run_until_complete(wrapper_instance.call_tool(name, args_dict))
                            return result
                    except Exception as e:
                        return f"Error executing tool: {str(e)}"

                return tool_func

            langchain_tool = Tool(
                name=tool_name,
                func=make_tool_func(tool_name, self),
                description=tool_description
            )
            langchain_tools.append(langchain_tool)

        return langchain_tools


async def initialize_mcp_tools(servers_config: Dict[str, Dict[str, Any]]) -> List[Tool]:
    """
    Initialize MCP servers and return LangChain tools.

    Args:
        servers_config: Dictionary of server configurations

    Returns:
        List of LangChain tools from all connected MCP servers
    """
    all_tools = []

    for server_name, config in servers_config.items():
        print(f"Connecting to MCP server: {server_name}...")
        wrapper = MCPToolWrapper(config)

        try:
            await wrapper.connect()
            tools = wrapper.get_langchain_tools()
            all_tools.extend(tools)
            print(f"✓ Connected to {server_name}, loaded {len(tools)} tools")
        except Exception as e:
            print(f"✗ Failed to connect to {server_name}: {str(e)}")
            import traceback
            traceback.print_exc()

    return all_tools
