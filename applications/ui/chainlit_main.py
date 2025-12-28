"""Main entry point for Chainlit UI."""
# This file is used to run Chainlit: chainlit run src/app/ui/chainlit_main.py
# Or use: python run_chainlit.py from project root
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / ".env"
load_dotenv(env_path)

from .chainlit_app import set_supervisor
from ..services.agent_service import get_agent_service

# Initialize agent service and get supervisor
agent_service = get_agent_service()
agent_service.initialize()

# Set supervisor in chainlit app
supervisor = agent_service.get_supervisor()
set_supervisor(supervisor)

