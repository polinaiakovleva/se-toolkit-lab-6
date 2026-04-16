#!/usr/bin/env python3
"""
System Agent with query_api tool.
Usage: uv run agent.py "Your question"
"""

import os
import sys
import json
import logging
import httpx
from openai import OpenAI

# Fix Windows encoding issue
sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def load_env():
    """Load variables from .env.agent.secret and .env.docker.secret."""
    # Сначала загружаем .env.agent.secret (LLM ключи)
    env_file_agent = ".env.agent.secret"
    if os.path.exists(env_file_agent):
        with open(env_file_agent) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")
    else:
        logger.error(f"File {env_file_agent} not found. Create it from .env.agent.example")
        sys.exit(1)

    # Загружаем .env.docker.secret (LMS_API_KEY)
    env_file_docker = ".env.docker.secret"
    if os.path.exists(env_file_docker):
        with open(env_file_docker) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")
    else:
        logger.warning("File .env.docker.secret not found; LMS_API_KEY may be missing.")

# ---------- Tools ----------
def list_files(path):
    """List files and directories at given path relative to project root."""
    base = PROJECT_ROOT
    safe_path = os.path.normpath(os.path.join(base, path))
    if not safe_path.startswith(base):
        return "Error: Access denied (path traversal attempt)."
    if not os.path.exists(safe_path):
        return "Error: Path does not exist."
    if os.path.isfile(safe_path):
        return "Error: Path is a file, not a directory."
    try:
        items = os.listdir(safe_path)
        return "\n".join(items)
    except Exception as e:
        return f"Error: {str(e)}"

def read_file(path):
    """Read contents of a file at given path relative to project root."""
    base = PROJECT_ROOT
    safe_path = os.path.normpath(os.path.join(base, path))
    if not safe_path.startswith(base):
        return "Error: Access denied (path traversal attempt)."
    if not os.path.exists(safe_path):
        return "Error: File does not exist."
    if not os.path.isfile(safe_path):
        return "Error: Path is not a file."
    try:
        with open(safe_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"

def query_api(method, path, body=None, auth=True):
    """Call the deployed backend API.

    Args:
        method: HTTP method (GET or POST)
        path: API endpoint path (e.g., /items/)
        body: Optional JSON body for POST requests
        auth: If True, include Authorization header. If False, skip auth (for testing auth errors).
    """
    base_url = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002").rstrip('/')
    lms_key = os.getenv("LMS_API_KEY") if auth else None
    url = base_url + path
    headers = {"Content-Type": "application/json"}
    if auth and lms_key:
        headers["Authorization"] = f"Bearer {lms_key}"
    try:
        with httpx.Client(timeout=10) as client:
            if method.upper() == "GET":
                resp = client.get(url, headers=headers)
            elif method.upper() == "POST":
                body_dict = json.loads(body) if body else None
                resp = client.post(url, headers=headers, json=body_dict)
            else:
                return json.dumps({"error": f"Unsupported method {method}"})
        return json.dumps({"status_code": resp.status_code, "body": resp.text})
    except Exception as e:
        return json.dumps({"error": str(e)})

# ---------- Tool schemas ----------
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path relative to the project root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path relative to project root"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file at a given path relative to the project root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to project root"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": "Call the deployed backend API. Use GET to retrieve data, POST to send data. The base URL is set via AGENT_API_BASE_URL (default http://localhost:42002).",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {"type": "string", "enum": ["GET", "POST"], "description": "HTTP method"},
                    "path": {"type": "string", "description": "API endpoint path, e.g., /items/ or /analytics/completion-rate?lab=lab-01"},
                    "body": {"type": "string", "description": "Optional JSON request body for POST"},
                    "auth": {"type": "boolean", "description": "If true (default), include Authorization header. Set to false to test authentication errors."}
                },
                "required": ["method", "path"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are an intelligent assistant with access to three types of tools to answer questions about this project:

## Available Tools

1. **list_files(path)** - List files and directories at a given path relative to project root.
   - path is a relative path like "wiki" or "backend/src", NOT starting with /

2. **read_file(path)** - Read the contents of a file at a given path relative to project root.
   - path is a relative path like "wiki/git-workflow.md" or "backend/app/main.py", NOT starting with /

3. **query_api(method, path, body?, auth?)** - Call the deployed backend API to get live data.
   - method is "GET" or "POST"
   - path is an API endpoint like "/items/" or "/analytics/completion-rate"
   - body is optional JSON string for POST requests
   - auth is optional (defaults to true). Set to false to test authentication errors (expect 401 Unauthorized)

## Important: Answer Simple Questions Directly

If the question is a simple factual question that doesn't require project files or API calls (like "What is 2+2?" or "What is the capital of France?"), answer directly without using any tools. Just output JSON with the answer.

## When to Use Each Tool

### Wiki Questions (documentation, processes, how-to guides)
- First call: list_files(path="wiki") to discover available wiki files
- Then call: read_file(path="wiki/some-file.md") to read specific documentation
- Include source in output: {"answer": "...", "source": "wiki/some-file.md"}

### Source Code Questions (framework, implementation details, architecture)
- First call: list_files(path="backend") to discover source structure
- Then call: read_file(path="backend/src/app/main.py") to read source code
- For framework questions, look for imports like "from fastapi import..."

### Live System Questions (database counts, status codes, analytics)
- Call query_api(method="GET", path="/items/") to get item counts
- Call query_api(method="GET", path="/analytics/...") for analytics endpoints
- To test authentication: call query_api with auth=false to see the error response
- source field is optional for API questions

## Output Format

When you have gathered enough information (or for simple questions that don't need tools), respond with ONLY a JSON object, no other text:
{
  "answer": "Your answer here",
  "source": "wiki/file.md or backend/src/path.py (optional for API questions)"
}

## Rules
- Paths are RELATIVE, never start with /
- For simple questions that don't require tools, answer directly in JSON format
- For project questions, always use tools to find information, never guess
- Maximum 10 tool calls per question
- For wiki questions, always include a source reference"""

# ---------- Main ----------
def main():
    if len(sys.argv) < 2:
        logger.error("Usage: uv run agent.py \"Your question\"")
        sys.exit(1)

    question = sys.argv[1]
    load_env()

    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_API_BASE")
    model = os.getenv("LLM_MODEL", "ollama/qwen2.5-coder:1.5b")

    if not api_key or not base_url:
        logger.error("LLM_API_KEY and/or LLM_API_BASE not set in .env.agent.secret")
        sys.exit(1)

    logger.info(f"Connecting to LLM at {base_url}, model: {model}")

    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
        default_headers={},
        timeout=60.0,  # 60 second timeout for LLM calls
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ]

    tool_calls_history = []
    max_turns = 10

    for turn in range(max_turns):
        logger.info(f"Turn {turn+1}")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            sys.exit(1)

        assistant_message = response.choices[0].message
        content = assistant_message.content or ""

        # Check for tool calls in the standard OpenAI format
        if assistant_message.tool_calls:
            messages.append(assistant_message)

            for tc in assistant_message.tool_calls:
                func_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except:
                    args = {}
                logger.info(f"Tool call: {func_name} with args {args}")

                if func_name == "list_files":
                    result = list_files(args.get("path", ""))
                elif func_name == "read_file":
                    result = read_file(args.get("path", ""))
                elif func_name == "query_api":
                    result = query_api(
                        method=args.get("method", "GET"),
                        path=args.get("path", ""),
                        body=args.get("body"),
                        auth=args.get("auth", True)
                    )
                else:
                    result = f"Unknown tool: {func_name}"

                tool_calls_history.append({
                    "tool": func_name,
                    "args": args,
                    "result": result
                })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result
                })

            continue

        # Check for tool calls embedded in text (for models that don't use proper function calling)
        text_tool_call = None
        import re
        # Look for JSON with "name" and "arguments" keys
        json_match = re.search(r'\{[^{}]*"name"\s*:\s*"([^"]+)"[^{}]*"arguments"\s*:\s*(\{[^}]+\})[^{}]*\}', content, re.DOTALL)
        if not json_match:
            # Also try looking for tool call in markdown code block
            json_match = re.search(r'```json\s*\{[^{}]*"name"\s*:\s*"([^"]+)"[^{}]*"arguments"\s*:\s*(\{[^}]+\})[^{}]*\}\s*```', content, re.DOTALL)

        if json_match:
            func_name = json_match.group(1)
            try:
                args = json.loads(json_match.group(2))
            except:
                args = {}
            logger.info(f"Text tool call: {func_name} with args {args}")

            if func_name == "list_files":
                result = list_files(args.get("path", ""))
            elif func_name == "read_file":
                result = read_file(args.get("path", ""))
            elif func_name == "query_api":
                result = query_api(
                    method=args.get("method", "GET"),
                    path=args.get("path", ""),
                    body=args.get("body"),
                    auth=args.get("auth", True)
                )
            else:
                result = f"Unknown tool: {func_name}"

            tool_calls_history.append({
                "tool": func_name,
                "args": args,
                "result": result
            })

            # Feed result back to model
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"Tool result: {result}\n\nNow answer the original question with a JSON object containing 'answer' and 'source' (if applicable)."})
            continue

        # No tool calls - this should be the final answer
        logger.info(f"Final response: {content}")
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[^{}]*"answer"[^{}]*\}', content, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group(0))
            else:
                result_json = json.loads(content)
            answer = result_json.get("answer", "")
            source = result_json.get("source", "")
        except json.JSONDecodeError:
            answer = content
            source = ""

        output = {
            "answer": answer,
            "source": source,
            "tool_calls": tool_calls_history
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        logger.info("Done")
        return

    output = {
        "answer": "Could not find answer within tool call limit.",
        "source": "",
        "tool_calls": tool_calls_history
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    logger.info("Exited after max turns")

if __name__ == "__main__":
    main()