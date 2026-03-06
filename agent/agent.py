import os
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.tools import get_board_data, analyze_revenue, get_all_boards, run_python_on_board, preview_board_schema
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

tools = [get_board_data, analyze_revenue, get_all_boards, run_python_on_board, preview_board_schema]

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

memory = MemorySaver()
agent = create_react_agent(llm, tools=tools, checkpointer=memory)

def generate_suggested_questions(last_assistant_message: str):
    """Generate 3 clickable follow-up questions for the user based on the AI's last response."""
    suggestion_prompt = f"""
    Based on the following response from a Business Intelligence AI, generate exactly 3 short, relevant follow-up questions the user might want to ask next.
    Return ONLY a valid JSON list of 3 strings. Do not use markdown backticks or explanation.
    
    Response:
    {last_assistant_message[-1000:]}
    """
    try:
        res = llm.invoke(suggestion_prompt)
        import json
        text = res.content.strip().replace("```json", "").replace("```", "")
        questions = json.loads(text)
        return questions[:3]
    except Exception:
        # Fallback default questions if parsing fails
        return ["What else is on the Deal funnel Data board?", "Analyze the revenue.", "Which boards do I have access to?"]