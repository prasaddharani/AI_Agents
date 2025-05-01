"""
Memory/history management for the agent with persistent file storage.
"""
import json
from typing import List

class Memory:
    def __init__(self, file_path: str = "memory.json"):
        self.file_path = file_path
        self.history: List[str] = []
        self._load()

    def add(self, entry: str):
        self.history.append(entry)
        self._save()

    def get(self) -> List[str]:
        return self.history

    def _save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f)
        except Exception:
            pass

    def _load(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except Exception:
            self.history = []
