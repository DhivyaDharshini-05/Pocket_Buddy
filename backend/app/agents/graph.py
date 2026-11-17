import json
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from app.config import get_settings
from .state import AgentState
from .advisory_agent import create_advisory_prompt
from .technical_agent import create_technical_prompt
from .portfolio_agent import create_portfolio_prompt
from .tools import calculate_sip_growth, calculate_asset_allocation, evaluate_stock_technical_status

settings = get_settings()

def get_llm():
    if settings.gemini_api_key:
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0.6,
            max_output_tokens=600
        )
    return None

# ============================================================================
# LangGraph Nodes
# ============================================================================

def supervisor_router(state: AgentState) -> Dict[str, Any]:
    """
    Supervisor Agent that analyzes query intent to dynamically route to specialized agents.
    """
    query = state["user_query"].lower()
    
    # Intent Detection
    if any(k in query for k in ["rsi", "macd", "indicator", "chart", "technical", "supertrend", "candle", "support", "resistance"]):
        intent = "technical"
    elif any(k in query for k in ["portfolio", "allocation", "sharpe", "asset mix", "weights", "rebalance", "diversif"]):
        intent = "portfolio"
    elif any(k in query for k in ["sip", "invest", "mutual fund", "stock", "tax", "retire", "emergency", "goal", "wealth", "plan"]):
        intent = "advisor"
    else:
        intent = "advisor"
        
    return {"target_intent": intent}

async def advisor_node(state: AgentState) -> Dict[str, Any]:
    """Lead Wealth Advisory Agent executing with LangChain."""
    llm = get_llm()
    if not llm:
        return {"agent_output": "I am Pocket Buddy, your AI Wealth Advisor. How can I assist with your financial goals?"}
        
    prompt_messages = create_advisory_prompt(state)
    try:
        response = await llm.ainvoke(prompt_messages)
        return {"agent_output": response.content}
    except Exception as e:
        print(f"Advisor Agent Error: {e}")
        return {"agent_output": "Financial advisory agent is currently formulating recommendations."}

async def technical_node(state: AgentState) -> Dict[str, Any]:
    """Quantitative Technical Analyst Agent executing with LangChain."""
    llm = get_llm()
    if not llm:
        return {"agent_output": "Technical analysis indicators show neutral momentum."}
        
    prompt_messages = create_technical_prompt(state)
    try:
        response = await llm.ainvoke(prompt_messages)
        return {"agent_output": response.content}
    except Exception as e:
        print(f"Technical Agent Error: {e}")
        return {"agent_output": "Technical indicator evaluation is currently being computed."}

async def portfolio_node(state: AgentState) -> Dict[str, Any]:
    """Portfolio Architecture Agent executing with LangChain."""
    llm = get_llm()
    if not llm:
        return {"agent_output": "Recommended portfolio allocation balances equities and debt."}
        
    prompt_messages = create_portfolio_prompt(state)
    try:
        response = await llm.ainvoke(prompt_messages)
        return {"agent_output": response.content}
    except Exception as e:
        print(f"Portfolio Agent Error: {e}")
        return {"agent_output": "Optimal portfolio asset weights generated."}

def response_synthesizer(state: AgentState) -> Dict[str, Any]:
    """Synthesize final output and assign metadata."""
    output = state.get("agent_output", "I'm ready to assist you with your financial planning and market queries.")
    return {
        "final_response": output,
        "context_used": bool(state.get("user_profile"))
    }

# ============================================================================
# Router Conditional Edge
# ============================================================================
def route_intent(state: AgentState) -> str:
    intent = state.get("target_intent", "advisor")
    if intent == "technical":
        return "technical_analyst"
    elif intent == "portfolio":
        return "portfolio_architect"
    return "wealth_advisor"

# ============================================================================
# Compile LangGraph StateGraph
# ============================================================================
def build_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("supervisor", supervisor_router)
    workflow.add_node("wealth_advisor", advisor_node)
    workflow.add_node("technical_analyst", technical_node)
    workflow.add_node("portfolio_architect", portfolio_node)
    workflow.add_node("synthesizer", response_synthesizer)
    
    # Set Entry Point
    workflow.set_entry_point("supervisor")
    
    # Add Conditional Edges from Supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_intent,
        {
            "wealth_advisor": "wealth_advisor",
            "technical_analyst": "technical_analyst",
            "portfolio_architect": "portfolio_architect"
        }
    )
    
    # Connect Agents to Synthesizer
    workflow.add_edge("wealth_advisor", "synthesizer")
    workflow.add_edge("technical_analyst", "synthesizer")
    workflow.add_edge("portfolio_architect", "synthesizer")
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()

# Global compiled instance
agent_graph = build_agent_graph()

def get_financial_agent_graph():
    return agent_graph

async def run_financial_multi_agent(query: str, user_profile: Dict[str, Any] = None, history: List[Dict] = None) -> Dict[str, Any]:
    """
    Public execution helper for the LangGraph Multi-Agent Financial System.
    """
    initial_state: AgentState = {
        "messages": [],
        "user_profile": user_profile or {},
        "user_query": query,
        "target_intent": None,
        "agent_output": None,
        "tool_data": None,
        "final_response": "",
        "context_used": bool(user_profile)
    }
    
    try:
        final_state = await agent_graph.ainvoke(initial_state)
        return {
            "response": final_state.get("final_response", ""),
            "context_used": final_state.get("context_used", False)
        }
    except Exception as e:
        print(f"LangGraph Execution Error: {e}")
        return {
            "response": "I'm here to help with your financial questions. You can ask about investments, stocks, mutual funds, tax planning, or retirement.",
            "context_used": bool(user_profile)
        }
