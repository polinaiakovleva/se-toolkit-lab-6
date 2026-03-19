# Task 2: The Documentation Agent

## Overview
Extend the agent from Task 1 to support tool calling. Implement two tools:
- `list_files(path)`: list files in a directory relative to project root.
- `read_file(path)`: read contents of a file.

Implement an agentic loop that:
1. Sends the user question and tool definitions to the LLM.
2. If the LLM responds with tool calls, executes them and appends results as tool messages, then repeats.
3. If the LLM responds with a text message (assumed to be JSON with answer and source), parses it and returns the final JSON.
4. Limits tool calls to 10.

## Tool schemas
- `list_files`: parameters: `path` (string). Returns newline-separated listing.
- `read_file`: parameters: `path` (string). Returns file content or error.

## Security
All paths are resolved relative to the project root (the directory containing agent.py). Path traversal attacks are prevented by checking that the absolute path starts with the project root.

## System prompt
The system prompt instructs the LLM to:
- Use `list_files` to explore the `wiki/` directory.
- Use `read_file` to read specific files.
- When enough information is gathered, provide the final answer as a JSON object with `answer` and `source` fields, where `source` is a wiki file path with optional anchor (e.g., `wiki/git-workflow.md#resolving-merge-conflicts`).
- Limit itself to at most 10 tool calls.

## Agentic loop implementation
- Use `openai` library with `tools` parameter.
- Maintain a list of messages (system prompt, user question, and assistant/tool messages).
- After each assistant response, check for `tool_calls`. If present, execute each tool, append a tool message with the result, and continue.
- If no tool_calls, assume the assistant's content is a JSON string; parse it and return.
- If tool calls exceed 10, stop and return whatever answer is available (or fallback).

## Testing
Two new tests:
1. Question: "How do you resolve a merge conflict?" – expects that `read_file` was called on `wiki/git-workflow.md` and that `source` field contains that file.
2. Question: "What files are in the wiki?" – expects that `list_files` was called on `wiki` and that `tool_calls` includes that call.
