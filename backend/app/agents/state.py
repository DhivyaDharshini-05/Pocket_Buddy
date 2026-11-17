from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    Unified state shared across the LangGraph Multi-Agent Financial System.
    """
    messages: List[BaseMessage]
    user_profile: Dict[str, Any]
    user_query: str
    target_intent: Optional[str]        # 'advisor' | 'technical' | 'portfolio' | 'general'
    agent_output: Optional[str]
    tool_data: Optional[Dict[str, Any]]
    final_response: str
    context_used: bool
