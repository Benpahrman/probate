import requests
import time
import json
import os

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = '3e0b5bd1-d90c-8105-b6fd-ef9a8371d96b'

headers = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

COUNTIES = [
    # Top Tier / Metro
    {"name": "Pierce", "stage": "Auditing", "accessibility": "Strong", "volume": 65, "status": "Complete", 
     "source_map": "https://linxonline.co.pierce.wa.us/linxweb/", 
     "notes": "Selected Primary Testbed. Superior Court powered by LINX (free online dockets & filings). Pierce County Assessor-Treasurer (e-ATR) integrated."},
    {"name": "King", "stage": "Candidate", "accessibility": "Strong", "volume": 140, "status": "Not Started", 
     "source_map": "https://kingcounty.gov/en/court/superior-court", 
     "notes": "Largest metro in WA. KC Script portal for court dockets. Highest average property value & volume."},
    {"name": "Snohomish", "stage": "Candidate", "accessibility": "Strong", "volume": 55, "status": "Not Started", 
     "source_map": "https://www.snohomishcountywa.gov/300/Superior-Court", 
     "notes": "Odyssey Portal & SCOPE assessor records. Strong suburban acquisition market."},
    {"name": "Spokane", "stage": "Candidate", "accessibility": "Moderate", "volume": 42, "status": "Not Started", 
     "source_map": "https://www.spokanecounty.org/628/Superior-Court", 
     "notes": "Eastern WA major metro. Odyssey Portal & County Clerk dockets."},
    {"name": "Clark", "stage": "Candidate", "accessibility": "Moderate", "volume": 38, "status": "Not Started", 
     "source_map": "https://clark.wa.gov/superior-court", 
     "notes": "Portland-Vancouver metro fringe. High demand, Odyssey portal."},
    
    # Tier 2 Secondary Counties
    {"name": "Thurston", "stage": "Candidate", "accessibility": "Moderate", "volume": 22, "status": "Not Started", "source_map": None, "notes": "State capital (Olympia/Lacey). Odyssey portal."},
    {"name": "Kitsap", "stage": "Candidate", "accessibility": "Moderate", "volume": 20, "status": "Not Started", "source_map": None, "notes": "Puget Sound naval & peninsula hub. Odyssey portal."},
    {"name": "Yakima", "stage": "Candidate", "accessibility": "Moderate", "volume": 18, "status": "Not Started", "source_map": None, "notes": "Central WA agricultural hub. Odyssey portal."},
    {"name": "Whatcom", "stage": "Candidate", "accessibility": "Moderate", "volume": 16, "status": "Not Started", "source_map": None, "notes": "Bellingham / Canadian border corridor."},
    {"name": "Benton", "stage": "Candidate", "accessibility": "Moderate", "volume": 15, "status": "Not Started", "source_map": None, "notes": "Tri-Cities metro (Kennewick/Richland)."},
    {"name": "Skagit", "stage": "Candidate", "accessibility": "Moderate", "volume": 11, "status": "Not Started", "source_map": None, "notes": "Mount Vernon / Anacortes."},
    {"name": "Cowlitz", "stage": "Candidate", "accessibility": "Moderate", "volume": 10, "status": "Not Started", "source_map": None, "notes": "Longview / Kelso corridor."},
    {"name": "Grant", "stage": "Candidate", "accessibility": "Moderate", "volume": 8, "status": "Not Started", "source_map": None, "notes": "Moses Lake / Columbia Basin."},
    {"name": "Franklin", "stage": "Candidate", "accessibility": "Moderate", "volume": 8, "status": "Not Started", "source_map": None, "notes": "Pasco / Tri-Cities."},
    {"name": "Island", "stage": "Candidate", "accessibility": "Moderate", "volume": 8, "status": "Not Started", "source_map": None, "notes": "Whidbey Island & Camano Island."},
    {"name": "Lewis", "stage": "Candidate", "accessibility": "Moderate", "volume": 7, "status": "Not Started", "source_map": None, "notes": "Centralia / Chehalis."},
    {"name": "Clallam", "stage": "Candidate", "accessibility": "Moderate", "volume": 8, "status": "Not Started", "source_map": None, "notes": "Port Angeles / Sequim (high median age)."},
    {"name": "Chelan", "stage": "Candidate", "accessibility": "Moderate", "volume": 6, "status": "Not Started", "source_map": None, "notes": "Wenatchee / Leavenworth."},
    {"name": "Mason", "stage": "Candidate", "accessibility": "Moderate", "volume": 6, "status": "Not Started", "source_map": None, "notes": "Shelton / Hood Canal."},
    {"name": "Grays Harbor", "stage": "Candidate", "accessibility": "Moderate", "volume": 6, "status": "Not Started", "source_map": None, "notes": "Aberdeen / Hoquiam coastal region."},
    {"name": "Walla Walla", "stage": "Candidate", "accessibility": "Moderate", "volume": 5, "status": "Not Started", "source_map": None, "notes": "Walla Walla wine country."},
    {"name": "Whitman", "stage": "Candidate", "accessibility": "Moderate", "volume": 4, "status": "Not Started", "source_map": None, "notes": "Pullman / WSU area."},
    {"name": "Kittitas", "stage": "Candidate", "accessibility": "Moderate", "volume": 4, "status": "Not Started", "source_map": None, "notes": "Ellensburg / Cle Elum."},
    {"name": "Douglas", "stage": "Candidate", "accessibility": "Moderate", "volume": 4, "status": "Not Started", "source_map": None, "notes": "East Wenatchee."},
    {"name": "Stevens", "stage": "Candidate", "accessibility": "Weak", "volume": 4, "status": "Not Started", "source_map": None, "notes": "Colville rural area."},
    {"name": "Jefferson", "stage": "Candidate", "accessibility": "Moderate", "volume": 4, "status": "Not Started", "source_map": None, "notes": "Port Townsend / Olympic Peninsula."},
    {"name": "Okanogan", "stage": "Candidate", "accessibility": "Weak", "volume": 3, "status": "Not Started", "source_map": None, "notes": "Omak / North Central rural."},
    {"name": "Pacific", "stage": "Candidate", "accessibility": "Weak", "volume": 3, "status": "Not Started", "source_map": None, "notes": "South Bend / Long Beach peninsula."},
    {"name": "Asotin", "stage": "Candidate", "accessibility": "Weak", "volume": 2, "status": "Not Started", "source_map": None, "notes": "Clarkston area."},
    {"name": "Klickitat", "stage": "Candidate", "accessibility": "Weak", "volume": 2, "status": "Not Started", "source_map": None, "notes": "Columbia Gorge rural."},
    {"name": "Adams", "stage": "Candidate", "accessibility": "Weak", "volume": 2, "status": "Not Started", "source_map": None, "notes": "Ritzville / Othello rural."},
    {"name": "San Juan", "stage": "Candidate", "accessibility": "Moderate", "volume": 2, "status": "Not Started", "source_map": None, "notes": "San Juan Islands (ultra-luxury estate market)."},
    {"name": "Pend Oreille", "stage": "Candidate", "accessibility": "Weak", "volume": 2, "status": "Not Started", "source_map": None, "notes": "Newport rural northeast."},
    {"name": "Skamania", "stage": "Candidate", "accessibility": "Weak", "volume": 2, "status": "Not Started", "source_map": None, "notes": "Stevenson / Columbia Gorge."},
    {"name": "Lincoln", "stage": "Candidate", "accessibility": "Weak", "volume": 2, "status": "Not Started", "source_map": None, "notes": "Davenport rural."},
    {"name": "Ferry", "stage": "Candidate", "accessibility": "Weak", "volume": 1, "status": "Not Started", "source_map": None, "notes": "Republic rural."},
    {"name": "Columbia", "stage": "Candidate", "accessibility": "Weak", "volume": 1, "status": "Not Started", "source_map": None, "notes": "Dayton rural."},
    {"name": "Wahkiakum", "stage": "Candidate", "accessibility": "Weak", "volume": 1, "status": "Not Started", "source_map": None, "notes": "Cathlamet rural."},
    {"name": "Garfield", "stage": "Candidate", "accessibility": "Weak", "volume": 1, "status": "Not Started", "source_map": None, "notes": "Pomeroy (least populated WA county)."}
]

os.makedirs("c:/Users/ben/probate/scripts", exist_ok=True)
created_count = 0
pierce_page_id = None

for c in COUNTIES:
    props = {
        "County": {
            "title": [{"text": {"content": c["name"]}}]
        },
        "State": {
            "select": {"name": "Washington"}
        },
        "Stage": {
            "select": {"name": c["stage"]}
        },
        "Data Accessibility": {
            "select": {"name": c["accessibility"]}
        },
        "Source Map Status": {
            "select": {"name": c["status"]}
        },
        "Qualified Filing Volume": {
            "number": c["volume"]
        },
        "Notes": {
            "rich_text": [{"text": {"content": c["notes"]}}]
        }
    }
    if c.get("source_map"):
        props["Source Map"] = {"url": c["source_map"]}

    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": props
    }

    resp = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload)
    if resp.status_code == 200:
        page_data = resp.json()
        created_count += 1
        if c["name"] == "Pierce":
            pierce_page_id = page_data["id"]
        print(f"[{created_count}/39] Added {c['name']} County")
    else:
        print(f"Error adding {c['name']}: {resp.status_code} - {resp.text}")
    
    time.sleep(0.35)

print(f"\nFinished! Successfully created {created_count} counties.")
if pierce_page_id:
    print(f"Pierce County Page ID: {pierce_page_id}")
    with open("c:/Users/ben/probate/scripts/county_context.json", "w") as f:
        json.dump({"pierce_page_id": pierce_page_id}, f)
