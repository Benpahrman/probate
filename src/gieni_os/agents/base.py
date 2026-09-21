"""
Gieni OS Universal Agent Interface Contract
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAgent(ABC):
    """
    Universal interface that all autonomous agents implement.
    Defines the behavioral contract: validate -> execute -> return_result.
    """
    def __init__(self, agent_id: str, agent_name: str, version: str = "1.0.0"):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.version = version

    @abstractmethod
    def validate(self, payload: Dict[str, Any]) -> bool:
        """
        Validates input payload against expected data contract before execution.
        Must return True if valid, False or raise ValidationError if invalid.
        """
        pass

    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent's core task deterministically or cognitively.
        """
        pass

    @abstractmethod
    def return_result(self, result: Dict[str, Any]) -> None:
        """
        Publishes the result back to the Event Bus or commits to the database.
        """
        pass
