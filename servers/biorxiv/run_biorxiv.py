#!/usr/bin/env python3
"""
bioRxiv MCP Server Wrapper - Runs biorxiv_server.py in stdio mode.
"""

import sys
import os
import subprocess

if __name__ == "__main__":
    # Get the path to the venv python interpreter
    venv_dir = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'streamlit-app',
        'venv'
    )
    
    if os.name == 'nt':  # Windows
        venv_python = os.path.join(venv_dir, 'Scripts', 'python.exe')
    else:  # macOS/Linux
        venv_python = os.path.join(venv_dir, 'bin', 'python')

    venv_python = os.path.normpath(venv_python)
    
    if not os.path.isfile(venv_python):
        sys.stderr.write(f"[bioRxiv] Error: Python executable not found at {venv_python}\n")
        sys.exit(1)

    # Build environment
    env = os.environ.copy()
    
    # Load environment variables from .env file if available
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        env_path = Path(__file__).parent / '..' / '..' / 'streamlit-app' / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
    except ImportError:
        pass

    # Handle SSL verification if requested (common in Merck environment)
    biomcp_disable = os.getenv("BIOMCP_DISABLE_SSL", "").lower() == "true"
    if biomcp_disable:
        env["PYTHONHTTPSVERIFY"] = "0"
        sys.stderr.write("[bioRxiv] SSL verification disabled via BIOMCP_DISABLE_SSL\n")

    # Run the server
    server_script = os.path.join(os.path.dirname(__file__), "biorxiv_server.py")
    
    result = subprocess.run(
        [venv_python, server_script],
        stderr=sys.stderr,
        stdout=sys.stdout,
        stdin=sys.stdin,
        env=env,
        cwd=os.path.dirname(__file__)
    )
    sys.exit(result.returncode)
