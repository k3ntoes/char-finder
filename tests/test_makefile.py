import os
import subprocess
from pathlib import Path

def test_makefile_exists():
    makefile_path = Path("Makefile")
    assert makefile_path.exists(), "Makefile does not exist at the project root"

def test_makefile_targets():
    makefile_path = Path("Makefile")
    content = makefile_path.read_text()
    
    expected_targets = ["help", "install", "run", "dev", "test", "clean"]
    for target in expected_targets:
        # Check if target is defined in any rule line (e.g. 'run dev:' or 'run:')
        found = any(line.strip().startswith(target) or target in line.split(':')[0].split() for line in content.splitlines() if ':' in line)
        assert found, f"Target '{target}' not found in Makefile"

def test_make_help():
    result = subprocess.run(["make", "help"], capture_output=True, text=True)
    assert result.returncode == 0, f"make help failed with output: {result.stderr}"
    assert "Available commands" in result.stdout
