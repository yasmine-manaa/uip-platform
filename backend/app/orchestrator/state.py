"""
State Definition for Multi-Agent Underwriting Graph (LangGraph).
Contains full execution context, agent outputs, accumulated alerts,
contradiction flags, and provisional decision.
"""

from typing import Dict, Any, List, Optional, TypedDict
from app.schemas.agent_contracts import AgentOutputContract


class UnderwritingGraphState(TypedDict, total=False):
    case_id: str
    applicant: Dict[str, Any]
    vehicle: Dict[str, Any]
    claims_summary: Dict[str, Any]
    claims_list: List[Dict[str, Any]]
    coverage_requested: str
    documents: List[Dict[str, Any]]
    area_density: int
    
    # Agent execution storage
    agent_outputs: Dict[str, Dict[str, Any]]
    execution_timeline: List[Dict[str, Any]]
    
    # Orchestrator tracking
    is_complete: bool
    missing_fields: List[str]
    contradictions: List[str]
    escalation_required: bool
    
    # Decision Engine outputs
    provisional_decision: Dict[str, Any]
