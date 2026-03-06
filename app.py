import streamlit as st
import os

# Ensure secrets are loaded into the environment before initializing the agent
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GEMINI_API_KEY"]
if "MONDAY_API_KEY" in st.secrets:
    os.environ["MONDAY_API_KEY"] = st.secrets["MONDAY_API_KEY"]

from dotenv import load_dotenv
import uuid
from agent.agent import agent, generate_suggested_questions

load_dotenv()

st.set_page_config(page_title="AI Business Intelligence Agent", page_icon=":chart_with_upwards_trend:", layout="wide")

st.title("AI Business Intelligence Agent")

# Initialize chat history and thread ID
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "session_id" not in st.session_state:
    st.session_state["session_id"] = uuid.uuid4().hex
if "suggestions" not in st.session_state:
    st.session_state["suggestions"] = ["What boards do you have access to?", "Analyze the Deals board revenue", "How many open Work Orders are there?"]

# Display chat messages from history on app rerun
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Suggestion Buttons
prompt = None
suggestion_clicked = False

# Render suggestions at the bottom
if st.session_state["suggestions"]:
    st.write("💡 **Suggested follow-ups:**")
    cols = st.columns(len(st.session_state["suggestions"]))
    for i, suggestion in enumerate(st.session_state["suggestions"]):
        with cols[i]:
            if st.button(suggestion, key=f"sug_btn_{i}"):
                prompt = suggestion
                suggestion_clicked = True

# Also capture normal chat input
chat_val = st.chat_input("Ask a founder-level question")
if chat_val:
    prompt = chat_val

# React to user input
if prompt:
    # Clear old suggestions when a new query is submitted
    st.session_state["suggestions"] = []
    
    # If it was from a button, it triggers rerun automatically so we render user message immediately
    st.chat_message("user").markdown(prompt)
    st.session_state["messages"].append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Format history for LangGraph
            chat_history = [
                ("system", "You are a helpful founder-level Business Intelligence AI. You have access to Monday.com boards. NEVER ask the user for a board ID. If they don't provide a board name, ask for it. If they provide a name, use `get_all_boards` to find its ID. To answer BI questions, avoid reading large raw board data directly. Instead, ALWAYS execute `preview_board_schema` to learn the exact column names, and then use `run_python_on_board` to write correct Pandas code to answer the user's question. If your python code fails, read the traceback and try again.")
            ]
            for msg in st.session_state["messages"]:
                chat_history.append((msg["role"], msg["content"]))
            
            inputs = {"messages": chat_history}
            config = {"configurable": {"thread_id": st.session_state["session_id"]}}
            
            response = agent.invoke(inputs, config=config)
            
            # Show tool calls in UI
            for msg in response["messages"]:
                if getattr(msg, 'type', '') == 'tool':
                    with st.expander(f"🛠️ Tool Result: {msg.name}"):
                        st.text(msg.content[:1000] + ('...' if len(msg.content) > 1000 else ''))
            
            raw_content = response["messages"][-1].content
            
            # Extract text
            if isinstance(raw_content, list):
                bot_reply = "".join(part.get("text", "") for part in raw_content if isinstance(part, dict) and "text" in part)
            elif isinstance(raw_content, str) and raw_content.strip().startswith("[{"):
                import ast
                try:
                    parsed = ast.literal_eval(raw_content)
                    bot_reply = "".join(item.get("text", "") for item in parsed if isinstance(item, dict) and "text" in item)
                except Exception:
                    bot_reply = raw_content
            else:
                bot_reply = raw_content
            
        st.markdown(bot_reply)
        st.session_state["messages"].append({"role": "assistant", "content": bot_reply})
        
        # Generate new suggestions based on the response
        with st.spinner("Brainstorming follow-ups..."):
            new_suggestions = generate_suggested_questions(bot_reply)
            st.session_state["suggestions"] = new_suggestions
            st.rerun()