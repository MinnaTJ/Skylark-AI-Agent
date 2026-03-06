import os
import requests
from dotenv import load_dotenv

load_dotenv()
MONDAY_API_KEY = os.environ.get("MONDAY_API_KEY")

def test_boards():
    # 1. First get all boards to find "Deal funnel Data"
    query = "{ boards(limit: 10) { id name } }"
    url = "https://api.monday.com/v2"
    headers = {"Authorization": MONDAY_API_KEY}
    
    resp = requests.post(url, json={"query": query}, headers=headers).json()
    print("ALL BOARDS:", resp)
    
    board_id = None
    for b in resp.get("data", {}).get("boards", []):
        if "Deal" in b["name"]:
            board_id = b["id"]
            break
            
    if not board_id:
        print("Could not find Deal funnel board")
        return
        
    print(f"\nFOUND DEAL BOARD: {board_id}")
    
    # 2. Query its columns and items
    item_query = f"""
    {{
      boards(ids: {board_id}) {{
        name
        items_page(limit: 5) {{
            cursor
            items {{
                name
                column_values {{
                    id
                    title
                    text
                }}
            }}
        }}
      }}
    }}
    """
    resp2 = requests.post(url, json={"query": item_query}, headers=headers).json()
    import json
    print("\nBOARD DATA:")
    print(json.dumps(resp2, indent=2))

if __name__ == "__main__":
    test_boards()
