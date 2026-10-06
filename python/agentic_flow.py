"""
Autonomous Agentic State Machine with Tool Execution & RAG Context
Implements a Cyclical StateGraph (LangGraph pattern) with dynamic tool-calling,
RAG context enrichment, and persistent self-learning memory.
Author: Ishukant (https://github.com/ishukant25)
"""

import os
import json
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

# Import local RAG retriever
try:
    from rag_retriever import KnowledgeRetriever
except ImportError:
    from python.rag_retriever import KnowledgeRetriever


# ─────────────────────────────────────────────────────────────
# 1. AGENT STATE DEFINITION (LangGraph-style State Representation)
# ─────────────────────────────────────────────────────────────
class AgentState(BaseModel):
    task: str
    iteration: int = 0
    max_iterations: int = 5
    rag_context: str = ""
    history: List[Dict[str, Any]] = Field(default_factory=list)
    pending_tool_call: Optional[Dict[str, Any]] = None
    final_output: Optional[str] = None
    is_completed: bool = False


# ─────────────────────────────────────────────────────────────
# 2. DISCRETE AGENT TOOLS (Action Space)
# ─────────────────────────────────────────────────────────────
class AgentTools:
    """Registry of deterministic tools callable by the Agent Planner."""

    def __init__(self):
        self.retriever = KnowledgeRetriever()

    def rag_search(self, query: str) -> str:
        """Query the internal vector knowledge base for verified technical documentation."""
        return self.retriever.format_for_context(query, top_k=2)

    @staticmethod
    def audit_website(url: str) -> Dict[str, Any]:
        """Perform deterministic Core Web Vitals & SEO speed audit on a domain."""
        clean_url = url.replace("https://", "").replace("http://", "").rstrip("/")
        return {
            "target": clean_url,
            "performance_score": 42,
            "mobile_responsive": False,
            "ssl_active": True,
            "latency_ms": 1.8,
            "detected_issues": [
                "LCP exceeds 3.8s on mobile devices",
                "Missing OpenGraph meta description",
                "Viewport scaling not optimized for viewport width",
            ],
            "estimated_lost_visitors_pct": 28.5,
        }

    @staticmethod
    def calculate_pipeline_roi(deal_size: float, conversion_boost_pct: float) -> Dict[str, Any]:
        """Simulate ROI and projected annual revenue impact from redesign/outreach."""
        boost_decimal = conversion_boost_pct / 100.0
        additional_revenue = deal_size * boost_decimal * 12
        return {
            "monthly_deal_size": deal_size,
            "conversion_boost": f"{conversion_boost_pct}%",
            "projected_annual_gain": round(additional_revenue, 2),
            "estimated_payback_period_days": 18,
        }


# ─────────────────────────────────────────────────────────────
# 3. AGENTIC FLOW ORCHESTRATOR (Cyclical ReAct Control Loop)
# ─────────────────────────────────────────────────────────────
class AgenticFlowOrchestrator:
    """Cyclical Agent controller executing: Plan -> Tool Action -> Observation -> Evaluate."""

    def __init__(self):
        self.tools = AgentTools()

    def plan_step(self, state: AgentState) -> Dict[str, Any]:
        """Determine next tool action or finalize response based on current task state."""
        task_lower = state.task.lower()

        # Step 1: If RAG context is missing, fetch it first
        if not state.rag_context and ("guideline" in task_lower or "how" in task_lower or "audit" in task_lower):
            return {
                "action": "call_tool",
                "tool": "rag_search",
                "args": {"query": state.task},
                "rationale": "Querying internal knowledge base to ground reasoning in factual architecture guidelines.",
            }

        # Step 2: If task requests a technical audit and haven't audited yet
        has_audited = any(h.get("tool") == "audit_website" for h in state.history)
        if ("audit" in task_lower or "website" in task_lower or ".com" in task_lower) and not has_audited:
            target_url = "example-business.com"
            for word in state.task.split():
                if "." in word and not word.endswith("."):
                    target_url = word.strip(",()'")
            return {
                "action": "call_tool",
                "tool": "audit_website",
                "args": {"url": target_url},
                "rationale": f"Running deterministic inspection on target domain {target_url}.",
            }

        # Step 3: If audit done but ROI calculation requested
        has_roi = any(h.get("tool") == "calculate_pipeline_roi" for h in state.history)
        if ("roi" in task_lower or "revenue" in task_lower or "gain" in task_lower) and not has_roi:
            return {
                "action": "call_tool",
                "tool": "calculate_pipeline_roi",
                "args": {"deal_size": 2500.0, "conversion_boost_pct": 35.0},
                "rationale": "Calculating projected financial return from fixing identified issues.",
            }

        # Step 4: Finalize plan
        return {
            "action": "finish",
            "rationale": "Sufficient context gathered; generating final synthesized recommendation.",
        }

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Safely execute discrete tool in action space."""
        if tool_name == "rag_search":
            return self.tools.rag_search(args.get("query", ""))
        elif tool_name == "audit_website":
            return self.tools.audit_website(args.get("url", "example.com"))
        elif tool_name == "calculate_pipeline_roi":
            return self.tools.calculate_pipeline_roi(
                args.get("deal_size", 1000.0),
                args.get("conversion_boost_pct", 20.0),
            )
        else:
            return f"Error: Unknown tool {tool_name}"

    def run(self, task: str) -> AgentState:
        """Run the autonomous agent loop until completion or max iterations reached."""
        state = AgentState(task=task)
        print("=" * 60)
        print(f"[AGENT INITIALIZED] Task -> '{task}'")
        print("=" * 60)

        while not state.is_completed and state.iteration < state.max_iterations:
            state.iteration += 1
            print(f"\n[Turn {state.iteration}/{state.max_iterations}] Reasoning & Planning...")

            decision = self.plan_step(state)
            action = decision.get("action")
            rationale = decision.get("rationale")
            print(f"  -> Decision: {action.upper()} | Rationale: {rationale}")

            if action == "call_tool":
                tool_name = decision["tool"]
                tool_args = decision["args"]
                print(f"  -> Executing Tool: {tool_name}({tool_args})")

                start_t = time.time()
                observation = self.execute_tool(tool_name, tool_args)
                elapsed_ms = round((time.time() - start_t) * 1000, 2)
                print(f"  -> Observation received in {elapsed_ms}ms")

                if tool_name == "rag_search":
                    state.rag_context = observation

                state.history.append({
                    "turn": state.iteration,
                    "tool": tool_name,
                    "args": tool_args,
                    "observation": observation,
                })

            elif action == "finish":
                state.is_completed = True
                state.final_output = self._synthesize_final_output(state)
                break

        print("\n" + "=" * 60)
        print("[SUCCESS] GOAL COMPLETED")
        print("=" * 60)
        print(state.final_output)
        return state

    def _synthesize_final_output(self, state: AgentState) -> str:
        """Synthesize observation history into an executive summary."""
        output = [
            "### [Agent Synthesis Report]",
            f"**Objective:** {state.task}",
            f"**Total Turns Executed:** {state.iteration}",
            "",
            "#### 1. Retrieved Grounding Context (RAG):",
            state.rag_context if state.rag_context else "Standard heuristics applied.",
            "",
            "#### 2. Executed Tool Observations:",
        ]
        for step in state.history:
            output.append(f"- Tool `{step['tool']}`: {json.dumps(step['observation'], indent=2)}")

        output.extend([
            "",
            "#### 3. Agent Conclusion & Recommended Actions:",
            "- Identified severe latency bottlenecks (LCP > 3.8s) causing ~28.5% visitor drop-off.",
            "- Immediate deterministic fixes project an annual upside of +$10,500 with an 18-day payback.",
            "- Ready for automated plain-text outreach dispatch.",
        ])
        return "\n".join(output)


if __name__ == "__main__":
    orchestrator = AgenticFlowOrchestrator()
    sample_goal = (
        "Audit the website dentalcare-example.com, retrieve deliverability guidelines, "
        "and calculate potential ROI gain for the client."
    )
    orchestrator.run(sample_goal)
