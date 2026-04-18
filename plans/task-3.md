# Task 3: The System Agent

## Implementation Plan

### 1. Add `query_api` Tool

The tool schema for `query_api`:
```python
{
    "type": "function",
    "function": {
        "name": "query_api",
        "description": "Call the deployed backend API. Use GET to retrieve data, POST to send data.",
        "parameters": {
            "type": "object",
            "properties": {
                "method": {"type": "string", "enum": ["GET", "POST"]},
                "path": {"type": "string", "description": "API endpoint path"},
                "body": {"type": "string", "description": "Optional JSON body for POST"},
                "auth": {"type": "boolean", "description": "Include auth header (default true)"}
            },
            "required": ["method", "path"]
        }
    }
}
```

### 2. Authentication

The tool reads:
- `LMS_API_KEY` from environment (set in `.env.docker.secret`)
- `AGENT_API_BASE_URL` from environment (defaults to `http://localhost:42002`)

Sends `Authorization: Bearer {LMS_API_KEY}` header with each request when auth=true.

### 3. System Prompt Update

The system prompt explains:
1. When to use wiki tools (`list_files`, `read_file`) - for project documentation questions
2. When to use `query_api` - for live system data (item count, status codes, analytics)
3. When to use `read_file` on source code - for questions about implementation
4. How to use `auth=false` parameter - for testing authentication errors

### 4. Response Format

The agent returns JSON with:
- `answer`: the answer string
- `source`: optional (for wiki-based answers)
- `tool_calls`: array of all tool calls made

## Benchmark Results

### Local Evaluation: 4/10 passed

| # | Question | Status | Notes |
|---|----------|--------|-------|
| 0 | Branch protection | ✅ PASSED | Uses read_file on wiki/github.md |
| 1 | SSH connection | ✅ PASSED | Uses read_file on wiki |
| 2 | Backend framework | ✅ PASSED | Uses read_file on source |
| 3 | Router modules | ✅ PASSED | Uses list_files and read_file |
| 4 | Items count | ❌ FAILED | API disconnected during test |
| 5+ | Remaining | ⏳ Pending | VM connectivity issues |

Note: Questions 4+ failed due to VM connectivity issues (API/SSH disconnected).

## Key Implementation Changes

### Iteration 1: Add query_api tool
- Implemented query_api function with httpx client
- Added tool schema to tools list
- Updated system prompt

### Iteration 2: Add auth parameter
- Added `auth` parameter to query_api (default true)
- When auth=false, request is made without Authorization header
- Essential for testing "What status code without auth?" questions

### Iteration 3: Add text-based tool call detection
- Some models don't support proper OpenAI function calling
- Added regex-based detection for tool calls in text
- Handles both standard and text-based tool call formats

### Iteration 4: Improve system prompt
- Added explicit instructions to use filenames from list_files output
- Added common wiki file examples (github.md, git.md, ssh.md)
- Added rule to never invent filenames

### Iteration 5: Add timeout handling
- Added 60-second timeout for LLM calls
- Better handling of slow cloud models

## Deployment on VM

The agent is deployed to the VM at `~/se-toolkit-lab-6` with:
- `.env.agent.secret` - LLM configuration (Ollama)
- `.env.docker.secret` - Backend API configuration
- Docker services running on ports 42031-42034

## Known Issues

1. **VM Connectivity**: The VM sometimes becomes unresponsive during heavy testing
2. **Cloud Model Rate Limits**: glm-4.6:cloud may hit rate limits
3. **Local Model Quality**: llama3.2 doesn't follow instructions well

## Files Modified

- `agent.py` - Main agent implementation
- `AGENT.md` - Documentation
- `plans/task-3.md` - This plan file
- `test_agent.py` - Added tests for framework and items count
- `pyproject.toml` - Added openai dependency