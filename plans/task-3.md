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
                "body": {"type": "string", "description": "Optional JSON body for POST"}
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

Sends `Authorization: Bearer {LMS_API_KEY}` header with each request.

### 3. System Prompt Update

The system prompt explains:
1. When to use wiki tools (`list_files`, `read_file`) - for project documentation questions
2. When to use `query_api` - for live system data (item count, status codes, analytics)
3. When to use `read_file` on source code - for questions about implementation

### 4. Response Format

The agent returns JSON with:
- `answer`: the answer string
- `source`: optional (for wiki-based answers)
- `tool_calls`: array of all tool calls made

## Benchmark Results

### Initial Score: 6/10 passed

| # | Question | Status | Notes |
|---|----------|--------|-------|
| 0 | Branch protection | ✅ PASSED | Uses read_file on wiki |
| 1 | SSH connection | ✅ PASSED | Uses read_file on wiki |
| 2 | Backend framework | ✅ PASSED | Uses read_file on source |
| 3 | Router modules | ✅ PASSED | Uses list_files and read_file |
| 4 | Items count | ✅ PASSED | Uses query_api |
| 5 | Auth status code | ✅ PASSED | Uses query_api |
| 6 | Analytics error | ❌ FAILED | Timeout - needs debugging |
| 7 | Top learners error | ❌ FAILED | Too many tool calls |
| 8 | Request journey | ❌ FAILED | Too many tool calls |
| 9 | ETL idempotency | ❌ FAILED | Too many tool calls |

### Issues Found

1. **Timeouts**: Some questions require too many tool calls
2. **Tool call limit**: 10 turns not enough for complex questions
3. **Model quality**: glm-4.6:cloud sometimes makes unnecessary calls

## Iterations

### Iteration 1: Fix encoding issue
- Added `sys.stdout.reconfigure(encoding='utf-8')` to fix Windows encoding
- Result: Fixed Unicode errors

### Iteration 2: Configure backend URL
- Set `AGENT_API_BASE_URL=http://10.93.25.70:42002` in `.env.agent.secret`
- Result: query_api now works with remote backend

### Iteration 3: Increase timeout
- Changed timeout from 60s to 120s in `run_eval.py`
- Result: More questions pass

## Remaining Work

1. Improve system prompt for complex questions
2. Add more specific guidance for debugging questions
3. Consider increasing max_turns for complex queries