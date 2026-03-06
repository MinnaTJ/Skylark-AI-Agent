import pandas as pd

def clean_board_data(api_data):

    boards = api_data.get("data", {}).get("boards", [])
    if not boards:
        return pd.DataFrame()
        
    items = boards[0].get("items_page", {}).get("items", [])

    rows = []

    for item in items:

        row = {"task": item["name"]}

        for col in item["column_values"]:
            title = col.get("column", {}).get("title", col.get("id"))
            row[title] = col.get("text")

        rows.append(row)

    df = pd.DataFrame(rows)

    return df