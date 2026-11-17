from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any
from .state import AgentState

ADVISORY_SYSTEM_PROMPT = """You are the Lead Financial Planning & Wealth Advisor Agent of Pocket Buddy.
Your mission is to provide personalized, mathematically sound, and actionable financial planning advice tailored specifically to the user's financial profile.

Guidelines:
1. Address the user's specific financial situation (Age, Income, Savings, Risk Appetite, Goals).
2. Clearly explain investment concepts (SIP compounding, debt vs equity balance, tax efficiency under 80C/NPS, emergency funds).
3. Use bullet points and clear formatting for readability.
4. Keep the tone encouraging, professional, transparent, and grounded in prudent risk management.
"""

def create_advisory_prompt(state: AgentState) -> list:
    profile = state.get("user_profile", {})
    profile_summary = f"""User Financial Context:
- Age: {profile.get('age', 'Not specified')}
- Annual Income: ₹{profile.get('income', 1000000):,}
- Current Savings: ₹{profile.get('savings', 200000):,}
- Risk Tolerance: {str(profile.get('risk_appetite', 'Medium')).upper()}
- Financial Horizon: {str(profile.get('financial_goals', 'Long-Term')).upper()}
- Preferences: {', '.join(profile.get('investment_preferences', ['Mutual Funds', 'Stocks']))}
"""
    return [
        SystemMessage(content=f"{ADVISORY_SYSTEM_PROMPT}\n\n{profile_summary}"),
        HumanMessage(content=state["user_query"])
    ]
