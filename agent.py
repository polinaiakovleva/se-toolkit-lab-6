cat > agent.py << 'EOF'
#!/usr/bin/env python3
"""
Simple CLI agent that calls an LLM and returns a JSON response.
Usage: uv run agent.py "Your question here"
"""

import os
import sys
import json
import logging
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

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

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": question}],
            timeout=60,
        )
        answer = response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        sys.exit(1)

    result = {"answer": answer, "tool_calls": []}
    print(json.dumps(result, ensure_ascii=False))
    logger.info("Done")

if __name__ == "__main__":
    main()
EOF
