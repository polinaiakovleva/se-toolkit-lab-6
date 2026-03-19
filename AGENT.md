cat > AGENT.md << 'EOF'
# Agent CLI

## Overview
A CLI agent that answers questions about the project by reading files from the wiki using tool calling. Built for Lab 6, Task 2.

## LLM Provider
- **Provider**: Ollama + LiteLLM on VM (or OpenRouter)
- **Base URL**: `http://10.93.25.70:8000/v1` (or your VM IP)
- **Model**: `ollama/qwen2.5-coder:1.5b` (must support tool calling)
- **Authentication**: API key stored in `.env.agent.secret`.

## Tools
- `list_files(path)` – lists files/directories at the given path (relative to project root).
- `read_file(path)` – returns the content of a file.

## Agentic Loop
1. Send user question + tool definitions to LLM.
2. If LLM responds with tool calls, execute them and feed results back.
3. Repeat until LLM returns a final answer (JSON with `answer` and `source` fields).
4. Limit of 10 tool calls per question.

## Output
Final JSON includes:
- `answer`: the answer string.
- `source`: wiki file reference (e.g., `wiki/git-workflow.md#resolving-merge-conflicts`).
- `tool_calls`: array of all tool calls made, each with `tool`, `args`, and `result`.

Example:
```json
{
  "answer": "Edit the conflicting file, choose which changes to keep, then stage and commit.",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {"tool": "list_files", "args": {"path": "wiki"}, "result": "git-workflow.md\n..."},
    {"tool": "read_file", "args": {"path": "wiki/git-workflow.md"}, "result": "..."}
  ]
}