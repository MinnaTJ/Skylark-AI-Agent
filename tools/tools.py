from langchain.tools import tool
from ext_api.monday_client import fetch_board_data, fetch_all_boards
import pandas as pd

@tool
def get_all_boards():
    """Fetch all available monday boards to find their IDs and names. Use this when the user asks about a board but doesn't provide the ID."""
    data = fetch_all_boards()
    try:
        boards = data.get("data", {}).get("boards", [])
        if not boards:
            return "No boards found."
        return "\n".join([f"ID: {b['id']} - Name: {b['name']}" for b in boards])
    except Exception as e:
        return f"Error fetching boards: {str(e)}"

@tool
def get_board_data(board_id: str):
    """Fetch data from monday board"""
    return fetch_board_data(board_id)


from preprocessing.data_cleaning import clean_board_data

@tool
def analyze_revenue(board_id: str):
    """Analyze revenue from board data by board_id"""
    raw_data = fetch_board_data(board_id)
    try:
        dataframe = clean_board_data(raw_data)
        # Ensure Revenue column exists and handles strings with symbols
        if "Revenue" in dataframe.columns:
            # Clean string symbols like $ and , and convert to float
            df_rev = dataframe["Revenue"].replace(r'[\$,]', '', regex=True)
            total = pd.to_numeric(df_rev, errors='coerce').sum()
            return f"Total revenue for board {board_id} is ${total:,.2f}"
        else:
            return f"No 'Revenue' column found in board {board_id}"
    except Exception as e:
        return f"Error analyzing revenue: {str(e)}"

@tool
def preview_board_schema(board_id: str):
    """Fetch the schema (columns, types, and first 3 rows) of a board.
    ALWAYS use this tool BEFORE writing a `run_python_on_board` script to ensure you use the exact correct column names.
    """
    raw_data = fetch_board_data(board_id)
    try:
        df = clean_board_data(raw_data)
        schema = f"Columns: {list(df.columns)}\n\n"
        schema += "First 3 rows:\n"
        schema += df.head(3).to_string()
        return schema
    except Exception as e:
        return f"Error previewing schema: {str(e)}"

@tool
def run_python_on_board(board_id: str, python_script: str):
    """Run dynamic python scripts on the Monday data. 
    A Pandas DataFrame containing the board data is available as the variable `df`.
    You MUST store your final output in a variable called `result`.
    Example python_script:
    ```python
    open_deals = df[df['Deal Status'] == 'Open']
    result = f"There are {len(open_deals)} open deals."
    ```
    """
    raw_data = fetch_board_data(board_id)
    try:
        df = clean_board_data(raw_data)
        
        # Pre-clean numbers to float
        for col in df.columns:
            if df[col].dtype == object:
                # Remove $ and , generically
                cleaned = df[col].astype(str).str.replace(r'[\$,]', '', regex=True)
                # If it can all be converted to numeric, do it
                try:
                    df[col] = pd.to_numeric(cleaned)
                except Exception:
                    pass
                    
        local_context = {"df": df, "pd": pd, "result": None}
        exec(python_script, globals(), local_context)
        return str(local_context.get("result", "Error: Script did not assign to 'result' variable."))
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        df_info = f"\nDataframe columns: {list(df.columns)}\nData Types: {df.dtypes.to_dict()}"
        return f"Error executing python script:\n{error_msg}\n{df_info}\nFix the script and try again."