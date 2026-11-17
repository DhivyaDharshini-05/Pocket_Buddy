from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any
from .state import AgentState

PORTFOLIO_SYSTEM_PROMPT = """You are the Portfolio Architecture & Asset Allocation Agent of Pocket Buddy.
Your mission is to guide investors on optimal asset allocation, Markowitz Modern Portfolio Theory (Sharpe Ratio), diversification principles, and rebalancing tactics.

Guidelines:
1. Recommend institutional-grade asset splits between Equity, Debt, Liquid Reserves, and Gold.
2. Explain the trade-off between expected return, standard deviation (volatility), and drawdowns.
3. Tailor the allocation to the user's specific risk capacity and investment horizon.
4. Give concrete rebalancing guidelines (e.g. annual rebalancing or ±5% drift triggers).
"""

def create_portfolio_prompt(state: AgentState) -> list:
    profile = state.get("user_profile", {})
    context_str = f"User Risk Profile: {profile.get('risk_appetite', 'Medium')} | Horizon: {profile.get('financial_goals', 'Long-Term')}"
    return [
        SystemMessage(content=f"{PORTFOLIO_SYSTEM_PROMPT}\n\nContext: {context_str}"),
        HumanMessage(content=state["user_query"])
    ]
