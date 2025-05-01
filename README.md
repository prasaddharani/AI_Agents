# AI Agent Framework

This project is a generic Python AI agent framework with:
- Pluggable LLMs (any model)
- Tool abstraction (search, weather, etc.)
- Memory for reasoning/history
- Judge agent to review answers and trigger retries

## Folder Structure

```
agents/           # Core framework code (agent.py, llm.py, tools.py, memory.py, judge.py, __init__.py)
data/             # Configuration and memory files (config.yaml, memory.json)
tests/            # Unit and integration tests
generated_docs/   # Generated documentation
README.md         # Project overview and instructions
.gitignore        # Git ignore rules
```

## Usage

Run the agent:
```
python -m agents.agent
```

Type your queries. The agent will use tools or LLM as needed, and the judge will review answers.

## Extending
- Add new tools in `agents/tools.py` by subclassing `Tool`.
- Swap in any LLM by subclassing `LLM` in `agents/llm.py`.
- Improve judge logic in `agents/judge.py`.
- Enhance memory in `agents/memory.py`.
