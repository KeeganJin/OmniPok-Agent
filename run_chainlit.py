"""Convenience script to run Chainlit UI."""
# Run from project root: python run_chainlit.py
import sys
import subprocess
from pathlib import Path

if __name__ == "__main__":
    # Get the chainlit_main.py file path
    project_root = Path(__file__).parent
    chainlit_file = project_root / "src" / "app" / "ui" / "chainlit_main.py"
    
    # Run chainlit using subprocess
    subprocess.run([
        sys.executable,
        "-m",
        "chainlit",
        "run",
        str(chainlit_file)
    ])

