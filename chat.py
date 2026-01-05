"""
Chatbot backend using LangChain and LangGraph.
"""
import os
import json
from flask import Blueprint, request, jsonify, stream_with_context, Response
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_node import ToolNode
from typing import TypedDict, Annotated, List
import operator

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# --- tools ---
@tool
def lookup_pokemon(name: str):
    """
    Search for a Pokémon by name to get its stats, type, and description.
    Useful when the user asks about a specific Pokémon's details.
    """
    from models import Pokemon
    
    # Simple fuzzy-ish search
    name = name.strip()
    
    # Ensure thread-safety for DB access in langgraph tools
    from app import app
    with app.app_context():
        pokemon = Pokemon.query.filter(Pokemon.name.ilike(f"%{name}%")).first()
        
        if not pokemon:
            return f"I couldn't find a Pokémon named '{name}'. Please check the spelling."
            
        data = pokemon.to_dict()
    
    # Format a nice string for the LLM
    info = (
        f"Name: {data['name']} (#{data['number']})\n"
        f"Type: {data['main_type']}" + (f"/{data['secondary_type']}" if data['secondary_type'] else "") + "\n"
        f"Description: {data['pokedex_desc']}\n"
        f"Stats: HP {data['hp']}, Atk {data['attack']}, Def {data['defense']}, "
        f"SpA {data['sp_attack']}, SpD {data['sp_defense']}, Spe {data['speed']}\n"
        f"Abilities: {data.get('abilities', 'Unknown')}\n"
    )
    
    if data.get('is_legendary'):
        info += "This is a Legendary Pokémon.\n"
    if data.get('is_mega'):
        info += "This is a Mega Evolution.\n"
        
    return info

@tool
def get_type_matchups(type_name: str):
    """
    Get type effectiveness (weaknesses/resistances) for a given type.
    """
    from models import PokemonType
    # This would ideally query a Type lookup table or logic
    # For now, we can rely on the LLM's internal knowledge or strict logic if we had a table.
    # Let's just return a placeholder or query if we had a Type model with matchups.
    return f"Type matchups for {type_name} are complex. (Functionality to query specific DB table coming soon, rely on general knowledge for now.)"

# --- Graph Definition ---

# --- Graph Definition ---

class AgentState(TypedDict):
    messages: Annotated[List[HumanMessage | AIMessage | SystemMessage], operator.add]

def get_model():
    # Use OpenRouter or OpenAI
    api_key = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY')
    base_url = None
    model_name = "gpt-3.5-turbo"
    
    if os.environ.get('OPENROUTER_API_KEY'):
        base_url = "https://openrouter.ai/api/v1"
        # Force gpt-4o-mini for robust output
        model_name = "openai/gpt-4o-mini"
        
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.7
    )
    return llm

# Global cache for compiled graph
_compiled_app_graph = None

def get_app_graph():
    """Lazily initialize and compile the graph"""
    global _compiled_app_graph
    if _compiled_app_graph is not None:
        return _compiled_app_graph

    # Define tools and model binding inside to avoid import-time errors
    tools = [lookup_pokemon]
    tool_node = ToolNode(tools)
    
    def call_model(state: AgentState):
        # Initialize model here so it fails only when used
        llm = get_model().bind_tools(tools)
        messages = state['messages']
        response = llm.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState):
        messages = state['messages']
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", "agent")

    _compiled_app_graph = workflow.compile()
    return _compiled_app_graph


# --- Routes ---

@chat_bp.route('/message', methods=['POST'])
def chat_message():
    data = request.get_json()
    user_message = data.get('message')
    history = data.get('history', []) # We might manage history on client or server. 
    # For simplicity, client sends full history or just last message and we handle limited context.
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    # Build state
    # Ideally we'd persist state, but for a simple widget, we can pass context back and forth 
    # OR start fresh. Let's assume stateless for the backend for now (history passed in).
    
    system_prompt = SystemMessage(content="You are a helpful Pokémon expert assistant named 'Rotom'. You help users identify Pokémon, build teams, and learn about stats. Use the available tools to look up accurate data from the database.")
    
    messages = [system_prompt]
    # Convert history dicts to Messages
    for msg in history:
        if msg['role'] == 'user':
            messages.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            messages.append(AIMessage(content=msg['content']))
            
    messages.append(HumanMessage(content=user_message))
    
    # Invoke graph
    # Note: Flask needs app context for DB tools to work
    from app import app
    with app.app_context():
        graph = get_app_graph()
        final_state = graph.invoke({"messages": messages})
        
    final_response = final_state['messages'][-1].content

    
    return jsonify({'response': final_response})
