"""
Performance Knowledge Base - Shared learning between Agent and MCP layers.
Implements bidirectional learning (Novel Feature 1).
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from models.performance import QueryType, AgentPerformance


@dataclass
class AgentLearning:
    """Knowledge learned by an agent."""
    agent_name: str
    learnings: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class MCPLearning:
    """Knowledge learned about an MCP."""
    mcp_name: str
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    preprocessing_tips: List[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CrossLayerPattern:
    """Learned pattern spanning both agent and MCP layers."""
    pattern_id: str
    description: str
    agent_name: str
    mcp_name: str
    query_type: QueryType
    success_rate: float
    discovered_at: datetime = field(default_factory=datetime.now)
    times_observed: int = 0


class PerformanceKnowledgeBase:
    """
    Central knowledge base for bidirectional learning.

    This allows:
    1. MCP layer to teach agents (e.g., "BioMCP is best for inhibitor queries")
    2. Agents to teach MCP layer (e.g., "Preprocessing improves trial ID extraction")
    3. System to discover emergent patterns (e.g., "Chemical Agent + BioMCP = 90% success")
    """

    def __init__(self):
        """Initialize the performance knowledge base."""
        self.agent_learnings: Dict[str, AgentLearning] = {}
        self.mcp_learnings: Dict[str, MCPLearning] = {}
        self.cross_layer_patterns: List[CrossLayerPattern] = []
        self.agent_performances: Dict[str, AgentPerformance] = {}

    # === Agent Learning ===

    def record_agent_learning(
        self,
        agent_name: str,
        learning: str,
        category: str = "general",
    ):
        """
        Record a learning by an agent.

        Example:
            record_agent_learning(
                "Chemical Agent",
                "BioMCP is more effective for inhibitor searches than PubChem",
                "mcp_preference"
            )
        """
        if agent_name not in self.agent_learnings:
            self.agent_learnings[agent_name] = AgentLearning(agent_name=agent_name)

        self.agent_learnings[agent_name].learnings.append(learning)
        self.agent_learnings[agent_name].updated_at = datetime.now()

        # Store in preferences if it's a preference-type learning
        if category == "mcp_preference":
            if "mcp_preferences" not in self.agent_learnings[agent_name].preferences:
                self.agent_learnings[agent_name].preferences["mcp_preferences"] = []
            self.agent_learnings[agent_name].preferences["mcp_preferences"].append(learning)

    def get_agent_learnings(self, agent_name: str) -> Optional[AgentLearning]:
        """Get all learnings for a specific agent."""
        return self.agent_learnings.get(agent_name)

    def register_agent_performance(self, agent_name: str) -> AgentPerformance:
        """Register or get agent performance tracker."""
        if agent_name not in self.agent_performances:
            self.agent_performances[agent_name] = AgentPerformance(agent_name=agent_name)
        return self.agent_performances[agent_name]

    # === MCP Learning ===

    def record_mcp_learning(
        self,
        mcp_name: str,
        learning_type: str,  # "strength", "weakness", "preprocessing"
        learning: str,
    ):
        """
        Record a learning about an MCP.

        Example:
            record_mcp_learning(
                "PubChem",
                "weakness",
                "Low success rate for inhibitor queries (20%)"
            )
        """
        if mcp_name not in self.mcp_learnings:
            self.mcp_learnings[mcp_name] = MCPLearning(mcp_name=mcp_name)

        if learning_type == "strength":
            self.mcp_learnings[mcp_name].strengths.append(learning)
        elif learning_type == "weakness":
            self.mcp_learnings[mcp_name].weaknesses.append(learning)
        elif learning_type == "preprocessing":
            self.mcp_learnings[mcp_name].preprocessing_tips.append(learning)

        self.mcp_learnings[mcp_name].updated_at = datetime.now()

    def get_mcp_learnings(self, mcp_name: str) -> Optional[MCPLearning]:
        """Get all learnings about a specific MCP."""
        return self.mcp_learnings.get(mcp_name)

    # === Cross-Layer Pattern Discovery ===

    def record_successful_pattern(
        self,
        agent_name: str,
        mcp_name: str,
        query_type: QueryType,
        success: bool,
    ):
        """
        Record a pattern observation (agent + MCP combination).
        Over time, discovers which combinations work best.
        """
        # Find existing pattern or create new one
        pattern_id = f"{agent_name}+{mcp_name}+{query_type.value}"

        existing_pattern = None
        for pattern in self.cross_layer_patterns:
            if pattern.pattern_id == pattern_id:
                existing_pattern = pattern
                break

        if existing_pattern:
            # Update existing pattern
            existing_pattern.times_observed += 1
            if success:
                # Update success rate using running average
                total_successes = existing_pattern.success_rate * (
                    existing_pattern.times_observed - 1
                )
                total_successes += 1
                existing_pattern.success_rate = total_successes / existing_pattern.times_observed
        else:
            # Create new pattern
            new_pattern = CrossLayerPattern(
                pattern_id=pattern_id,
                description=f"{agent_name} using {mcp_name} for {query_type.value}",
                agent_name=agent_name,
                mcp_name=mcp_name,
                query_type=query_type,
                success_rate=1.0 if success else 0.0,
                times_observed=1,
            )
            self.cross_layer_patterns.append(new_pattern)

    def get_best_pattern_for_agent(
        self,
        agent_name: str,
        query_type: QueryType,
    ) -> Optional[CrossLayerPattern]:
        """
        Get the best-performing MCP for an agent+query_type combination.
        This is emergent intelligence - learned through experience.
        """
        matching_patterns = [
            p for p in self.cross_layer_patterns
            if p.agent_name == agent_name and p.query_type == query_type
        ]

        if not matching_patterns:
            return None

        # Return pattern with highest success rate (minimum 3 observations)
        valid_patterns = [p for p in matching_patterns if p.times_observed >= 3]
        if not valid_patterns:
            return None

        return max(valid_patterns, key=lambda p: p.success_rate)

    # === Bidirectional Feedback ===

    def generate_mcp_to_agent_feedback(
        self,
        mcp_performance_insights: Dict[str, Any],
    ) -> List[str]:
        """
        Generate feedback from MCP layer to agents.
        MCP layer teaches agents which MCPs work best.
        """
        feedback = []

        # Extract recommendations from MCP performance
        if "query_type_recommendations" in mcp_performance_insights:
            for query_type, rec in mcp_performance_insights["query_type_recommendations"].items():
                feedback.append(
                    f"For {query_type} queries, {rec['best_mcp']} has "
                    f"{rec['success_rate']*100:.1f}% success rate "
                    f"(avg {rec['avg_time']:.2f}s)"
                )

        return feedback

    def generate_agent_to_mcp_feedback(
        self,
        agent_name: str,
    ) -> Dict[str, List[str]]:
        """
        Generate feedback from agent to MCP layer.
        Agent shares what preprocessing or patterns help.
        """
        feedback = {
            "preprocessing_suggestions": [],
            "usage_patterns": [],
        }

        agent_learning = self.get_agent_learnings(agent_name)
        if agent_learning:
            # Share preprocessing insights
            if "preprocessing" in agent_learning.preferences:
                feedback["preprocessing_suggestions"] = agent_learning.preferences["preprocessing"]

        return feedback

    # === Summary & Dashboard ===

    def get_learning_summary(self) -> Dict[str, Any]:
        """
        Get summary of all learnings for dashboard display.
        """
        return {
            "agents": {
                name: {
                    "total_learnings": len(learning.learnings),
                    "recent_learnings": learning.learnings[-5:],
                    "last_updated": learning.updated_at.isoformat(),
                }
                for name, learning in self.agent_learnings.items()
            },
            "mcps": {
                name: {
                    "strengths": len(learning.strengths),
                    "weaknesses": len(learning.weaknesses),
                    "preprocessing_tips": len(learning.preprocessing_tips),
                }
                for name, learning in self.mcp_learnings.items()
            },
            "patterns": {
                "total_patterns": len(self.cross_layer_patterns),
                "high_performing": len([
                    p for p in self.cross_layer_patterns
                    if p.success_rate > 0.8 and p.times_observed >= 5
                ]),
            },
        }

    def get_insights(self) -> List[str]:
        """
        Get human-readable insights from learned patterns.
        These can be shown to users to demonstrate learning.
        """
        insights = []

        # High-performing patterns
        high_perf = [
            p for p in self.cross_layer_patterns
            if p.success_rate > 0.85 and p.times_observed >= 5
        ]
        for pattern in high_perf[:5]:  # Top 5
            insights.append(
                f"✓ {pattern.agent_name} + {pattern.mcp_name} achieves "
                f"{pattern.success_rate*100:.0f}% success for {pattern.query_type.value} queries"
            )

        # MCP strengths
        for mcp_name, learning in self.mcp_learnings.items():
            if learning.strengths:
                insights.append(f"✓ {mcp_name}: {learning.strengths[0]}")

        return insights
