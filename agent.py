#!/usr/bin/env python3
"""
Documentation Agent with tool calling.
Usage: uv run agent.py "Your question"
"""

import os
import sys
import json
import logging
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ---------- Security: project root ----------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def load_env():
    """Load variables from .env.agent.secret into environment."""
    env_file = ".env.agent.secret"
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")
    else:
        logger.error(f"File {env_file} not found. Create it from .env.agent.example")
        sys.exit(1)

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

# ---------- Tool schemas (OpenAI format) ----------
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path relative to the project root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path relative to project root"
                    }
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
                    "path": {
                        "type": "string",
                        "description": "File path relative to project root"
                    }
                },
                "required": ["path"]
            }
        }
    }
]

# ---------- System prompt ----------
SYSTEM_PROMPT = """You are a helpful assistant with access to the project wiki files. You have two tools:
- list_files(path): list files and directories at the given path relative to the project root.
- read_file(path): read the contents of a file at the given path relative to the project root.

Your task: answer the user's question about the project using the wiki. First, use list_files to discover what files are available in the wiki directory. Then read relevant files to find the answer. When you have enough information, provide the final answer as a JSON object with two fields:
- "answer": a string containing the answer to the user's question.
- "source": a string indicating the wiki file (and optional section anchor) where the answer was found, e.g., "wiki/git-workflow.md#resolving-merge-conflicts".

Do not exceed 10 tool calls.
"""

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

    # Инициализируем сообщения
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ]

    tool_calls_history = []  # для финального вывода
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

        # Если есть вызовы инструментов
        if assistant_message.tool_calls:
            # Добавляем сообщение ассистента в историю
            messages.append(assistant_message)

            # Для каждого вызова выполняем инструмент и добавляем результат
            for tc in assistant_message.tool_calls:
                func_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except:
                    args = {}
                logger.info(f"Tool call: {func_name} with args {args}")

                # Выполняем функцию
                if func_name == "list_files":
                    result = list_files(args.get("path", ""))
                elif func_name == "read_file":
                    result = read_file(args.get("path", ""))
                else:
                    result = f"Unknown tool: {func_name}"

                # Сохраняем в историю для финального вывода
                tool_calls_history.append({
                    "tool": func_name,
                    "args": args,
                    "result": result
                })

                # Добавляем сообщение с результатом инструмента
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result
                })

            # Продолжаем цикл
            continue
        else:
            # Нет tool_calls – это финальный ответ (должен быть JSON)
            final_text = assistant_message.content
            logger.info(f"Final response: {final_text}")
            try:
                result_json = json.loads(final_text)
                answer = result_json.get("answer", "")
                source = result_json.get("source", "")
            except json.JSONDecodeError:
                # Если LLM не вернул JSON, используем текст как answer
                answer = final_text
                source = ""

            output = {
                "answer": answer,
                "source": source,
                "tool_calls": tool_calls_history
            }
            print(json.dumps(output, ensure_ascii=False))
            logger.info("Done")
            return

    # Если превышен лимит вызовов
    output = {
        "answer": "Could not find answer within tool call limit.",
        "source": "",
        "tool_calls": tool_calls_history
    }
    print(json.dumps(output, ensure_ascii=False))
    logger.info("Exited after max turns")

if __name__ == "__main__":
    main()