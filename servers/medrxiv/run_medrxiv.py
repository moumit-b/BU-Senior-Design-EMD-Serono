#!/usr/bin/env python3
"""
medRxiv MCP Server Wrapper - Runs medrxiv_server.py in stdio mode.
"""

import sys
import os
import subprocess

if __name__ == "__main__":
    # Get the path to the venv python interpreter (cross-platform)
    venv_dir = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'streamlit-app',
        'venv'
    )
    
    # Cross-platform venv python path detection
    if os.name == 'nt':  # Windows
        venv_python = os.path.join(venv_dir, 'Scripts', 'python.exe')
    else:  # macOS/Linux
        venv_python = os.path.join(venv_dir, 'bin', 'python')

    # Normalize the path
    venv_python = os.path.normpath(venv_python)
    
    # Verify the python executable exists
    if not os.path.isfile(venv_python):
        sys.stderr.write(f"[medRxiv] Error: Python executable not found at {venv_python}\n")
        sys.stderr.flush()
        sys.exit(1)

    # Build environment
    env = os.environ.copy()
    
    # SSL Handling (similar to BioMCP if needed, but requests usually follows environment)
    # Merck-specific SSL handling can be added here if medRxiv API fails in Merck network

    server_script = os.path.join(os.path.dirname(__file__), "medrxiv_server.py")
    
    sys.stderr.write(f"Starting medRxiv server via: {venv_python}\n")
    sys.stderr.flush()

    result = subprocess.run(
        [venv_python, server_script],
        stderr=sys.stderr,
        stdout=sys.stdout,
        stdin=sys.stdin,
        env=env,
        cwd=os.path.dirname(__file__)
    )
    sys.exit(result.returncode)
