"""Convenience script to run Chainlit UI."""
# Run from project root: python run_chainlit.py
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

if __name__ == "__main__":
    # Load environment variables
    project_root = Path(__file__).parent
    env_path = project_root / ".env"
    load_dotenv(env_path)
    
    # Get the chainlit_main.py file path
    chainlit_file = project_root / "applications" / "ui" / "chainlit_main.py"
    
    # Run chainlit using subprocess
    subprocess.run([
        sys.executable,
        "-m",
        "chainlit",
        "run",
        str(chainlit_file)
    ])

