"""Main entry point for Chainlit UI."""
# This file is used to run Chainlit: chainlit run src/app/ui/chainlit_main.py
# Or use: python run_chainlit.py from project root
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from src.app.ui.chainlit_app import set_supervisor
    from src.agent.core import global_registry
    from src.agent.orchestration import Supervisor, SimpleRouter
    from src.agent.tools import http_get, http_post, http_put, http_delete
except ImportError:
    # Fallback to relative imports if absolute imports fail
    from .chainlit_app import set_supervisor
    from ...agent.core import global_registry
    from ...agent.orchestration import Supervisor, SimpleRouter
    from ...agent.tools import http_get, http_post, http_put, http_delete

# Initialize tools on import
global_registry.register(
    name="http_get",
    description="Make an HTTP GET request",
    func=http_get
)
global_registry.register(
    name="http_post",
    description="Make an HTTP POST request",
    func=http_post
)
global_registry.register(
    name="http_put",
    description="Make an HTTP PUT request",
    func=http_put
)
global_registry.register(
    name="http_delete",
    description="Make an HTTP DELETE request",
    func=http_delete
)

# Initialize supervisor
router = SimpleRouter()
supervisor = Supervisor(agents=[], router=router)

# Set supervisor in chainlit app
set_supervisor(supervisor)

