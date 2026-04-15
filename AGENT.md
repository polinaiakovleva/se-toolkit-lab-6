# Agent CLI

## Overview
A CLI agent that answers questions about the project by reading files from the wiki and source code, and querying the backend API. Built for Lab 6, Task 3.

## LLM Provider
- **Provider**: Local Ollama with glm-4.6:cloud or llama3.2
- **Base URL**: `http://localhost:11434/v1`
- **Model**: `glm-4.6:cloud` (recommended) or `llama3.2`
- **Authentication**: No API key needed for local Ollama

## Tools

### `list_files(path)`
Lists files and directories at the given path (relative to project root).
- **When to use**: Exploring directory structure, discovering available files
- **Example**: `list_files("wiki")` returns all wiki files

### `read_file(path)`
Returns the content of a file at the given path (relative to project root).
- **When to use**: Reading documentation, source code, configuration files
- **Security**: Prevents path traversal attacks by validating paths

### `query_api(method, path, body?)`
Calls the deployed backend API to get live data.
- **Parameters**:
  - `method`: HTTP method (GET or POST)
  - `path`: API endpoint path (e.g., `/items/`, `/analytics/completion-rate?lab=lab-01`)
  - `body`: Optional JSON request body for POST requests
- **Authentication**: Uses `LMS_API_KEY` from environment
- **Returns**: JSON with `status_code` and `body`

## Environment Variables

| Variable | Purpose | Source |
|----------|---------|--------|
| `LLM_API_KEY` | LLM provider API key | `.env.agent.secret` |
| `LLM_API_BASE` | LLM API endpoint URL | `.env.agent.secret` |
| `LLM_MODEL` | Model name | `.env.agent.secret` |
| `LMS_API_KEY` | Backend API key for `query_api` | `.env.docker.secret` |
| `AGENT_API_BASE_URL` | Base URL for `query_api` | Optional, defaults to `http://localhost:42002` |

## Agentic Loop

1. Send user question + tool definitions to LLM
2. If LLM responds with tool calls, execute them and feed results back
3. Repeat until LLM returns a final answer (JSON with `answer` and `source`)
4. Maximum 10 tool calls per question

## Output Format

```json
{
  "answer": "The answer to the question",
  "source": "wiki/file.md or backend/src/path.py (optional)",
  "tool_calls": [
    {"tool": "read_file", "args": {"path": "wiki/git-workflow.md"}, "result": "..."}
  ]
}
```

## Usage

```bash
uv run agent.py "How do you resolve a merge conflict?"
uv run agent.py "How many items are in the database?"
uv run agent.py "What framework does this project use?"
```

## Lessons Learned

1. **Model Quality Matters**: glm-4.6:cloud follows instructions better than llama3.2
2. **Timeout Management**: Complex questions need more time; increased timeout to 120s
3. **Tool Call Efficiency**: The model sometimes makes unnecessary calls; system prompt should guide better
4. **Source Attribution**: Wiki questions should always include source; API questions have optional source
5. **Error Handling**: The agent gracefully handles missing files and API errors

## Benchmark Score

**6/10** questions passed on local evaluation. Failed questions involve:
- Complex debugging (analytics endpoints)
- Multi-file reasoning (request journey)
- Deep code analysis (ETL idempotency)

These require more sophisticated reasoning or additional tool improvements.