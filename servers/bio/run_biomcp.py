#!/usr/bin/env python3
"""
Bio MCP Server Wrapper - Runs biomcp-python in stdio mode.
This server provides access to biomedical databases through the biomcp SDK.
"""

import sys
import os
import subprocess

if __name__ == "__main__":
    # Get the path to the venv python interpreter
    venv_python = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'streamlit-app',
        'venv',
        'Scripts',
        'python.exe'
    )

    # Normalize the path
    venv_python = os.path.normpath(venv_python)

    sys.stderr.write(f"Starting BioMCP server via: {venv_python}\n")
    sys.stderr.flush()

    # Run biomcp using the venv python
    # Use subprocess to execute: python -m biomcp run
    result = subprocess.run(
        [venv_python, "-m", "biomcp", "run"],
        stderr=sys.stderr,
        stdout=sys.stdout,
        stdin=sys.stdin
    )

    sys.exit(result.returncode)
