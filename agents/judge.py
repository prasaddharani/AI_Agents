"""
Judge agent logic for answer review with async and LLM-based review option.
"""
import random
import asyncio
from .llm import LLM

class JudgeAgent:
    def __init__(self, llm: LLM, use_llm: bool = False):
        self.llm = llm
        self.use_llm = use_llm

    async def areview(self, answer: str, memory, tool_name: str = None) -> (bool, str):
        if tool_name == "doc":
            return True, "Auto-approved for doc tool."
        if self.use_llm:
            review_prompt = f"Is the following answer correct? {answer}"
            review = await self.llm.agenerate(review_prompt, memory)
            approved = "yes" in review.lower()
            reason = review.strip() if not approved else "Approved by LLM."
            return approved, reason
        else:
            await asyncio.sleep(0.05)
            approved = random.choice([True, False])
            reason = "Randomly rejected (demo mode)" if not approved else "Randomly approved (demo mode)"
            return approved, reason
