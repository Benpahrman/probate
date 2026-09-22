"""
Gieni OS - Automated Opportunity Ingestion & Notion Sync Engine
==============================================================
This tool ingests raw/pre-processed probate case records, computes
Gieni Decision Intelligence scores (Authority, Ownership, Equity, Control),
and automatically creates decision-ready Opportunity Files in Notion.
"""

import requests
import json
import time
import argparse
import sys
import os

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
OPPORTUNITIES_DB_ID = '3e0b5bd1-d90c-81e6-bb4d-c1bc60166a40'
COUNTIES_DB_ID = '3e0b5bd1-d90c-8105-b6fd-ef9a8371d96b'
CLIENTS_DB_ID = '3e0b5bd1-d90c-810e-a326-de5677c60e18'

class GieniOpportunityEngine:
    def __init__(self, token=NOTION_TOKEN):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }

    @staticmethod
    def _score_authority(case_data: dict) -> int:
        if case_data.get('has_nonintervention_powers'):
            return 35
        if case_data.get('petition_filed_no_dispute'):
            return 20
        return 5

    @staticmethod
    def _score_equity(case_data: dict) -> int:
        ltv = case_data.get('estimated_ltv', 0.0)
        if ltv == 0.0:
            return 25
        if ltv < 0.40:
            return 20
        if ltv < 0.70:
            return 10
        return 0

    @staticmethod
    def _score_control(case_data: dict) -> int:
        num_heirs = case_data.get('heir_count', 1)
        if num_heirs == 1:
            return 25
        if num_heirs <= 3 and case_data.get('heirs_cooperative', True):
            return 18
        return 5

    @staticmethod
    def _score_occupancy(case_data: dict) -> int:
        occupancy = case_data.get('occupancy', 'vacant').lower()
        if occupancy == 'vacant':
            return 15
        if occupancy == 'tenant':
            return 8
        return 5

    @staticmethod
    def _determine_priority(score: int) -> str:
        if score >= 85:
            return "Priority A"
        if score >= 65:
            return "Priority B"
        if score >= 45:
            return "Priority C"
        return "Disqualified"

    def calculate_score(self, case_data):
        """
        Calculates the Gieni Opportunity Score (0 - 100)
        based on Authority, Equity, Control, and Condition.
        """
        score = (
            self._score_authority(case_data)
            + self._score_equity(case_data)
            + self._score_control(case_data)
            + self._score_occupancy(case_data)
        )
        priority = self._determine_priority(score)
        return score, priority

    def create_opportunity(self, data, county_id=None, client_id=None):
        score, priority = self.calculate_score(data)
        
        qc_status = "Passed" if priority != "Disqualified" else "Failed"
        stage = "Approved" if priority in ["Priority A", "Priority B"] else "Rejected"
        if data.get("is_delivered"):
            stage = "Delivered"

        title = f"{data['opp_id']} | {data['address']}"

        properties = {
            "Opportunity ID": {"title": [{"text": {"content": title}}]},
            "Probate Case Number": {"rich_text": [{"text": {"content": data.get('case_number', '')}}]},
            "Decedent or Estate": {"rich_text": [{"text": {"content": data.get('estate_name', '')}}]},
            "Property Address": {"rich_text": [{"text": {"content": data.get('address', '')}}]},
            "Workflow Stage": {"select": {"name": stage}},
            "Date Received": {"date": {"start": data.get('date_received', time.strftime('%Y-%m-%d'))}},
            "Priority": {"select": {"name": priority}},
            "Score": {"number": score},
            "Property Match Status": {"select": {"name": "Confirmed" if qc_status == "Passed" else "Rejected"}},
            "Ownership Status": {"select": {"name": "Resolved" if qc_status == "Passed" else "Complex"}},
            "Ownership Complexity": {"select": {"name": "Low" if data.get('heir_count', 1) == 1 else "Medium"}},
            "Authority Classification": {"select": {"name": data.get('authority_class', 'Confirmed Authority')}},
            "Authority Confidence": {"select": {"name": "High" if data.get('has_nonintervention_powers') else "Medium"}},
            "Decision Maker": {"rich_text": [{"text": {"content": data.get('decision_maker', '')}}]},
            "Contact Readiness": {"select": {"name": "Ready" if qc_status == "Passed" else "Do Not Contact"}},
            "Contact Outcome": {"select": {"name": data.get('contact_outcome', 'Not Attempted')}},
            "QC Status": {"select": {"name": qc_status}},
            "Research Time": {"number": data.get('research_time_minutes', 15)},
            "Direct Cost": {"number": data.get('direct_cost_dollars', 10.0)},
            "Notes": {"rich_text": [{"text": {"content": data.get('summary_notes', '')}}]}
        }

        if county_id:
            properties["County"] = {"relation": [{"id": county_id}]}
        if client_id:
            properties["Client"] = {"relation": [{"id": client_id}]}
        if data.get("date_delivered"):
            properties["Date Delivered"] = {"date": {"start": data["date_delivered"]}}

        payload = {
            "parent": {"database_id": OPPORTUNITIES_DB_ID},
            "properties": properties
        }

        resp = requests.post("https://api.notion.com/v1/pages", headers=self.headers, json=payload)
        if resp.status_code == 200:
            page_id = resp.json()["id"]
            print(f"[SUCCESS] Opportunity created: {title} (ID: {page_id})")
            return page_id
        else:
            print(f"[ERROR] Failed creating {title}: {resp.status_code} - {resp.text}")
            return None

def main():
    parser = argparse.ArgumentParser(description="Gieni OS Opportunity Ingestion")
    parser.add_argument("--test", action="store_true", help="Run self-test calculation")
    args = parser.parse_args()

    engine = GieniOpportunityEngine()
    if args.test:
        sample_case = {
            "opp_id": "TEST-001",
            "address": "123 Test St, Tacoma, WA",
            "has_nonintervention_powers": True,
            "estimated_ltv": 0.0,
            "heir_count": 1,
            "occupancy": "vacant"
        }
        score, prio = engine.calculate_score(sample_case)
        print(f"Self-Test Result: Score={score}, Priority={prio} (Expected: Score=100, Priority=Priority A)")

if __name__ == "__main__":
    main()
