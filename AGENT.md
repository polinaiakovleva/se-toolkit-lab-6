# Agent CLI

## Overview
A CLI agent that answers questions about the project by reading files from the wiki and source code, and querying the backend API. Built for Lab 6, Task 3.

## LLM Provider
- **Provider**: Configurable via environment variables (OpenAI-compatible API)
- **Default**: Local Ollama with glm-4.6:cloud or llama3.2
- **Base URL**: Set via `LLM_API_BASE` environment variable
- **Authentication**: Uses `LLM_API_KEY` from environment (no key needed for local Ollama)

## Tools

### `list_files(path)`
Lists files and directories at the given path (relative to project root).
- **When to use**: Exploring directory structure, discovering available files
- **Example**: `list_files("wiki")` returns all wiki files

### `read_file(path)`
Returns the content of a file at the given path (relative to project root).
- **When to use**: Reading documentation, source code, configuration files
- **Security**: Prevents path traversal attacks by validating paths

### `query_api(method, path, body?, auth?)`
Calls the deployed backend API to get live data.
- **Parameters**:
  - `method`: HTTP method (GET or POST)
  - `path`: API endpoint path (e.g., `/items/`, `/analytics/completion-rate?lab=lab-01`)
  - `body`: Optional JSON request body for POST requests
  - `auth`: Optional boolean (default true). Set to false to test authentication errors.
- **Authentication**: Uses `LMS_API_KEY` from environment when auth=true
- **Returns**: JSON with `status_code` and `body`
- **Use auth=false** when testing what happens without authentication (expect 401)

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

## Implementation Details

### Authentication Testing
The `query_api` tool supports an `auth` parameter:
- When `auth=true` (default): Includes `Authorization: Bearer {LMS_API_KEY}` header
- When `auth=false`: Skips authentication header, useful for testing auth error responses

This is essential for questions like "What status code does the API return without authentication?"

### Tool Call Handling
The agent handles two types of tool call formats:
1. **Standard OpenAI function calling**: When the LLM uses proper `tool_calls` in the response
2. **Text-based JSON**: When the LLM outputs tool calls as JSON text (for models with limited function calling support)

### Text-Based Tool Call Detection
For models that don't support proper OpenAI function calling, the agent parses tool calls from the response text using regex patterns to find JSON objects with `name` and `arguments` fields.

## Lessons Learned

1. **Model Quality Matters**: glm-4.6:cloud follows instructions better than smaller models like llama3.2 or qwen2.5-coder:1.5b
2. **Timeout Management**: Added 60-second timeout for LLM calls to prevent hanging on slow models
3. **Auth Parameter**: Essential to add auth=false option for testing authentication scenarios
4. **System Prompt Clarity**: Clear instructions about when to use each tool and how to format tool calls
5. **Error Handling**: The agent gracefully handles missing files and API errors

## Benchmark Results

### Local Evaluation (5/10 questions passed)

| # | Question | Status | Notes |
|---|----------|--------|-------|
| 0 | Branch protection | ✅ PASSED | Uses read_file on wiki |
| 1 | SSH connection | ✅ PASSED | Uses read_file on wiki |
| 2 | Backend framework | ✅ PASSED | Uses read_file on source |
| 3 | Router modules | ✅ PASSED | Uses list_files and read_file |
| 4 | Items count | ✅ PASSED | Uses query_api |
| 5 | Auth status code | ✅ PASSED | Uses query_api with auth=false |
| 6+ | Complex questions | ⏳ Pending | Require multi-step reasoning |

### Key Improvements Made
1. Added `auth` parameter to `query_api` for testing auth errors
2. Added text-based tool call detection for models without proper function calling
3. Improved system prompt with clearer tool usage instructions
4. Added timeout handling for slow LLM responses