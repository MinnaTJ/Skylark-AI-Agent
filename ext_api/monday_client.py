import requests
import os

def get_monday_headers():
    api_key = os.getenv("MONDAY_API_KEY")
    if not api_key:
        raise ValueError("MONDAY_API_KEY is missing from the environment or secrets.")
    return {"Authorization": api_key}

def fetch_all_boards():
    query = """
    {
      boards(limit: 100) {
        id
        name
      }
    }
    """
    url = "https://api.monday.com/v2"
    response = requests.post(url, json={"query": query}, headers=get_monday_headers())
    return response.json()

def fetch_board_data(board_id):
    url = "https://api.monday.com/v2"
    headers = get_monday_headers()

    # 1. Initial 500 items
    query = f"""
    {{
      boards(ids: {board_id}) {{
        items_page(limit: 500) {{
          cursor
          items {{
            name
            column_values {{
              id
              text
              column {{
                title
              }}
            }}
          }}
        }}
      }}
    }}
    """
    response = requests.post(url, json={"query": query}, headers=headers).json()
    
    boards = response.get("data", {}).get("boards", [])
    if not boards:
        return response
        
    items_page = boards[0].get("items_page", {})
    all_items = items_page.get("items", [])
    cursor = items_page.get("cursor")
    
    # 2. Paginate remaining items using the cursor
    while cursor:
        next_query = f"""
        {{
          next_items_page(limit: 500, cursor: "{cursor}") {{
            cursor
            items {{
              name
              column_values {{
                id
                text
                column {{
                  title
                }}
              }}
            }}
          }}
        }}
        """
        next_res = requests.post(url, json={"query": next_query}, headers=headers).json()
        
        next_page = next_res.get("data", {}).get("next_items_page", {})
        if not next_page:
            break
            
        new_items = next_page.get("items", [])
        if not new_items:
            break
            
        all_items.extend(new_items)
        cursor = next_page.get("cursor")
        
    # 3. Inject aggregated items back into original response shape so data_cleaning dict parser still works
    response["data"]["boards"][0]["items_page"]["items"] = all_items
    response["data"]["boards"][0]["items_page"]["cursor"] = None

    return response