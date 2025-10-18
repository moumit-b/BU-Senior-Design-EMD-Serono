"""
Agent module - Sets up the LangChain agent with Ollama and MCP tools.
"""

from typing import List, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, AGENT_MAX_ITERATIONS, AGENT_VERBOSE


# ReAct prompt template for the agent
REACT_PROMPT = """You are a helpful AI assistant that can query chemical compound databases and other data sources.
You have access to the following tools:

{tools}

Tool Names: {tool_names}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action (must be valid JSON for the tool)
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""


class MCPAgent:
    """LangChain agent that uses Ollama LLM and MCP tools."""

    def __init__(self, tools: List[Tool], model_name: str = OLLAMA_MODEL):
        """
        Initialize the MCP agent.

        Args:
            tools: List of LangChain tools (from MCP servers)
            model_name: Name of the Ollama model to use
        """
        self.tools = tools
        self.model_name = model_name
        self.llm = None
        self.agent_executor = None

        self._setup_agent()

    def _setup_agent(self):
        """Set up the LangChain agent with Ollama LLM."""
        # Initialize Ollama LLM
        self.llm = OllamaLLM(
            model=self.model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=0.7,
        )

        # Create the prompt template
        prompt = PromptTemplate(
            template=REACT_PROMPT,
            input_variables=["input", "agent_scratchpad"],
            partial_variables={
                "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools]),
                "tool_names": ", ".join([tool.name for tool in self.tools])
            }
        )

        # Create the ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=AGENT_VERBOSE,
            max_iterations=AGENT_MAX_ITERATIONS,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )

    def query(self, question: str) -> dict:
        """
        Query the agent with a question.

        Args:
            question: The question to ask the agent

        Returns:
            Dictionary with 'output' and 'intermediate_steps'
        """
        if not self.agent_executor:
            return {
                "output": "Error: Agent not initialized",
                "intermediate_steps": []
            }

        try:
            result = self.agent_executor.invoke({"input": question})
            return result
        except Exception as e:
            return {
                "output": f"Error executing query: {str(e)}",
                "intermediate_steps": []
            }

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]
