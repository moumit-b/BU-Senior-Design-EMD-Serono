"""
Demonstration of Dual Orchestration with Novel Features

This script demonstrates:
1. Bidirectional Learning (MCP <-> Agent feedback)
2. Dynamic Tool Composition (agents create new tools)
3. Research Session Memory (multi-turn context)

Run this to see the dual orchestration in action!
"""

import asyncio
from typing import Dict, Any

# Import orchestration components
from orchestration.mcp_orchestrator import MCPOrchestrator
from orchestration.agent_orchestrator import AgentOrchestrator
from orchestration.performance_kb import PerformanceKnowledgeBase
from orchestration.tool_composer import ToolComposer
from orchestration.session_manager import SessionManager
from models.performance import PerformanceMetrics, QueryType
from models.entities import Drug, Gene, EntityType
from models.session import InsightType, HypothesisStatus


class DualOrchestrationDemo:
    """
    Demonstrates the dual orchestration system with novel features.
    """

    def __init__(self):
        """Initialize the demonstration."""
        print("=" * 80)
        print("DUAL ORCHESTRATION SYSTEM - DEMONSTRATION")
        print("=" * 80)
        print()
        print("NOTE: This is a simulated demonstration of the architecture.")
        print("      Real MCP server integration requires additional setup.")
        print()

        # Initialize components (with empty/mock MCP wrappers for demo)
        self.mcp_orchestrator = MCPOrchestrator(mcp_wrappers={})
        self.performance_kb = PerformanceKnowledgeBase()
        self.tool_composer = ToolComposer(self.mcp_orchestrator)
        self.session_manager = SessionManager()

        print("[OK] MCP Orchestrator initialized (with caching & monitoring)")
        print("[OK] Performance Knowledge Base initialized (bidirectional learning)")
        print("[OK] Tool Composer initialized (dynamic tool creation)")
        print("[OK] Session Manager initialized (research memory)")
        print()

    def demo_1_bidirectional_learning(self):
        """Demonstrate Novel Feature 1: Bidirectional Learning."""
        print("-" * 80)
        print("DEMO 1: BIDIRECTIONAL LEARNING")
        print("MCP layer teaches agents, Agents teach MCP layer")
        print("-" * 80)
        print()

        # Simulate MCP performance data
        print("Simulating MCP performance tracking...")
        print()
        print("Scenario: Agent tries to find 'BRCA1 inhibitors'")
        print("  - PubChem: Failed (0% success rate, 2.1s)")
        print("  - BioMCP: Succeeded (100% success rate, 1.45s avg)")
        print()

        # MCP -> Agent Learning
        print("MCP Layer -> Agent Learning:")
        print("  The MCP Orchestrator tracks these patterns and learns:")
        print("  - For 'inhibitor_search' queries: Use BioMCP")
        print("    (Success: 100%, Time: 1.45s)")
        print("  - PubChem is not optimal for inhibitor searches")
        print()
        print("  This feedback is sent to the Agent Layer...")
        print()

        # Record agent learning
        self.performance_kb.record_agent_learning(
            agent_name="Chemical Agent",
            learning="Learned that BioMCP is superior for inhibitor searches",
            category="mcp_preference",
        )

        print("Chemical Agent learned:")
        agent_learning = self.performance_kb.get_agent_learnings("Chemical Agent")
        for learning in agent_learning.learnings:
            print(f"  - {learning}")

        print()

        # Agent -> MCP Learning
        print("Agent -> MCP Layer Learning:")
        self.performance_kb.record_mcp_learning(
            mcp_name="BioMCP",
            learning_type="strength",
            learning="Excellent for inhibitor and drug discovery queries",
        )

        mcp_learning = self.performance_kb.get_mcp_learnings("BioMCP")
        print(f"  - BioMCP Strengths:")
        for strength in mcp_learning.strengths:
            print(f"    - {strength}")

        print()

        # Cross-layer pattern discovery
        print("Cross-Layer Pattern Discovery:")
        self.performance_kb.record_successful_pattern(
            agent_name="Chemical Agent",
            mcp_name="BioMCP",
            query_type=QueryType.INHIBITOR_SEARCH,
            success=True,
        )
        self.performance_kb.record_successful_pattern(
            agent_name="Chemical Agent",
            mcp_name="BioMCP",
            query_type=QueryType.INHIBITOR_SEARCH,
            success=True,
        )

        pattern = self.performance_kb.get_best_pattern_for_agent(
            agent_name="Chemical Agent",
            query_type=QueryType.INHIBITOR_SEARCH,
        )

        if pattern:
            print(f"  - Discovered pattern: {pattern.description}")
            print(f"    Success rate: {pattern.success_rate*100:.0f}% ({pattern.times_observed} observations)")

        print()

    def demo_2_tool_composition(self):
        """Demonstrate Novel Feature 2: Dynamic Tool Composition."""
        print("-" * 80)
        print("DEMO 2: DYNAMIC TOOL COMPOSITION")
        print("Agents create new tools by composing MCP workflows")
        print("-" * 80)
        print()

        print("Scenario: Agent needs to compare drug safety profiles")
        print("Creating composed tool: 'compare_drug_safety_profiles'")
        print()

        # Create a composed tool
        tool = self.tool_composer.create_composed_tool(
            name="compare_drug_safety_profiles",
            description="Compare multiple drugs by efficacy and safety data",
            creator_agent="Chemical Agent",
            tags=["drug", "safety", "comparison"],
            steps=[
                {
                    "mcp": "PubChem",
                    "tool": "search_compounds_by_name",
                    "input": {"name": "${user.drug_name}"},
                },
                {
                    "mcp": "BioMCP",
                    "tool": "find_similar_compounds",
                    "input": {"smiles": "${step1.smiles}"},
                },
                {
                    "mcp": "Literature",
                    "tool": "search_adverse_events",
                    "input": {"compounds": "${step2.compounds}"},
                },
            ],
        )

        print(f"[OK] Created composed tool: '{tool.name}'")
        print(f"  Creator: {tool.created_by}")
        print(f"  Steps: {len(tool.steps)}")
        for i, step in enumerate(tool.steps, 1):
            print(f"    {i}. {step.mcp_name}.{step.tool_name}")

        print()

        # Simulate tool usage
        print("Simulating tool reuse in future queries...")
        tool.record_execution(success=True, execution_time=8.5)
        tool.record_execution(success=True, execution_time=7.2)
        tool.record_execution(success=True, execution_time=6.8)

        print(f"  - Tool used {tool.times_used} times")
        print(f"  - Success rate: {tool.success_rate*100:.0f}%")
        print(f"  - Avg execution time: {tool.avg_execution_time:.2f}s")
        print()

        # Find matching tool for similar query
        print("Later, user asks: 'Compare ibuprofen safety to alternatives'")
        matching_tool = self.tool_composer.get_tool_or_suggest(
            "Compare ibuprofen safety to alternatives"
        )

        if matching_tool:
            print(f"[OK] Found existing composed tool: '{matching_tool.name}'")
            print(f"  -> Reusing tool instead of creating new workflow")
            print(f"  -> Estimated time savings: 50%+")
        else:
            print("  No matching tool found - would create new one")

        print()

        # Show registry stats
        stats = self.tool_composer.registry.get_stats()
        print("Tool Composition Registry Stats:")
        print(f"  - Total tools: {stats['total_tools']}")
        print(f"  - Total uses: {stats['total_uses']}")
        print(f"  - Avg success rate: {stats['avg_success_rate']*100:.0f}%")

        print()

    def demo_3_research_session_memory(self):
        """Demonstrate Novel Feature 8: Research Session Memory."""
        print("-" * 80)
        print("DEMO 3: RESEARCH SESSION MEMORY")
        print("Multi-turn collaborative research with context")
        print("-" * 80)
        print()

        # Create session
        user_id = "researcher_001"
        session = self.session_manager.create_session(
            user_id=user_id,
            research_goal="Find BRCA1-targeting drugs for breast cancer treatment",
        )

        print(f"[OK] Created research session: {session.session_id[:8]}...")
        print(f"  Research goal: {session.research_goal}")
        print()

        # Turn 1: Initial query
        print("TURN 1: User asks 'What is BRCA1?'")
        query1 = self.session_manager.add_query_to_session(
            session.session_id,
            "What is BRCA1?",
        )

        # Add entities discovered
        brca1_gene = Gene(
            entity_id="gene_brca1",
            name="BRCA1",
            gene_symbol="BRCA1",
            function="DNA repair, tumor suppressor",
            associated_diseases=["Breast cancer", "Ovarian cancer"],
        )

        self.session_manager.add_entity_to_session(
            session.session_id,
            brca1_gene,
        )

        print(f"  [OK] Discovered entity: {brca1_gene.name} (Gene)")
        print(f"    Function: {brca1_gene.function}")
        print()

        # Turn 2: Follow-up query
        print("TURN 2: User asks 'Find drugs targeting BRCA1' (builds on context)")
        query2 = self.session_manager.add_query_to_session(
            session.session_id,
            "Find drugs targeting BRCA1",
            parent_query_id=query1.query_id,
        )

        # Add drugs discovered
        olaparib = Drug(
            entity_id="drug_olaparib",
            name="Olaparib",
            brand_names=["Lynparza"],
            indication="BRCA-mutated breast/ovarian cancer",
            mechanism_of_action="PARP inhibitor",
            development_stage="Approved",
        )

        self.session_manager.add_entity_to_session(
            session.session_id,
            olaparib,
        )

        print(f"  [OK] System knows context: Looking for drugs related to {brca1_gene.name}")
        print(f"  [OK] Discovered entity: {olaparib.name} (Drug)")
        print(f"    Mechanism: {olaparib.mechanism_of_action}")
        print()

        # Add hypothesis
        hypothesis = self.session_manager.add_hypothesis_to_session(
            session.session_id,
            statement="PARP inhibitors are effective for BRCA1-mutated cancers",
            proposed_by="Literature Agent",
            confidence=0.85,
            related_entities=["gene_brca1", "drug_olaparib"],
        )

        print(f"  [OK] System formed hypothesis:")
        print(f"    '{hypothesis.statement}'")
        print(f"    Confidence: {hypothesis.confidence*100:.0f}%")
        print()

        # Add insight
        insight = self.session_manager.add_insight_to_session(
            session.session_id,
            insight_type=InsightType.PATTERN_DETECTED,
            description="Multiple PARP inhibitors in clinical development for BRCA mutations",
            discovered_by="Clinical Agent",
            confidence=0.9,
        )

        print(f"  [OK] System discovered insight:")
        print(f"    {insight.description}")
        print()

        # Proactive suggestions
        suggestions = self.session_manager.suggest_next_steps(session.session_id)
        print("  [IDEA] Proactive suggestions for next steps:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"    {i}. {suggestion}")

        print()

        # Turn 3: Week later
        print("TURN 3: One week later, user returns to session")
        print()

        # Get session summary
        summary = self.session_manager.generate_session_summary(session.session_id)

        print("  Session Summary:")
        print(f"    - Duration: {summary['duration_hours']:.1f} hours")
        print(f"    - Total queries: {summary['total_queries']}")
        print(f"    - Entities discovered: {summary['entities_discovered']}")
        print(f"    - Hypotheses formed: {summary['hypotheses_formed']}")
        print(f"    - Active hypotheses: {summary['active_hypotheses']}")
        print()

        print("  Key Entities:")
        for entity in summary["key_entities"]:
            print(f"    - {entity['name']} ({entity['type']})")

        print()

        print("  Active Hypotheses:")
        for hyp in summary["active_hypotheses"]:
            print(f"    - {hyp['statement']}")
            print(f"      Status: {hyp['status']}, Confidence: {hyp['confidence']*100:.0f}%")

        print()

    def demo_summary(self):
        """Show overall system status and insights."""
        print("-" * 80)
        print("SYSTEM STATUS & INSIGHTS")
        print("-" * 80)
        print()

        # Performance KB summary
        print("Performance Knowledge Base:")
        kb_summary = self.performance_kb.get_learning_summary()

        print(f"  Agents with learnings: {len(kb_summary['agents'])}")
        for agent_name, data in kb_summary['agents'].items():
            print(f"    - {agent_name}: {data['total_learnings']} learnings")

        print(f"  MCPs with learnings: {len(kb_summary['mcps'])}")

        print(f"  Cross-layer patterns: {kb_summary['patterns']['total_patterns']}")
        print(f"    High-performing: {kb_summary['patterns']['high_performing']}")

        print()

        # Insights
        insights = self.performance_kb.get_insights()
        if insights:
            print("Key Insights:")
            for insight in insights:
                print(f"  {insight}")

        print()

        # Session stats
        print("Session Manager:")
        session_stats = self.session_manager.get_session_statistics()
        print(f"  Total sessions: {session_stats['total_sessions']}")
        print(f"  Total queries: {session_stats['total_queries']}")
        print(f"  Total entities discovered: {session_stats['total_entities']}")
        print(f"  Total hypotheses: {session_stats['total_hypotheses']}")

        print()

        # MCP stats
        print("MCP Orchestrator:")
        mcp_stats = self.mcp_orchestrator.get_stats_dashboard()
        print(f"  Total calls: {mcp_stats['overall']['total_calls']}")
        print(f"  Success rate: {mcp_stats['overall']['success_rate']*100:.0f}%")

        if mcp_stats['overall']['cache_stats']:
            cache = mcp_stats['overall']['cache_stats']
            print(f"  Cache hit rate: {cache['hit_rate']*100:.0f}%")
            print(f"  Cache size: {cache['size']}/{cache['max_size']}")

        print()

    def run(self):
        """Run the full demonstration."""
        print()
        print("This demonstration showcases three novel features:")
        print("  1. Bidirectional Learning (Agents <-> MCPs teach each other)")
        print("  2. Dynamic Tool Composition (Agents create reusable workflows)")
        print("  3. Research Session Memory (Context across multiple turns)")
        print()
        input("Press Enter to begin demonstration...")
        print()

        self.demo_1_bidirectional_learning()
        input("\nPress Enter to continue to Demo 2...")
        print()

        self.demo_2_tool_composition()
        input("\nPress Enter to continue to Demo 3...")
        print()

        self.demo_3_research_session_memory()
        input("\nPress Enter to view system summary...")
        print()

        self.demo_summary()

        print()
        print("=" * 80)
        print("DEMONSTRATION COMPLETE")
        print("=" * 80)
        print()
        print("What you've seen:")
        print("  [OK] MCP layer learning which tools work best for which queries")
        print("  [OK] Agents learning from MCP performance feedback")
        print("  [OK] Emergent patterns discovered across agent+MCP combinations")
        print("  [OK] Agents creating composed tools that can be reused")
        print("  [OK] Tool composition saving time on repeated workflows")
        print("  [OK] Research sessions maintaining context across multiple turns")
        print("  [OK] System forming hypotheses and providing proactive suggestions")
        print()
        print("This is the foundation for ambitious capabilities:")
        print("  -> Hypothesis formation & testing")
        print("  -> Adversarial cross-validation")
        print("  -> Autonomous research workflows")
        print("  -> True collaborative research intelligence")
        print()


def main():
    """Run the demonstration."""
    demo = DualOrchestrationDemo()
    demo.run()


if __name__ == "__main__":
    main()
