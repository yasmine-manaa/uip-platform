"""
Base Specialized Agent Class.
Defines execution interface and standard audit hooks.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from app.schemas.agent_contracts import AgentOutputContract


class BaseSpecializedAgent(ABC):
    def __init__(self, agent_id: str, agent_name: str, version: str = "1.0.0"):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.version = version

    @abstractmethod
    def execute(self, case_context: Dict[str, Any]) -> AgentOutputContract:
        """
        Executes agent logic on the unified case context and returns standard output contract.
        """
        pass
