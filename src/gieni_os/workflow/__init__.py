"""
Gieni OS Workflow Package
"""

from gieni_os.workflow.engine import (
    WorkflowEngine,
    WorkflowStage,
    InvalidWorkflowTransitionError
)

def __getattr__(name: str):
    import importlib
    workflows_mod = importlib.import_module("src.gieni_os.workflows")
    if hasattr(workflows_mod, name):
        return getattr(workflows_mod, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

