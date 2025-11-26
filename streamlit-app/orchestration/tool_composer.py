"""
Tool Composer - Dynamic tool composition (Novel Feature 2).
Allows agents to create new tools by combining MCP calls.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re
import json
from models.composed_tool import (
    ComposedTool,
    ToolStep,
    ToolExecutionResult,
    ToolStepStatus,
    ToolCompositionPattern,
)


class ToolCompositionRegistry:
    """
    Registry of composed tools created by agents.
    These tools can be reused, shared, and improved over time.
    """

    def __init__(self):
        """Initialize the tool composition registry."""
        self.tools: Dict[str, ComposedTool] = {}
        self.patterns: List[ToolCompositionPattern] = []

    def register_tool(self, tool: ComposedTool):
        """Register a new composed tool."""
        self.tools[tool.name] = tool

    def get_tool(self, tool_name: str) -> Optional[ComposedTool]:
        """Retrieve a composed tool by name."""
        return self.tools.get(tool_name)

    def find_matching_tools(
        self,
        query: str,
        tags: Optional[List[str]] = None,
    ) -> List[ComposedTool]:
        """
        Find composed tools that might be suitable for a query.

        Args:
            query: The user query
            tags: Optional tags to filter by

        Returns:
            List of matching composed tools
        """
        matching_tools = []

        for tool in self.tools.values():
            # Check tags if provided
            if tags:
                if any(tag in tool.tags for tag in tags):
                    matching_tools.append(tool)
                    continue

            # Check if query keywords match tool description
            query_words = set(query.lower().split())
            desc_words = set(tool.description.lower().split())

            if len(query_words & desc_words) >= 2:  # At least 2 common words
                matching_tools.append(tool)

        # Sort by success rate
        matching_tools.sort(key=lambda t: t.success_rate, reverse=True)

        return matching_tools

    def get_top_performing_tools(self, limit: int = 10) -> List[ComposedTool]:
        """Get top performing composed tools by success rate."""
        tools_list = list(self.tools.values())
        # Filter to tools with at least 3 uses
        tools_list = [t for t in tools_list if t.times_used >= 3]
        tools_list.sort(key=lambda t: t.success_rate, reverse=True)
        return tools_list[:limit]

    def record_pattern(self, pattern: ToolCompositionPattern):
        """Record a tool composition pattern."""
        self.patterns.append(pattern)

    def suggest_composition_pattern(self, query: str) -> Optional[ToolCompositionPattern]:
        """
        Suggest a composition pattern for a query.
        This helps agents create new tools.
        """
        for pattern in self.patterns:
            # Simple pattern matching (could be enhanced with ML)
            if re.search(pattern.query_pattern, query, re.IGNORECASE):
                pattern.times_suggested += 1
                return pattern

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_tools": len(self.tools),
            "total_uses": sum(t.times_used for t in self.tools.values()),
            "avg_success_rate": (
                sum(t.success_rate for t in self.tools.values()) / len(self.tools)
                if self.tools else 0.0
            ),
            "patterns_learned": len(self.patterns),
        }


class ToolComposer:
    """
    Composes and executes multi-step tools.
    Agents use this to create new capabilities dynamically.
    """

    def __init__(self, mcp_orchestrator):
        """
        Initialize the tool composer.

        Args:
            mcp_orchestrator: MCP orchestrator for executing steps
        """
        self.mcp_orchestrator = mcp_orchestrator
        self.registry = ToolCompositionRegistry()

    async def execute_composed_tool(
        self,
        tool: ComposedTool,
        inputs: Dict[str, Any],
    ) -> ToolExecutionResult:
        """
        Execute a composed tool workflow.

        Args:
            tool: The composed tool to execute
            inputs: Input parameters

        Returns:
            Tool execution result
        """
        import time
        start_time = time.time()

        step_results = []
        step_outputs = {}  # Store outputs for variable substitution

        for step in tool.steps:
            step.status = ToolStepStatus.RUNNING

            # Resolve input template with variables
            resolved_input = self._resolve_input_template(
                step.input_template,
                inputs,
                step_outputs,
            )

            # Check run condition if specified
            if step.run_if:
                should_run = self._evaluate_condition(step.run_if, step_outputs)
                if not should_run:
                    step.status = ToolStepStatus.SKIPPED
                    continue

            # Execute step
            try:
                step_start = time.time()

                result = await self.mcp_orchestrator.call_tool(
                    tool_name=step.tool_name,
                    arguments=resolved_input,
                    preferred_mcp=step.mcp_name,
                )

                step.execution_time = time.time() - step_start
                step.result = result["result"]
                step.status = ToolStepStatus.COMPLETED

                # Store output for next steps
                step_outputs[f"step{step.step_id}"] = result["result"]

                step_results.append({
                    "step_id": step.step_id,
                    "mcp": step.mcp_name,
                    "tool": step.tool_name,
                    "status": "success",
                    "result": result["result"],
                    "time": step.execution_time,
                })

            except Exception as e:
                step.status = ToolStepStatus.FAILED
                step.error = str(e)

                step_results.append({
                    "step_id": step.step_id,
                    "mcp": step.mcp_name,
                    "tool": step.tool_name,
                    "status": "failed",
                    "error": str(e),
                })

                # Record failure and return early
                execution_time = time.time() - start_time
                tool.record_execution(success=False, execution_time=execution_time)

                return ToolExecutionResult(
                    tool_name=tool.name,
                    success=False,
                    execution_time=execution_time,
                    step_results=step_results,
                    error=f"Step {step.step_id} failed: {e}",
                    steps_executed=step.step_id,
                    steps_failed=1,
                )

        # All steps completed successfully
        execution_time = time.time() - start_time
        tool.record_execution(success=True, execution_time=execution_time)

        # Final result is the last step's output
        final_result = step_outputs.get(f"step{len(tool.steps)}")

        return ToolExecutionResult(
            tool_name=tool.name,
            success=True,
            execution_time=execution_time,
            step_results=step_results,
            final_result=final_result,
            steps_executed=len(tool.steps),
            steps_failed=0,
        )

    def _resolve_input_template(
        self,
        template: Dict[str, Any],
        user_inputs: Dict[str, Any],
        step_outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Resolve input template with variable substitution.

        Supports:
        - ${user.field} - from user inputs
        - ${step1.field} - from previous step output
        - ${step1} - entire output from step 1
        """
        resolved = {}

        for key, value in template.items():
            if isinstance(value, str) and "${" in value:
                # Variable substitution
                resolved[key] = self._substitute_variables(
                    value,
                    user_inputs,
                    step_outputs,
                )
            else:
                resolved[key] = value

        return resolved

    def _substitute_variables(
        self,
        template_str: str,
        user_inputs: Dict[str, Any],
        step_outputs: Dict[str, Any],
    ) -> Any:
        """Substitute variables in template string."""
        # Pattern: ${source.field} or ${source}
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, template_str)

        result = template_str
        for match in matches:
            if "." in match:
                source, field = match.split(".", 1)
            else:
                source, field = match, None

            # Get value from appropriate source
            value = None
            if source == "user":
                value = user_inputs.get(field) if field else user_inputs
            elif source.startswith("step"):
                step_output = step_outputs.get(source)
                if step_output:
                    if field:
                        # Try to extract field from JSON
                        try:
                            data = json.loads(step_output) if isinstance(step_output, str) else step_output
                            value = data.get(field)
                        except:
                            value = step_output
                    else:
                        value = step_output

            # Replace in result
            if value is not None:
                result = result.replace(f"${{{match}}}", str(value))

        return result

    def _evaluate_condition(
        self,
        condition: str,
        step_outputs: Dict[str, Any],
    ) -> bool:
        """
        Evaluate a condition string.

        Example: "step1.success == True"
        """
        # Simple evaluation (could be enhanced)
        # For now, just check if step succeeded
        if "success" in condition.lower():
            step_match = re.search(r'step(\d+)', condition)
            if step_match:
                step_num = step_match.group(1)
                step_key = f"step{step_num}"
                return step_key in step_outputs

        return True  # Default to running

    def create_composed_tool(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        creator_agent: str,
        tags: List[str] = None,
    ) -> ComposedTool:
        """
        Create a new composed tool.

        Args:
            name: Tool name
            description: Tool description
            steps: List of step definitions
            creator_agent: Name of agent creating this tool
            tags: Optional tags for categorization

        Returns:
            Created ComposedTool instance
        """
        tool_steps = []

        for i, step_def in enumerate(steps):
            tool_step = ToolStep(
                step_id=i + 1,
                mcp_name=step_def["mcp"],
                tool_name=step_def["tool"],
                input_template=step_def["input"],
                run_if=step_def.get("run_if"),
            )
            tool_steps.append(tool_step)

        composed_tool = ComposedTool(
            name=name,
            description=description,
            created_by=creator_agent,
            steps=tool_steps,
            tags=tags or [],
        )

        # Register in registry
        self.registry.register_tool(composed_tool)

        return composed_tool

    def get_tool_or_suggest(self, query: str) -> Optional[ComposedTool]:
        """
        Find existing composed tool or None if needs to be created.

        Args:
            query: User query

        Returns:
            Existing tool if found, None if new tool should be created
        """
        matching_tools = self.registry.find_matching_tools(query)

        if matching_tools:
            # Return best matching tool
            return matching_tools[0]

        return None
