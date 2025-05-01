"""
Main agent logic: orchestrates LLM, tools, memory, and judge.
Production-ready version with config file support.
"""
import asyncio
import logging
import yaml
import re
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

from .llm import LLM, DummyLLM, ConfigurableLLM
from .tools import Tool, SearchTool, WeatherTool, DocumentationTool
from .memory import Memory
from .judge import JudgeAgent

logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file at startup
load_dotenv()

def load_config(path: str = "data/config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def build_llm(cfg: dict) -> LLM:
    llm_cfg = cfg.get("llm", {})
    provider = llm_cfg.get("provider", "dummy")
    if provider == "dummy":
        return DummyLLM()
    return ConfigurableLLM(
        endpoint=llm_cfg.get("endpoint", ""),
        api_key=llm_cfg.get("api_key", ""),
        model=llm_cfg.get("model", ""),
        provider=provider
    )

class DateTool(Tool):
    async def arun(self, query: str, memory: List[str]) -> str:
        # Always return the current date in a friendly format
        now = datetime.now()
        return now.strftime("Today is %A, %B %d, %Y.")

def build_tools(cfg: dict, llm: LLM) -> Dict[str, Tool]:
    tools_cfg = cfg.get("tools", {})
    tools = {}
    if tools_cfg.get("search"):
        tools["search"] = SearchTool()
    if tools_cfg.get("weather"):
        tools["weather"] = WeatherTool()
    tools["date"] = DateTool()  # Always add date tool
    tools["doc"] = DocumentationTool(llm)  # Always add documentation tool
    return tools

def build_memory(cfg: dict) -> Memory:
    mem_cfg = cfg.get("memory", {})
    return Memory(file_path=mem_cfg.get("file_path", "data/memory.json"))

def build_judge(cfg: dict, llm: LLM) -> JudgeAgent:
    judge_cfg = cfg.get("judge", {})
    return JudgeAgent(llm, use_llm=judge_cfg.get("use_llm", False))

class AIAgent:
    def __init__(self, llm: LLM, tools: Dict[str, Tool], judge: JudgeAgent, memory: Memory):
        self.llm = llm
        self.tools = tools
        self.judge = judge
        self.memory = memory

    async def handle_query(self, query: str):
        self.memory.add(f"User: {query}")
        tool_used = None
        tool_result = None
        # Intent-based tool selection
        tool_intents = {
            "search": [
                r"search", r"find", r"look up", r"who is", r"what is", r"when did", r"where is", r"tell me about",
                r"cm", r"chief minister", r"prime minister", r"president", r"governor", r"current", r"latest", r"news", r"update", r"leader", r"minister", r"ceo", r"head of", r"famous", r"notable", r"recent", r"today's", r"today in history", r"winner", r"score", r"result", r"election", r"sports", r"movie", r"actor", r"actress", r"celebrity", r"billionaire", r"richest", r"top", r"best"
            ],
            "weather": [r"weather", r"temperature", r"forecast", r"rain", r"humidity"],
            "date": [r"date", r"day", r"today", r"what day", r"what's the date", r"current date", r"current day"],
            "doc": [r"doc", r"documentation", r"explain code", r"generate doc", r"write doc", r"write documentation", r"explain function", r"explain this", r"add docstring", r"generate docstring"]
        }
        selected_tool = None
        for tool_name, patterns in tool_intents.items():
            for pat in patterns:
                if re.search(pat, query, re.IGNORECASE):
                    selected_tool = tool_name
                    break
            if selected_tool:
                break
        try:
            answer = await self.llm.agenerate(query, self.memory.get())
            self.memory.add(f"LLM: {answer}")
        except Exception as e:
            logging.error(f"LLM error: {e}")
            answer = "Sorry, there was an error with the language model."
            self.memory.add(f"LLM error: {e}")

        if selected_tool and selected_tool in self.tools:
            try:
                tool_result = await self.tools[selected_tool].arun(query, self.memory.get())
                self.memory.add(f"Tool[{selected_tool}]: {tool_result}")
                print(f"[TOOL] Using '{selected_tool}' tool for this query.")
                print(f"[TOOL RESULT] {tool_result}")
                answer = tool_result
                tool_used = selected_tool
            except Exception as e:
                logging.error(f"Tool '{selected_tool}' error: {e}")
                self.memory.add(f"Tool[{selected_tool}] error: {e}")

        for _ in range(3):  # Retry up to 3 times
            try:
                approved, reason = await self.judge.areview(answer, self.memory.get(),  tool_name)
            except Exception as e:
                logging.error(f"Judge error: {e}")
                approved = False
                reason = f"Judge error: {e}"
            if approved:
                if tool_used:
                    print(f"[INFO] Answer provided by '{tool_used}' tool.")
                else:
                    print(f"[INFO] Answer provided by LLM.")
                print(f"Agent: {answer}")
                self.memory.add(f"Agent: {answer}")
                return answer
            else:
                print(f"Judge: Answer not approved, retrying... Reason: {reason}")
                try:
                    answer = await self.llm.agenerate(query + " (retry)", self.memory.get())
                    self.memory.add(f"LLM (retry): {answer}")
                except Exception as e:
                    logging.error(f"LLM retry error: {e}")
                    answer = "Sorry, there was an error with the language model."
                    self.memory.add(f"LLM retry error: {e}")
        print("Agent: Unable to provide a satisfactory answer after retries.")
        return "Unable to provide a satisfactory answer."

async def main():
    config = load_config()
    llm = build_llm(config)
    tools = build_tools(config, llm)
    memory = build_memory(config)
    judge = build_judge(config, llm)
    agent = AIAgent(llm, tools, judge, memory)

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        await agent.handle_query(user_input)

if __name__ == "__main__":
    asyncio.run(main())
