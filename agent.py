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

def query_api(method, path, body=None):
    """Call the deployed backend API."""
    base_url = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002").rstrip('/')
    lms_key = os.getenv("LMS_API_KEY")
    if not lms_key:
        return json.dumps({"error": "LMS_API_KEY not set"})
    url = base_url + path
    headers = {
        "Authorization": f"Bearer {lms_key}",
        "Content-Type": "application/json"
    }
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
                    "body": {"type": "string", "description": "Optional JSON request body for POST"}
                },
                "required": ["method", "path"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are an intelligent assistant with access to three types of tools to answer questions about this project:

## Available Tools

1. **list_files(path)** - List files and directories at a given path relative to project root.
2. **read_file(path)** - Read the contents of a file at a given path relative to project root.
3. **query_api(method, path, body?)** - Call the deployed backend API to get live data.

## When to Use Each Tool

### Wiki Questions (documentation, processes, how-to guides)
- Use `list_files("wiki")` to discover available wiki files
- Use `read_file("wiki/some-file.md")` to read documentation
- The source should reference the wiki file path

### Source Code Questions (framework, implementation details, architecture)
- Use `list_files("src")` or `list_files("backend")` to discover source files
- Use `read_file("src/app/main.py")` to read source code
- For framework questions, read the imports in main files

### Live System Questions (database counts, status codes, analytics)
- Use `query_api("GET", "/items/")` to get item counts
- Use `query_api("GET", "/analytics/...")` for analytics endpoints
- Query without auth header to test authentication (expect 401)
- The source field is optional for system questions

### Bug Diagnosis Questions
- First use `query_api` to trigger the error and see the response
- Then use `read_file` to find the buggy code in the source

## Output Format

When you have gathered enough information, respond with a JSON object:
{
  "answer": "Your answer here",
  "source": "wiki/file.md or src/path.py (optional for API questions)"
}

## Rules
- Always use tools to find information, never guess
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
                        body=args.get("body")
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
        else:
            final_text = assistant_message.content
            logger.info(f"Final response: {final_text}")
            try:
                result_json = json.loads(final_text)
                answer = result_json.get("answer", "")
                source = result_json.get("source", "")
            except json.JSONDecodeError:
                answer = final_text
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