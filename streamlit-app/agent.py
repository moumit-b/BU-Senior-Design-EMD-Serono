"""
Agent module - Sets up a simple agent with Ollama and MCP tools.
"""

from typing import List, Dict, Any, Optional, Tuple
from langchain_core.tools import Tool
from langchain_ollama import OllamaLLM
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, AGENT_MAX_ITERATIONS, AGENT_VERBOSE
import json
import re


class MCPAgent:
    """Simple agent that uses Ollama LLM and MCP tools."""

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
        self.tools_dict = {tool.name: tool for tool in tools}

        self._setup_agent()

    def _setup_agent(self):
        """Set up the Ollama LLM."""
        self.llm = OllamaLLM(
            model=self.model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=0.7,
        )

    def _create_prompt(self, question: str) -> str:
        """Create a prompt for the LLM with available tools."""
        tools_desc = "\n".join([
            f"- {tool.name}: {tool.description}"
            for tool in self.tools
        ])

        prompt = f"""You are a helpful AI assistant that can query chemical compound databases.

Available tools:
{tools_desc}

When you need to use a tool, respond in this exact format:
ACTION: tool_name
INPUT: {{"parameter": "value"}}

When you have the final answer, respond with:
FINAL ANSWER: your answer here

Question: {question}

Let's think step by step:"""

        return prompt

    def _parse_action(self, text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Parse action and input from LLM response."""
        # Look for ACTION and INPUT pattern
        action_match = re.search(r'ACTION:\s*(\w+)', text, re.IGNORECASE)
        input_match = re.search(r'INPUT:\s*({[^}]+})', text, re.IGNORECASE | re.DOTALL)

        if action_match and input_match:
            action = action_match.group(1).strip()
            try:
                input_str = input_match.group(1).strip()
                tool_input = json.loads(input_str)
                return action, tool_input
            except json.JSONDecodeError:
                # Try to extract key-value pairs manually
                input_text = input_match.group(1).strip()
                # Simple parsing for single parameter
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

        try:
            for iteration in range(AGENT_MAX_ITERATIONS):
                if AGENT_VERBOSE:
                    print(f"\n=== Iteration {iteration + 1} ===")
                    print(f"Prompt: {conversation[-500:]}")  # Last 500 chars

                # Get LLM response
                response = self.llm.invoke(conversation)

                if AGENT_VERBOSE:
                    print(f"Response: {response}")

                # Check for final answer
                if "FINAL ANSWER:" in response.upper():
                    final_answer = re.search(
                        r'FINAL ANSWER:\s*(.+)',
                        response,
                        re.IGNORECASE | re.DOTALL
                    )
                    if final_answer:
                        return {
                            "output": final_answer.group(1).strip(),
                            "intermediate_steps": intermediate_steps
                        }

                # Try to parse action
                action_result = self._parse_action(response)

                if action_result:
                    action_name, action_input = action_result

                    # Execute tool
                    if action_name in self.tools_dict:
                        tool = self.tools_dict[action_name]
                        try:
                            observation = tool.func(json.dumps(action_input))

                            # Store intermediate step
                            intermediate_steps.append((
                                type('Action', (), {
                                    'tool': action_name,
                                    'tool_input': action_input
                                })(),
                                observation
                            ))

                            # Add to conversation
                            conversation += f"\n\n{response}\n\nOBSERVATION: {observation}\n\nWhat should I do next?"

                        except Exception as e:
                            observation = f"Error executing tool: {str(e)}"
                            conversation += f"\n\n{response}\n\nOBSERVATION: {observation}\n\nWhat should I do next?"
                    else:
                        conversation += f"\n\n{response}\n\nError: Tool '{action_name}' not found. Available tools: {', '.join(self.tools_dict.keys())}\n\nWhat should I do next?"
                else:
                    # No clear action, ask LLM to clarify or provide final answer
                    conversation += f"\n\n{response}\n\nPlease either use a tool with ACTION/INPUT format or provide a FINAL ANSWER."

            # Max iterations reached
            return {
                "output": "I apologize, but I couldn't find a complete answer within the iteration limit. Please try rephrasing your question or being more specific.",
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
