"""
Agent module - Sets up a simple agent with configurable LLM and MCP tools.
"""

from typing import List, Dict, Any, Optional, Tuple
import json
import re
from langchain_core.tools import Tool
from utils.llm_factory import get_llm_from_config
from config import AGENT_MAX_ITERATIONS, AGENT_VERBOSE


class MCPAgent:
    """Simple agent that uses configurable LLM and MCP tools."""

    def __init__(self, tools: List[Tool], config_data: Optional[Dict[str, Any]] = None):
        """
        Initialize the MCP agent.

        Args:
            tools: List of LangChain tools (from MCP servers)
            config_data: Configuration data from ConfigurationManager
        """
        self.tools = tools
        self.config_data = config_data
        self.llm = None
        self.tools_dict = {tool.name: tool for tool in tools}

        self._setup_agent()

    def _setup_agent(self):
        """Set up the LLM using the factory."""
        try:
            if self.config_data:
                # Use new configuration system
                self.llm = get_llm_from_config(self.config_data, temperature=0.7)
            else:
                # Fallback to legacy method for backward compatibility
                from utils.llm_factory import get_llm
                self.llm = get_llm(temperature=0.7)
                
        except ValueError as e:
            error_msg = f"Failed to initialize LLM: {e}"
            if self.config_data and self.config_data.get("profile", {}).name == "merck":
                error_msg += "\nMake sure to set AZURE_OPENAI_API_KEY or AZURE_API_KEY environment variable."
            else:
                error_msg += "\nMake sure to set ANTHROPIC_API_KEY environment variable."
            raise ValueError(error_msg)
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

        return f"""You are a Pharmaceutical Research AI Agent. You MUST use tools to provide accurate, data-driven answers.

AVAILABLE TOOLS:
{tools_desc}

CRITICAL INSTRUCTIONS:
1. ONLY use tools from the AVAILABLE TOOLS list above
2. DO NOT use "think" or any other tools not listed above
3. To use a tool, use this EXACT format:
ACTION: tool_name
INPUT: {{"parameter": "value"}}

4. When you have enough information, use this EXACT format:
FINAL ANSWER: your complete research summary here

5. DO NOT provide conversational filler or reasoning steps
6. Start with a tool call to gather information, then provide FINAL ANSWER

Question: {question}

Begin by selecting an appropriate tool from the available list:"""

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
            no_action_count = 0  # Track consecutive responses with no tool call
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
                    no_action_count = 0
                    action_name, action_input = action_result

                    # Special handling for "think" tool attempts
                    if action_name.lower() == "think":
                        error_msg = f"ERROR: 'think' is not a valid tool. You must use one of the available tools: {', '.join(self.tools_dict.keys())}. Please select an actual tool to gather information."
                        conversation += f"\n\n{response_text}\n\n{error_msg}\n\nSelect a real tool from the available list:"
                        continue

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
                            intermediate_steps.append((
                                type('Action', (), {
                                    'tool': action_name,
                                    'tool_input': action_input
                                })(),
                                observation
                            ))
                            conversation += f"\n\n{response_text}\n\nOBSERVATION: {observation}\n\nPlease try a different approach or provide a FINAL ANSWER."
                    else:
                        error_msg = f"Error: Tool '{action_name}' not found. Available tools: {', '.join(self.tools_dict.keys())}\n\nPlease use ONLY the tools listed above."
                        conversation += f"\n\n{response_text}\n\n{error_msg}\n\nSelect a valid tool:"
                else:
                    no_action_count += 1
                    # If the LLM gave a substantial response without ACTION or 
                    # FINAL ANSWER markers, give it ONE nudge before giving up.
                    # This prevents 1B models from "chatting" instead of doing research.
                    if no_action_count >= 2:
                        return {
                            "output": response_text.strip(),
                            "intermediate_steps": intermediate_steps
                        }
                    
                    # If it's the first non-compliant response, nudge it to use the format
                    conversation += f"\n\n{response_text}\n\nERROR: You did not follow the required ACTION/INPUT format or provide a FINAL ANSWER. Please use a tool to research the question."

            # If we exhausted iterations but got tool results, synthesize them
            if intermediate_steps:
                last_observations = [obs for _, obs in intermediate_steps[-3:]]
                return {
                    "output": "\n\n".join(last_observations),
                    "intermediate_steps": intermediate_steps
                }

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
