"""
MCP Tools module - Connects to MCP servers and exposes their tools to LangChain.
"""

import asyncio
import threading
from typing import List, Dict, Any, Optional
import json

# Import MCP components if available
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("[WARNING] MCP package not available. MCP server connections will not work.")

# Import LangChain Tool
from langchain_core.tools import Tool
from pydantic import BaseModel, Field


# Global storage for the background event loop
_mcp_loop: Optional[asyncio.AbstractEventLoop] = None
_mcp_thread: Optional[threading.Thread] = None

def _start_background_loop(loop: asyncio.AbstractEventLoop):
    """Run the event loop in a background thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()

def get_mcp_loop() -> asyncio.AbstractEventLoop:
    """Get or create the global background event loop for MCP operations."""
    global _mcp_loop, _mcp_thread
    if _mcp_loop is None:
        _mcp_loop = asyncio.new_event_loop()
        _mcp_thread = threading.Thread(target=_start_background_loop, args=(_mcp_loop,), daemon=True)
        _mcp_thread.start()
    return _mcp_loop


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
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def connect(self):
        """Establish connection to the MCP server."""
        self._loop = asyncio.get_running_loop()
        
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
            try:
                await self.session.__aexit__(None, None, None)
            except:
                pass

        if self._context_manager:
            try:
                await self._context_manager.__aexit__(None, None, None)
            except:
                pass
        
        self.session = None
        self._context_manager = None

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
            import traceback
            error_detail = f"{type(e).__name__}: {str(e)}\nTraceback:\n{traceback.format_exc()}"
            return f"Error calling tool {tool_name}: {error_detail}"

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
            def make_tool_func(name: str, wrapper_instance: 'MCPToolWrapper'):
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

                    # Use run_coroutine_threadsafe to execute call_tool in the background loop
                    if not wrapper_instance._loop:
                        return f"Error: MCP wrapper loop not initialized for tool {name}"
                    
                    try:
                        future = asyncio.run_coroutine_threadsafe(
                            wrapper_instance.call_tool(name, args_dict),
                            wrapper_instance._loop
                        )
                        # Wait for the result with a timeout
                        return future.result(timeout=60)
                    except TimeoutError:
                        return f"Tool {name} timed out after 60 seconds"
                    except Exception as e:
                        return f"Error executing tool {name}: {str(e)}"

                return tool_func

            langchain_tool = Tool(
                name=tool_name,
                func=make_tool_func(tool_name, self),
                description=tool_description
            )
            langchain_tools.append(langchain_tool)

        return langchain_tools


# Global storage for active MCP wrappers to keep connections alive
_active_wrappers = {}

async def initialize_mcp_tools(servers_config: Dict[str, Dict[str, Any]]) -> List[Tool]:
    """
    Initialize MCP servers and return LangChain tools.

    Args:
        servers_config: Dictionary of server configurations

    Returns:
        List of LangChain tools from all connected MCP servers
    """
    if not MCP_AVAILABLE:
        print("[WARNING] MCP package not installed. Skipping MCP server initialization.")
        print("[INFO] Install with: pip install mcp")
        return []

    all_tools = []
    global _active_wrappers
    
    # Clear any existing connections first
    for wrapper in list(_active_wrappers.values()):
        try:
            await wrapper.disconnect()
        except:
            pass
    _active_wrappers.clear()

    for server_name, config in servers_config.items():
        print(f"Connecting to MCP server: {server_name}...")
        wrapper = MCPToolWrapper(config)

        try:
            await wrapper.connect()
            tools = wrapper.get_langchain_tools()
            all_tools.extend(tools)
            
            # Store the wrapper to keep the connection alive
            _active_wrappers[server_name] = wrapper
            
            print(f"✓ Connected to {server_name}, loaded {len(tools)} tools")
        except Exception as e:
            print(f"✗ Failed to connect to {server_name}: {str(e)}")
            # Try to clean up any partially initialized connections
            try:
                await wrapper.disconnect()
            except:
                pass  # Ignore cleanup errors

    return all_tools
