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
    """Test that the agent uses read_file on wiki/git-workflow.md for merge conflict question."""
    result = subprocess.run(
        [sys.executable, "agent.py", "How do you resolve a merge conflict?"],
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
    # Проверяем, что был вызов read_file с git-workflow.md
    found_read_file = any(
        call["tool"] == "read_file" and "git-workflow.md" in call["args"].get("path", "")
        for call in output["tool_calls"]
    )
    assert found_read_file, "Expected read_file on git-workflow.md"
    # source должен содержать этот файл
    assert "git-workflow.md" in output["source"]

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

if __name__ == "__main__":
    test_basic()
    test_merge_conflict()
    test_list_files()
    print("All tests passed!")