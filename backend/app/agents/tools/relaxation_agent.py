"""
Constraint Relaxation Agent (Agent 3) — Infeasibility diagnosis with LLM narrative.

This agent combines:
1. The Constraint Relaxation Tool (pure Python analysis) — detects blocking
   constraints and generates fix suggestions
2. Gemini LLM — writes a human-readable summary of the diagnosis

The tool handles the heavy lifting (constraint detection, suggestion generation).
This agent just wraps it with the LLM narrative layer, following the same
pattern as the other agents (validation, insight, scenario).
"""

import os
import json
from typing import List, Dict, Optional
from backend.app.agents.tools.constraint_relaxation_tool import analyze_constraints


def generate_llm_summary(relaxation_report: Dict) -> Optional[str]:
    """
    Use Gemini to write a natural language explanation of why the plan
    is infeasible and what the user should do about it.

    Returns None if no API key is set or the LLM call fails.
    """
    google_api_key = os.getenv("GOOGLE_API_KEY", "")
    if not google_api_key:
        return None

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=google_api_key,
            temperature=0.3,
        )

        prompt = f"""You are a logistics optimization advisor helping a freight manager fix an infeasible consolidation plan.

The optimizer could not assign all shipments to vehicles. Below is the analysis of what went wrong and suggested fixes.

Write a clear, actionable summary (4-6 sentences) that:
1. Explains the root cause(s) of infeasibility in plain language
2. Prioritizes the most impactful fix(es) — what should they do FIRST
3. Gives a realistic expectation of what will improve after the fix

Feasibility Status: {"Fully infeasible" if relaxation_report.get("is_fully_infeasible") else "Partially infeasible"}
Unassigned Shipments: {relaxation_report.get("unassigned_count", 0)}

Blocking Constraints:
{json.dumps(relaxation_report.get("blocking_constraints", [])[:8], indent=2, default=str)}

Suggested Fixes:
{json.dumps(relaxation_report.get("suggestions", [])[:8], indent=2, default=str)}

Write the summary now. Be specific — use shipment IDs and numbers.
Start with the most important action item."""

        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content

    except Exception as e:
        print(f"[Relaxation Agent] LLM summary generation failed: {e}")
        return None


def run_relaxation_analysis(
    all_shipments: List[Dict],
    unassigned_shipments: List[Dict],
    vehicles: List[Dict],
    is_fully_infeasible: bool = False,
) -> Dict:
    """
    Full relaxation pipeline: constraint analysis + optional LLM summary.

    This is what the LangGraph relaxation_node calls. Runs the tool
    for structured analysis, then optionally adds an LLM narrative.

    Args:
        all_shipments: Every shipment in the input set
        unassigned_shipments: Shipments the solver couldn't assign
        vehicles: All vehicles in the fleet
        is_fully_infeasible: True if the solver found no valid plan at all

    Returns:
        Complete relaxation report with blocking_constraints, suggestions,
        summary_counts, and optionally llm_summary.
    """
    # Step 1: Run the constraint analysis tool
    report = analyze_constraints(
        all_shipments=all_shipments,
        unassigned_shipments=unassigned_shipments,
        vehicles=vehicles,
        is_fully_infeasible=is_fully_infeasible,
    )

    # Step 2: Generate LLM summary if there are issues to explain
    if report["blocking_constraints"] or report["suggestions"]:
        report["llm_summary"] = generate_llm_summary(report)
    else:
        report["llm_summary"] = None

    return report