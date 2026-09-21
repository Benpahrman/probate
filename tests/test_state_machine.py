"""
Test Suite for Gieni OS 14-Stage Opportunity State Machine
"""

import pytest
from gieni_os.lifecycle.state_machine import OpportunityStateMachine, OpportunityStage

def test_state_machine_initial_state():
    sm = OpportunityStateMachine("OPP-TEST-01")
    assert sm.current_stage == OpportunityStage.DISCOVERED
    assert len(sm.history) == 1
    assert sm.history[0]["stage"] == "DISCOVERED"

def test_state_machine_full_progression():
    sm = OpportunityStateMachine("OPP-TEST-02")
    
    stages = [
        OpportunityStage.PROPERTY_IDENTIFIED,
        OpportunityStage.OWNERSHIP_RESOLVED,
        OpportunityStage.CONTROL_MAPPED,
        OpportunityStage.AUTHORITY_RESOLVED,
        OpportunityStage.SCORED,
        OpportunityStage.QC_CERTIFIED,
        OpportunityStage.DELIVERED,
        OpportunityStage.CONTACTED,
        OpportunityStage.APPOINTMENT,
        OpportunityStage.OFFER_PRESENTED,
        OpportunityStage.CONTRACT_EXECUTED,
        OpportunityStage.CLOSED_WON,
        OpportunityStage.ARCHIVED
    ]

    for stage in stages:
        sm.transition_to(stage, context={"info": stage.value}, actor="TestWorker")
        assert sm.current_stage == stage

    assert len(sm.history) == 14
    assert sm.history[-1]["stage"] == "ARCHIVED"
    assert sm.history[-1]["actor"] == "TestWorker"
