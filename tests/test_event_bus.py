"""
Test Suite for Gieni OS Asynchronous Event Bus & Dead-Letter Queue (DLQ)
"""

import pytest
from gieni_os.events.bus import EventBus
from gieni_os.events.schemas import PropertyIdentifiedEvent

def test_event_bus_publish_subscribe():
    bus = EventBus()
    received = []

    def handler(evt):
        received.append(evt)

    bus.subscribe("Property.Identified", handler)

    event = PropertyIdentifiedEvent(
        caseId="c_101",
        propertyId="p_101",
        apn="0321151042",
        situsAddress={"street": "3719 N 28TH ST"},
        pasScore=95.0,
        assessedValue=450000.0
    )
    bus.publish(event)

    assert len(received) == 1
    assert received[0].caseId == "c_101"
    assert received[0].pasScore == 95.0

def test_event_bus_wildcard_subscription():
    bus = EventBus()
    received = []

    bus.subscribe("*", lambda e: received.append(e))

    event = PropertyIdentifiedEvent(
        caseId="c_102",
        propertyId="p_102",
        apn="0321151043",
        situsAddress={"street": "123 Main St"},
        pasScore=88.0
    )
    bus.publish(event)

    assert len(received) == 1
    assert bus.dlq.size() == 0

def test_event_bus_error_routing_to_dlq():
    bus = EventBus()

    def faulty_handler(evt):
        raise ValueError("Simulated handler crash")

    bus.subscribe("Property.Identified", faulty_handler)

    event = PropertyIdentifiedEvent(
        caseId="c_103",
        propertyId="p_103",
        apn="0321151044",
        situsAddress={"street": "Error Ave"},
        pasScore=50.0
    )
    bus.publish(event)

    assert bus.dlq.size() == 1
    item = bus.dlq.pop()
    assert "Simulated handler crash" in item["error"]
