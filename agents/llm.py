"""
Generic LLM abstraction and provider-agnostic implementation.
Supports configurable provider, endpoint, API key, and model.
"""
from typing import List, Optional
import asyncio
import os
import aiohttp

class LLM:
    async def agenerate(self, prompt: str, memory: List[str]) -> str:
        raise NotImplementedError

class ConfigurableLLM(LLM):
    def __init__(self, endpoint: str, api_key: str, model: str, provider: str = "generic", extra_headers: Optional[dict] = None):
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.extra_headers = extra_headers or {}

    async def agenerate(self, prompt: str, memory: List[str]) -> str:
        headers = {"Content-Type": "application/json"}
        headers.update(self.extra_headers)
        # Add API key to headers or params as needed
        if self.provider == "openai":
            headers["Authorization"] = f"Bearer {self.api_key}"
            data = {
                "model": self.model,
                "messages": [{"role": "system", "content": "You are a helpful assistant."}] + [{"role": "user", "content": m} for m in memory] + [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        elif self.provider == "gemini":
            # Gemini expects only the latest prompt in the correct payload structure
            data = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            }
            url = self.endpoint
            if "?" not in url:
                url += f"?key={self.api_key}"
            elif "key=" not in url:
                url += f"&key={self.api_key}"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as resp:
                    resp.raise_for_status()
                    result = await resp.json()
                    return result["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            # Generic fallback
            data = {"prompt": prompt, "memory": memory, "model": self.model}
        url = self.endpoint
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                resp.raise_for_status()
                result = await resp.json()
                if self.provider == "openai":
                    return result["choices"][0]["message"]["content"].strip()
                elif self.provider == "gemini":
                    return result["candidates"][0]["content"]["parts"][0]["text"].strip()
                else:
                    # Fallback: try to get 'result' or 'text' field
                    return result.get("result") or result.get("text") or str(result)

class DummyLLM(LLM):
    async def agenerate(self, prompt: str, memory: List[str]) -> str:
        await asyncio.sleep(0.1)
        return f"LLM response to: {prompt}"

"""
OpenAILLM implementation for calling OpenAI's REST API.
Set your API key in the OPENAI_API_KEY environment variable.
"""
class OpenAILLM(LLM):
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"

    async def agenerate(self, prompt: str, memory: List[str]) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        for entry in memory:
            messages.append({"role": "user", "content": entry})
        messages.append({"role": "user", "content": prompt})
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=data) as resp:
                resp.raise_for_status()
                result = await resp.json()
                return result["choices"][0]["message"]["content"].strip()
