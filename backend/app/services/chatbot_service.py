from typing import Dict, List, Any
import datetime
from app.config import get_settings
from app.database import get_collection
from app.agents.graph import run_financial_multi_agent

settings = get_settings()

class ChatbotService:
    def __init__(self):
        self.has_api_key = bool(settings.gemini_api_key)

    async def process_query(self, query: str, user_id: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Process user query using LangGraph Multi-Agent Financial System.
        Preserves exact API contract for frontend compatibility.
        """
        # 1. Fetch user financial profile from MongoDB
        users_collection = get_collection("users")
        user = await users_collection.find_one({"_id": user_id})
        profile = user.get("profile", {}) if user else {}

        # 2. Invoke LangGraph Multi-Agent Workflow
        if self.has_api_key:
            try:
                agent_result = await run_financial_multi_agent(
                    query=query,
                    user_profile=profile,
                    history=conversation_history
                )
                response_text = agent_result.get("response")
                if not response_text or len(response_text.strip()) == 0:
                    response_text = self._rule_based_response(query, profile)
            except Exception as e:
                print(f"LangGraph Agent execution exception: {e}")
                response_text = self._rule_based_response(query, profile)
        else:
            response_text = self._rule_based_response(query, profile)

        return {
            "response": response_text,
            "context_used": bool(profile),
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    def _rule_based_response(self, query: str, profile: Dict) -> str:
        """Rule-based fallback response system"""
        query_lower = query.lower()

        responses = {
            "invest": self._get_investment_advice(profile),
            "stock": self._get_stock_advice(query_lower, profile),
            "mutual fund": self._get_mf_advice(profile),
            "sip": "SIP (Systematic Investment Plan) is a proven way to compound wealth. Based on your profile, consider starting with ₹" + str(self._suggest_sip_amount(profile)) + " monthly.",
            "risk": f"Your risk appetite is {profile.get('risk_appetite', 'not set')}. This means you should {self._get_risk_guidance(profile)}.",
            "portfolio": "A balanced portfolio typically balances equity index funds, government bonds, and liquid reserves. Based on your risk appetite, rebalance periodically.",
            "tax": "Consider tax-saving instruments like ELSS mutual funds, PPF, and NPS. ELSS has a favorable lock-in period of 3 years.",
            "retirement": f"For retirement planning at age {profile.get('age', 'your age')}, start investing early. Consider NPS and long-term equity index funds.",
            "emergency": "Keep 3-6 months of essential living expenses in a liquid fund or savings account as an emergency buffer.",
        }

        for keyword, response in responses.items():
            if keyword in query_lower:
                return response

        return "I'm Pocket Buddy, your AI Financial Advisor powered by LangGraph. You can ask me about investment planning, stock technicals, portfolio asset allocation, and retirement strategies. How can I assist you?"

    def _get_investment_advice(self, profile: Dict) -> str:
        risk = profile.get("risk_appetite", "medium")
        if risk == "low":
            return "For low-risk profiles, we prioritize capital preservation with debt mutual funds, sovereign gold bonds, and fixed deposits."
        elif risk == "high":
            return "For aggressive profiles, we recommend compounding capital via equity index funds, mid-cap growth stocks, and sectoral themes."
        return "For moderate risk profiles, a 60/40 blend of equity index funds and high-grade debt funds ensures steady compounding through market cycles."

    def _get_stock_advice(self, query: str, profile: Dict) -> str:
        return "Equity investments require discipline. Focus on companies with strong free cash flow, high ROCE, and solid corporate governance (such as NIFTY 50 leaders)."

    def _get_mf_advice(self, profile: Dict) -> str:
        risk = profile.get("risk_appetite", "medium")
        if risk == "low":
            return "Consider debt funds, liquid funds, and conservative hybrid funds for stable, predictable yields."
        return "Look for low-cost broad-market index funds (NIFTY 50 / NIFTY Next 50) and flexi-cap funds aligned with your investment horizon."

    def _suggest_sip_amount(self, profile: Dict) -> int:
        income = profile.get("income", 500000)
        return int((income / 12) * 0.20 / 100) * 100

    def _get_risk_guidance(self, profile: Dict) -> str:
        risk = profile.get("risk_appetite", "medium")
        guidance = {
            "low": "prioritize capital preservation with debt instruments and fixed deposits",
            "medium": "balance growth and safety with a mix of equity and debt",
            "high": "focus on aggressive growth through equity and growth funds"
        }
        return guidance.get(risk, "assess your comfort with market fluctuations")
