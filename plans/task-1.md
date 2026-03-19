\# Task 1: Call an LLM from Code



\## LLM Provider Choice

\- \*\*Provider\*\*: Local Ollama + LiteLLM on VM

\- \*\*Base URL\*\*: `http://10.93.25.70:8000/v1`

\- \*\*Model\*\*: `ollama/qwen2.5-coder:1.5b`

\- \*\*API Key\*\*: stored in `.env.agent.secret`



\## Agent Architecture

\- Use `openai` Python library.

\- Load environment variables from `.env.agent.secret`.

\- Accept question as first CLI argument.

\- Call `client.chat.completions.create`.

\- Output JSON with `answer` and empty `tool\_calls`.

\- All logs to stderr, JSON to stdout.

\- Timeout: 60 seconds.



\## Testing

One regression test that verifies JSON output.

