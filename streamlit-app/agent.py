"""
Agent module - Sets up a simple agent with Claude Sonnet 4.5 LLM and MCP tools.
"""

from typing import List, Dict, Any, Optional, Tuple
import json
import re
from langchain_core.tools import Tool
from utils.llm_factory import get_llm
from config import AGENT_MAX_ITERATIONS, AGENT_VERBOSE


class MCPAgent:
    """Simple agent that uses Claude Sonnet 4.5 and MCP tools."""

    def __init__(self, tools: List[Tool]):
        """
        Initialize the MCP agent.

        Args:
            tools: List of LangChain tools (from MCP servers)
        """
        self.tools = tools
        self.llm = None
        self.tools_dict = {tool.name: tool for tool in tools}

        self._setup_agent()

    def _setup_agent(self):
        """Set up the LLM using the factory."""
        try:
            self.llm = get_llm(temperature=0.7)
        except ValueError as e:
            raise ValueError(
                f"Failed to initialize LLM: {e}\n"
                "Make sure to set ANTHROPIC_API_KEY environment variable."
            )
        except ImportError as e:
            raise ImportError(
                f"Missing required package: {e}\n"
                "Run: pip install -r requirements.txt"
            )

    def _create_prompt(self, question: str) -> str:
        """Create a prompt for the LLM with available tools."""
        if not self.tools:
            return f"""You are a helpful AI assistant specialized in pharmaceutical research, chemistry, biology, and drug development.

Please answer the following question to the best of your knowledge:

Question: {question}

Answer:"""

        tools_desc = "\n".join([
            f"- {tool.name}: {tool.description}"
            for tool in self.tools
        ])

        return f"""You are a helpful AI assistant that can query chemical compound databases.

Available tools:
{tools_desc}

When you need to use a tool, respond in this exact format:
ACTION: tool_name
INPUT: {{"parameter": "value"}}

When you have the final answer, respond with:
FINAL ANSWER: your answer here

Question: {question}

Let's think step by step:"""

    def _parse_action(self, text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Parse action and input from LLM response."""
        action_match = re.search(r'ACTION:\s*(\w+)', text, re.IGNORECASE)
        input_match = re.search(r'INPUT:\s*(\{[^}]+\})', text, re.IGNORECASE | re.DOTALL)

        if action_match and input_match:
            action = action_match.group(1).strip()
            try:
                input_str = input_match.group(1).strip()
                tool_input = json.loads(input_str)
                return action, tool_input
            except json.JSONDecodeError:
                input_text = input_match.group(1).strip()
                if '"' in input_text:
                    parts = input_text.split('"')
                    if len(parts) >= 4:
                        key = parts[1]
                        value = parts[3]
                        return action, {key: value}

        return None

    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the agent with a question.

        Args:
            question: The question to ask the agent

        Returns:
            Dictionary with 'output' and 'intermediate_steps'
        """
        if not self.llm:
            return {
                "output": "Error: Agent not initialized",
                "intermediate_steps": []
            }

        intermediate_steps = []
        conversation = self._create_prompt(question)

        # If no tools, use direct LLM mode
        if not self.tools:
            try:
                response = self.llm.invoke(conversation)
                answer = response.content if hasattr(response, 'content') else str(response)
                return {
                    "output": answer,
                    "intermediate_steps": []
                }
            except Exception as e:
                return {
                    "output": f"Error generating response: {str(e)}",
                    "intermediate_steps": []
                }

        # Tool-calling mode
        try:
            for iteration in range(AGENT_MAX_ITERATIONS):
                if AGENT_VERBOSE:
                    print(f"\n=== Iteration {iteration + 1} ===")

                response = self.llm.invoke(conversation)
                response_text = response.content if hasattr(response, 'content') else str(response)

                if AGENT_VERBOSE:
                    print(f"Response: {response_text[:500]}")

                # Check for final answer
                if "FINAL ANSWER:" in response_text.upper():
                    final_answer = re.search(
                        r'FINAL ANSWER:\s*(.+)',
                        response_text,
                        re.IGNORECASE | re.DOTALL
                    )
                    if final_answer:
                        return {
                            "output": final_answer.group(1).strip(),
                            "intermediate_steps": intermediate_steps
                        }

                # Try to parse action
                action_result = self._parse_action(response_text)

                if action_result:
                    action_name, action_input = action_result

                    if action_name in self.tools_dict:
                        tool = self.tools_dict[action_name]
                        try:
                            observation = tool.func(json.dumps(action_input))
                            intermediate_steps.append((
                                type('Action', (), {
                                    'tool': action_name,
                                    'tool_input': action_input
                                })(),
                                observation
                            ))
                            conversation += f"\n\n{response_text}\n\nOBSERVATION: {observation}\n\nWhat should I do next?"
                        except Exception as e:
                            observation = f"Error executing tool: {str(e)}"
                            conversation += f"\n\n{response_text}\n\nOBSERVATION: {observation}\n\nWhat should I do next?"
                    else:
                        conversation += f"\n\n{response_text}\n\nError: Tool '{action_name}' not found. Available tools: {', '.join(self.tools_dict.keys())}\n\nWhat should I do next?"
                else:
                    conversation += f"\n\n{response_text}\n\nPlease either use a tool with ACTION/INPUT format or provide a FINAL ANSWER."

            return {
                "output": "I apologize, but I couldn't find a complete answer within the iteration limit. Please try rephrasing your question.",
                "intermediate_steps": intermediate_steps
            }

        except Exception as e:
            return {
                "output": f"Error executing query: {str(e)}",
                "intermediate_steps": intermediate_steps
            }

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]
