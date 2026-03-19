# Task 1: Call an LLM from Code

## LLM Provider Choice
- **Provider**: Local Ollama + LiteLLM on VM
- **Base URL**: `http://10.93.25.70:8000/v1` (replace with your VM IP)
- **Model**: `ollama/qwen2.5-coder:1.5b`
- **API Key**: stored in `.env.agent.secret`

## Agent Architecture
- Use `openai` Python library.
- Load environment variables from `.env.agent.secret`.
- Accept question as first CLI argument.
- Call `client.chat.completions.create` with model and user message.
- Output JSON with `answer` and empty `tool_calls`.
- All logs go to stderr, only JSON to stdout.
- Timeout: 60 seconds.

## Testing
One regression test: run `agent.py` with a question, verify stdout is valid JSON and contains `answer` and `tool_calls`.
