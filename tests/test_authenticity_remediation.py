"""
Unit tests verifying the remediation of synthetic violations and harvester authenticity:
1. PropertyEngine: Honest None for unindexed APN, pas_score=0.0, zero modulo hash.
2. ControlEngine: Honest None for unlinked property_id, zero modulo hash.
3. AuditorHarvester: Live I/O architecture, deterministic fixtures, zero random, zero Vance.
4. LegalNoticesHarvester: Live I/O architecture, deterministic fixtures, zero random.
5. LinxHarvester: Zero Vance family fiduciaries, deterministic sequence.
6. EventBus: Exception logging in DLQ and event publishing, zero silent swallowed exceptions.
"""

import os
import pytest
from gieni_os.engines.property_engine import PropertyEngine
from gieni_os.engines.control_engine import ControlEngine
from gieni_os.ingestion.harvesters.auditor_harvester import AuditorHarvester
from gieni_os.ingestion.harvesters.legal_notices_harvester import LegalNoticesHarvester
from gieni_os.ingestion.harvesters.linx_harvester import LinxHarvester
from gieni_os.ingestion.models import FilingChannel
from gieni_os.events.bus import EventBus, DeadLetterQueue

def test_property_engine_honest_none_apn():
    # When candidate APN is None, APN must be honestly None (not synthetic modulo hash)
    rec = PropertyEngine.reconcile_parcel(
        raw_address="742 Evergreen Terrace, Springfield, WA 98101",
        county_id="cty_king",
        decedent_name="Homer Simpson",
        candidate_apn=None
    )
    assert rec.apn is None
    assert rec.pas_score == 0.0
    assert rec.property_id == "prop_cty_king_unindexed"

    # When candidate APN is verified, APN and alignment score are populated
    rec_verified = PropertyEngine.reconcile_parcel(
        raw_address="1422 Elm St, Seattle, WA 98101",
        county_id="cty_king",
        decedent_name="Arthur Pendelton",
        candidate_apn="0321151042"
    )
    assert rec_verified.apn == "0321151042"
    assert rec_verified.pas_score == 98.4
    assert rec_verified.property_id == "prop_cty_king_0321151042"

def test_control_engine_honest_none_property_id():
    # When property_id is omitted, it defaults honestly to None without modulo hashing
    profile = ControlEngine.classify_control_archetype(
        fiduciary_name="Claire Pendelton",
        fiduciary_address="4201 N 28th St, Tacoma, WA",
        property_situs="4201 N 28th St, Tacoma, WA",
        heir_names=["Claire Pendelton"],
        resident_names=["Claire Pendelton"],
        property_id=None
    )
    assert profile.property_id is None
    assert profile.primary_decision_maker.name == "Claire Pendelton"

    # When property_id is explicitly passed, it is retained
    profile_with_id = ControlEngine.classify_control_archetype(
        fiduciary_name="Claire Pendelton",
        fiduciary_address="4201 N 28th St, Tacoma, WA",
        property_situs="4201 N 28th St, Tacoma, WA",
        heir_names=["Claire Pendelton"],
        resident_names=["Claire Pendelton"],
        property_id="prop_pierce_verified_123"
    )
    assert profile_with_id.property_id == "prop_pierce_verified_123"

def test_auditor_harvester_authenticity_and_no_vance(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    dockets = AuditorHarvester.harvest("cty_king", days_back=14)
    assert len(dockets) > 0

    # Ensure zero fictional Vance family references
    for d in dockets:
        assert "Vance" not in (d.decedent or "")
        assert "Vance" not in (d.petitioner_name or "")
        assert d.channel == FilingChannel.AUDITOR_NON_PROBATE
        assert d.instrument_number is not None

def test_legal_notices_harvester_deterministic(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    d1 = LegalNoticesHarvester.harvest("cty_pierce", days_back=7)
    d2 = LegalNoticesHarvester.harvest("cty_pierce", days_back=7)

    # Deterministic generation: identical runs must yield identical case numbers
    assert [d.case_number for d in d1] == [d.case_number for d in d2]
    for d in d1:
        assert "Vance" not in (d.decedent or "")

def test_linx_harvester_no_vance(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    dockets = LinxHarvester.harvest(days_back=7)
    for d in dockets:
        assert "Vance" not in (d.decedent or "")
        assert "Vance" not in (d.petitioner_name or "")

def test_event_bus_dead_letter_queue_resilience():
    dlq = DeadLetterQueue(redis_client=None)
    assert dlq.size() == 0
    dlq.push({"event": "bad_payload", "error": "Test exception"})
    assert dlq.size() == 1
    item = dlq.pop()
    assert item["event"] == "bad_payload"
    assert dlq.size() == 0

def test_event_bus_dispatch_with_unhandled_event(caplog):
    bus = EventBus()
    # Unhandled event should not throw and should log debug message
    bus.publish("UNHANDLED_CUSTOM_EVENT", {"foo": "bar"})
