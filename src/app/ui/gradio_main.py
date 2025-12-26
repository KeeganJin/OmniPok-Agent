"""Main entry point for Gradio UI."""
import sys
from .gradio_app import launch_gradio

if __name__ == "__main__":
    # Parse command line arguments
    share = "--share" in sys.argv
    port = 7860
    host = "0.0.0.0"
    
    # Parse port if provided
    if "--port" in sys.argv:
        try:
            port_idx = sys.argv.index("--port")
            port = int(sys.argv[port_idx + 1])
        except (ValueError, IndexError):
            pass
    
    # Parse host if provided
    if "--host" in sys.argv:
        try:
            host_idx = sys.argv.index("--host")
            host = sys.argv[host_idx + 1]
        except IndexError:
            pass
    
    launch_gradio(share=share, server_name=host, server_port=port)

