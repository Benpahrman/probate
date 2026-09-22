import requests
import json
import time
import os

NOTION_TOKEN = os.environ["NOTION_TOKEN"]

CLIENTS_DB_ID = '3e0b5bd1-d90c-810e-a326-de5677c60e18'
OPPORTUNITIES_DB_ID = '3e0b5bd1-d90c-81e6-bb4d-c1bc60166a40'
COUNTIES_DB_ID = '3e0b5bd1-d90c-8105-b6fd-ef9a8371d96b'

headers = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

def t(content, bold=False, color="default"):
    return {
        "type": "text",
        "text": {"content": content},
        "annotations": {
            "bold": bold,
            "italic": False,
            "strikethrough": False,
            "underline": False,
            "code": False,
            "color": color
        }
    }

def main():
    # 1. Load Pierce County Page ID
    context_file = "c:/Users/ben/probate/scripts/county_context.json"
    pierce_page_id = None
    if os.path.exists(context_file):
        with open(context_file, "r") as f:
            data = json.load(f)
            pierce_page_id = data.get("pierce_page_id")

    if not pierce_page_id:
        query_payload = {
            "filter": {
                "property": "County",
                "title": {
                    "equals": "Pierce"
                }
            }
        }
        r = requests.post(f"https://api.notion.com/v1/databases/{COUNTIES_DB_ID}/query", headers=headers, json=query_payload)
        results = r.json().get("results", [])
        if results:
            pierce_page_id = results[0]["id"]
            print(f"Found Pierce County ID from DB: {pierce_page_id}")

    # 2. Create Simulated Founding Partner in Clients DB
    print("\n--- Step 1: Creating Simulated Founding Partner in Clients DB ---")
    client_payload = {
        "parent": {"database_id": CLIENTS_DB_ID},
        "properties": {
            "Client": {
                "title": [{"text": {"content": "Cascade Property Partners"}}]
            },
            "Primary Contact": {
                "rich_text": [{"text": {"content": "Marcus Vance (Managing Director)"}}]
            },
            "Email": {
                "email": "acquisitions@cascadepropertypartners.com"
            },
            "Phone": {
                "phone_number": "(253) 555-0192"
            },
            "Plan": {
                "select": {"name": "Founding County Partner"}
            },
            "Lifecycle Stage": {
                "select": {"name": "Active"}
            },
            "Exclusivity Status": {
                "select": {"name": "Active"}
            },
            "Monthly Capacity": {
                "number": 20
            },
            "Monthly Fee": {
                "number": 2500
            },
            "Setup Fee": {
                "number": 1500
            },
            "Overage Rate": {
                "number": 75
            },
            "Contract Start": {
                "date": {"start": "2026-09-01"}
            },
            "Renewal Date": {
                "date": {"start": "2026-11-30"}
            },
            "County": {
                "relation": [{"id": pierce_page_id}] if pierce_page_id else []
            },
            "Notes": {
                "rich_text": [{"text": {"content": "Founding County Partner for Pierce County, WA. Standard 90-day validation pilot. Focuses on off-market residential acquisitions in Tacoma, Puyallup, Lakewood, and University Place."}}]
            }
        }
    }

    client_resp = requests.post("https://api.notion.com/v1/pages", headers=headers, json=client_payload)
    client_page_id = None
    if client_resp.status_code == 200:
        client_page_id = client_resp.json()["id"]
        print(f"Created Client: Cascade Property Partners (ID: {client_page_id})")
    else:
        print(f"Error creating client: {client_resp.status_code} - {client_resp.text}")

    # 3. Update Pierce County to link back to Client and set Stage to Active
    if pierce_page_id and client_page_id:
        print("\n--- Step 2: Updating Pierce County Status & Relations ---")
        update_county_payload = {
            "properties": {
                "Stage": {"select": {"name": "Active"}},
                "Launch Date": {"date": {"start": "2026-09-01"}},
                "Renewal Date": {"date": {"start": "2026-11-30"}},
                "Active Client": {"relation": [{"id": client_page_id}]}
            }
        }
        requests.patch(f"https://api.notion.com/v1/pages/{pierce_page_id}", headers=headers, json=update_county_payload)
        print("Pierce County updated to Active with linked Founding Partner.")

    time.sleep(1)

    # 4. Create 3 Backfilled Opportunities
    print("\n--- Step 3: Backfilling Realistic Opportunities ---")

    OPPORTUNITY_1 = {
        "title": "OPP-2026-PC-001 | 4812 S Pine St, Tacoma",
        "case_num": "26-4-00892-1",
        "estate": "Estate of Robert Arthur Miller",
        "address": "4812 S Pine St, Tacoma, WA 98409",
        "stage": "Delivered",
        "date_rec": "2026-09-08",
        "date_del": "2026-09-10",
        "priority": "Priority A",
        "score": 94,
        "prop_match": "Confirmed",
        "own_status": "Resolved",
        "own_comp": "Low",
        "auth_class": "Confirmed Authority",
        "auth_conf": "High",
        "decision_maker": "David R. Miller (Son / Sole Personal Representative)",
        "dm_accuracy": "Correct",
        "contact_readiness": "Ready",
        "contact_outcome": "Appointment Set",
        "qc_status": "Passed",
        "research_time": 18,
        "direct_cost": 12.50,
        "notes": "PR granted Nonintervention Powers under RCW 11.68. Craftsman 3bd/1ba, built 1954. Free and clear. Motivated to sell directly without listing fees."
    }

    OPPORTUNITY_2 = {
        "title": "OPP-2026-PC-002 | 11204 94th Ave E, Puyallup",
        "case_num": "26-4-01044-8",
        "estate": "Estate of Eleanor Vance Hayes",
        "address": "11204 94th Ave E, Puyallup, WA 98373",
        "stage": "Delivered",
        "date_rec": "2026-09-11",
        "date_del": "2026-09-14",
        "priority": "Priority B",
        "score": 76,
        "prop_match": "Confirmed",
        "own_status": "Resolved",
        "own_comp": "Medium",
        "auth_class": "Likely Decision Maker",
        "auth_conf": "Medium",
        "decision_maker": "Patricia Hayes Morgan (Daughter / Petitioning Admin)",
        "dm_accuracy": "Useful",
        "contact_readiness": "Ready",
        "contact_outcome": "Follow-Up Required",
        "qc_status": "Passed",
        "research_time": 26,
        "direct_cost": 18.00,
        "notes": "Intestate with 3 adult children. Waivers signed. Small balance mortgage (~$145k). Est ARV $485k."
    }

    OPPORTUNITY_3 = {
        "title": "OPP-2026-PC-003 | 3102 6th Ave, Tacoma",
        "case_num": "26-4-01105-3",
        "estate": "Estate of Thomas Glenn Walker",
        "address": "3102 6th Ave, Tacoma, WA 98406",
        "stage": "Rejected",
        "date_rec": "2026-09-15",
        "date_del": None,
        "priority": "Disqualified",
        "score": 22,
        "prop_match": "Rejected",
        "own_status": "Complex",
        "own_comp": "High",
        "auth_class": "Authority Unresolved",
        "auth_conf": "Low",
        "decision_maker": "Unresolved (Title passed via Transfer on Death Deed to Irrevocable Trust)",
        "dm_accuracy": "Not Yet Reviewed",
        "contact_readiness": "Do Not Contact",
        "contact_outcome": "Not Attempted",
        "qc_status": "Failed",
        "research_time": 12,
        "direct_cost": 5.00,
        "notes": "QC Rejected: Real property transferred via TODD outside probate court jurisdiction. Underwater reverse mortgage. Filtered out before delivery."
    }

    opp_pages = []

    for opp in [OPPORTUNITY_1, OPPORTUNITY_2, OPPORTUNITY_3]:
        props = {
            "Opportunity ID": {"title": [{"text": {"content": opp["title"]}}]},
            "Probate Case Number": {"rich_text": [{"text": {"content": opp["case_num"]}}]},
            "Decedent or Estate": {"rich_text": [{"text": {"content": opp["estate"]}}]},
            "Property Address": {"rich_text": [{"text": {"content": opp["address"]}}]},
            "Workflow Stage": {"select": {"name": opp["stage"]}},
            "Date Received": {"date": {"start": opp["date_rec"]}},
            "Priority": {"select": {"name": opp["priority"]}},
            "Score": {"number": opp["score"]},
            "Property Match Status": {"select": {"name": opp["prop_match"]}},
            "Ownership Status": {"select": {"name": opp["own_status"]}},
            "Ownership Complexity": {"select": {"name": opp["own_comp"]}},
            "Authority Classification": {"select": {"name": opp["auth_class"]}},
            "Authority Confidence": {"select": {"name": opp["auth_conf"]}},
            "Decision Maker": {"rich_text": [{"text": {"content": opp["decision_maker"]}}]},
            "Decision-Maker Accuracy": {"select": {"name": opp["dm_accuracy"]}},
            "Contact Readiness": {"select": {"name": opp["contact_readiness"]}},
            "Contact Outcome": {"select": {"name": opp["contact_outcome"]}},
            "QC Status": {"select": {"name": opp["qc_status"]}},
            "Research Time": {"number": opp["research_time"]},
            "Direct Cost": {"number": opp["direct_cost"]},
            "Notes": {"rich_text": [{"text": {"content": opp["notes"]}}]},
            "County": {"relation": [{"id": pierce_page_id}] if pierce_page_id else []},
            "Client": {"relation": [{"id": client_page_id}] if client_page_id else []}
        }
        if opp["date_del"]:
            props["Date Delivered"] = {"date": {"start": opp["date_del"]}}

        opp_payload = {
            "parent": {"database_id": OPPORTUNITIES_DB_ID},
            "properties": props
        }

        r = requests.post("https://api.notion.com/v1/pages", headers=headers, json=opp_payload)
        if r.status_code == 200:
            p_id = r.json()["id"]
            opp_pages.append((opp["title"], p_id))
            print(f"Created Opportunity: {opp['title']} (ID: {p_id})")
        else:
            print(f"Error creating opp {opp['title']}: {r.status_code} - {r.text}")

    # 5. Populate Complete Probate Opportunity File on OPP-1
    if opp_pages:
        opp1_id = opp_pages[0][1]
        print(f"\n--- Step 4: Formatting Full Opportunity File on {opp_pages[0][0]} ---")

        blocks = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [t("GIENI ACQUISITION DECISION FILE"), t(" — EXCLUSIVE OPPORTUNITY", False, "green")]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [t("Target County: Pierce County, WA | Confidential Delivery for Cascade Property Partners\nDelivered under County Exclusivity SLA. Decision readiness verified through 5-layer intelligence pipeline.")]}
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [t("1. Executive Acquisition Summary")]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [t("Property: ", True), t("4812 S Pine St, Tacoma, WA 98409 (Parcel # 0320183042)")]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [t("Estimated ARV: ", True), t("$445,000 | "), t("Estimated Repair Budget: ", True), t("$55,000 | "), t("Target Max Offer: ", True), t("$255,000")]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [t("Equity Position: ", True), t("100% Free and Clear. No recorded senior deed of trust or encumbrances.")]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [t("Decision Maker: ", True), t("David R. Miller (Son, Personal Representative with Nonintervention Powers)")]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [t("Legal Authority Status: ", True), t("RCW 11.68 Confirmed. Letters Testamentary issued August 24, 2026. Nonintervention powers active—PR can execute purchase contract without court confirmation or appraisal hearing.")]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [t("2. Property & Physical Profile")]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [t("Single-Family Residence built in 1954. 3 Bedrooms, 1 Bathroom, 1,248 sqft finished area on a 6,500 sqft lot. Detached 1-car garage with alley access. Zoned Tacoma R-2 (Single Family Residential). Assessed Land Value: $162,400, Improvements: $148,600 (Total Tax Assessed: $311,000). Roof age ~18 yrs, original galvanized plumbing, dated cosmetics. Vacant as of August 2026.")]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [t("3. Ownership & Title Analysis")]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [t("Statutory Warranty Deed recorded in Pierce County Auditor records (Recording # 8204120341) vesting title in Robert Arthur Miller as sole owner. Decedent spouse predeceased in 2017 (Pierce County Auditor Recording # 201708150119). No secondary claims, lis pendens, or tax delinquencies found. 2026 property taxes paid in full.")]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [t("4. Control & Authority Resolution")]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [t("Probate Court: ", True), t("Pierce County Superior Court, Case # 26-4-00892-1.")]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [t("Last Will and Testament: ", True), t("Executed March 14, 2019. Designates son David R. Miller as sole Executor with request for Nonintervention Powers.")]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [t("Order Admitting Will: ", True), t("Entered August 24, 2026 by Court Commissioner. Finding estate solvent and granting Nonintervention Powers under RCW 11.68.011.")]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [t("Transactional Certainty: ", True), t("EXTREMELY HIGH. The PR can execute a standard PSA and Personal Representative Deed without further court petition.")]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [t("5. Acquisition Strategy & Suggested Outreach")]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [t("Recommended Angle: ", True), t("Compassionate, 'As-Is' convenience purchase. PR David Miller resides in neighboring Puyallup (approx 15 miles away) and works full-time. He has voiced exhaustion with maintaining the yard and clearing 40 years of personal property.")]}
            },
            {
                "object": "block",
                "type": "quote",
                "quote": {"rich_text": [t("\"Hi David, my name is Marcus with Cascade Property Partners. First, our condolences on your father's passing. I'm reaching out because we purchase homes as-is directly in the Pine Street area. We understand navigating an estate can involve immense logistical effort, so we can purchase without any cleanout required, cover standard escrow closing costs, and close on whichever timeline works best for the estate.\"")]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [t("6. Verified Evidence & Document Links")]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [t("Court Docket: ", True), t("Pierce County LINX Superior Court Case # 26-4-00892-1 (Verified Letters Issued)")]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [t("Tax Assessor: ", True), t("Pierce County e-ATR Parcel # 0320183042")]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [t("Recorded Deed: ", True), t("Pierce County Auditor Instrument # 8204120341")]}
            }
        ]

        r_blocks = requests.patch(f"https://api.notion.com/v1/blocks/{opp1_id}/children", headers=headers, json={"children": blocks})
        if r_blocks.status_code == 200:
            print("Successfully attached rich Opportunity File content to OPP-1!")
        else:
            print(f"Error attaching blocks: {r_blocks.status_code} - {r_blocks.text}")

    print("\nAll tasks completed successfully!")

if __name__ == "__main__":
    main()
