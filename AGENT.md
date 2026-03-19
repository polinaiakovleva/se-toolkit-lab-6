cat > AGENT.md << 'EOF'
# Agent CLI

## Overview
Simple CLI agent that sends a question to an LLM and returns JSON.

## LLM Provider
- **Provider**: Ollama + LiteLLM on VM
- **Base URL**: `http://10.93.25.70:8000/v1`
- **Model**: `ollama/qwen2.5-coder:1.5b`
- **Authentication**: API key (`sk-123`) via `Authorization: Bearer`.

## Configuration
Create `.env.agent.secret`:
LLM_API_KEY=3537
LLM_API_BASE=http://10.93.25.70:8000/v1
LLM_MODEL=ollama/qwen2.5-coder:7b


## Usage
```bash
uv run agent.py "What is REST?"


""

