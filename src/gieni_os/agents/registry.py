"""
Gieni OS Agent Registry
Tracks registered agents, versioning, operational status, and health heartbeats.
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from gieni_os.database.models import AgentRegistryModel

class AgentRegistry:
    @staticmethod
    def register_agent(
        db: Session,
        agent_id: str,
        agent_name: str,
        version: str = "1.0.0",
        capabilities: Optional[str] = None,
        status: str = "ONLINE"
    ) -> AgentRegistryModel:
        agent = db.query(AgentRegistryModel).filter(AgentRegistryModel.id == agent_id).first()
        now = datetime.now(timezone.utc)
        if agent:
            agent.agent_name = agent_name
            agent.version = version
            agent.status = status
            agent.capabilities = capabilities
            agent.last_heartbeat = now
        else:
            agent = AgentRegistryModel(
                id=agent_id,
                agent_name=agent_name,
                version=version,
                capabilities=capabilities,
                status=status,
                last_heartbeat=now
            )
            db.add(agent)
        
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def heartbeat(db: Session, agent_id: str) -> bool:
        agent = db.query(AgentRegistryModel).filter(AgentRegistryModel.id == agent_id).first()
        if agent:
            agent.last_heartbeat = datetime.now(timezone.utc)
            agent.status = "ONLINE"
            db.commit()
            return True
        return False

    @staticmethod
    def list_agents(db: Session) -> List[AgentRegistryModel]:
        return db.query(AgentRegistryModel).all()
