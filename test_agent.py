import subprocess
import json
import sys

def test_basic():
    """Test that the agent returns valid JSON with answer and tool_calls (empty)."""
    result = subprocess.run(
        [sys.executable, "agent.py", "What is 2+2?"],
        capture_output=True,
        text=True,
        timeout=70
    )
    assert result.returncode == 0, f"Agent failed: {result.stderr}"
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        assert False, f"stdout is not valid JSON: {result.stdout}"
    assert "answer" in output
    assert "tool_calls" in output
    assert isinstance(output["tool_calls"], list)

def test_merge_conflict():
    """Test that the agent uses read_file on wiki files for merge conflict question."""
    result = subprocess.run(
        [sys.executable, "agent.py", "How do you resolve a merge conflict?"],
        capture_output=True,
        text=True,
        timeout=120
    )
    assert result.returncode == 0, f"Agent failed: {result.stderr}"
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        assert False, f"stdout is not valid JSON: {result.stdout}"
    assert "answer" in output
    assert "source" in output
    assert "tool_calls" in output
    # Check that read_file was called on a wiki file
    found_read_file = any(
        call["tool"] == "read_file" and "wiki" in call["args"].get("path", "")
        for call in output["tool_calls"]
    )
    assert found_read_file, "Expected read_file on wiki files"
    # source should contain a wiki file
    assert "wiki" in output["source"] or output["source"] == ""

def test_list_files():
    """Test that the agent uses list_files on wiki directory."""
    result = subprocess.run(
        [sys.executable, "agent.py", "What files are in the wiki?"],
        capture_output=True,
        text=True,
        timeout=70
    )
    assert result.returncode == 0, f"Agent failed: {result.stderr}"
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        assert False, f"stdout is not valid JSON: {result.stdout}"
    assert "answer" in output
    assert "source" in output
    assert "tool_calls" in output
    found_list_files = any(
        call["tool"] == "list_files" and "wiki" in call["args"].get("path", "")
        for call in output["tool_calls"]
    )
    assert found_list_files, "Expected list_files on wiki"

def test_framework_question():
    """Test that the agent uses read_file for framework questions."""
    result = subprocess.run(
        [sys.executable, "agent.py", "What framework does the backend use?"],
        capture_output=True,
        text=True,
        timeout=120
    )
    assert result.returncode == 0, f"Agent failed: {result.stderr}"
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        assert False, f"stdout is not valid JSON: {result.stdout}"
    assert "answer" in output
    assert "tool_calls" in output
    # Should use read_file on source code
    found_read_file = any(
        call["tool"] == "read_file"
        for call in output["tool_calls"]
    )
    assert found_read_file, "Expected read_file to be called"
    # Answer should mention FastAPI
    assert "fastapi" in output["answer"].lower(), "Answer should mention FastAPI"

def test_items_count():
    """Test that the agent uses query_api for database questions."""
    result = subprocess.run(
        [sys.executable, "agent.py", "How many items are in the database?"],
        capture_output=True,
        text=True,
        timeout=120
    )
    assert result.returncode == 0, f"Agent failed: {result.stderr}"
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        assert False, f"stdout is not valid JSON: {result.stdout}"
    assert "answer" in output
    assert "tool_calls" in output
    # Should use query_api
    found_query_api = any(
        call["tool"] == "query_api" and "/items" in call["args"].get("path", "")
        for call in output["tool_calls"]
    )
    assert found_query_api, "Expected query_api to be called on /items"

if __name__ == "__main__":
    test_basic()
    test_merge_conflict()
    test_list_files()
    test_framework_question()
    test_items_count()
    print("All tests passed!")