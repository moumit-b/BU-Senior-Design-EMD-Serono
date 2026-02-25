#!/usr/bin/env python3
"""
Bio MCP Server Wrapper - Runs biomcp-python in stdio mode.
This server provides access to biomedical databases through the biomcp SDK.

SSL Certificate Handling:
  On corporate networks (e.g., Merck), proxy servers may inject self-signed
  certificates that cause SSL verification failures when BioMCP calls NCBI,
  ClinicalTrials.gov, MyGene.info, etc.

  Set one of these in your .env or environment:
    BIOMCP_DISABLE_SSL=true   - Disable SSL verification (corporate proxies)
    SSL_CERT_PATH=/path/cert  - Use a custom CA certificate bundle (PEM file)
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

    # Build environment, passing through SSL config vars
    env = os.environ.copy()

    # Option 1: Custom CA certificate bundle (preferred for production)
    custom_cert = env.get("SSL_CERT_PATH", "")
    if custom_cert and os.path.isfile(custom_cert):
        env["SSL_CERT_FILE"] = custom_cert
        sys.stderr.write(f"[BioMCP] Using custom SSL cert: {custom_cert}\n")
        sys.stderr.flush()

    # Option 2: Disable SSL verification entirely (corporate proxy workaround)
    elif env.get("BIOMCP_DISABLE_SSL", "").lower() == "true":
        sys.stderr.write("[BioMCP] SSL verification disabled via BIOMCP_DISABLE_SSL\n")
        sys.stderr.flush()

        # Launch BioMCP via a tiny patch script that monkeypatches call_http
        patch_script = os.path.join(os.path.dirname(__file__), "_biomcp_no_ssl.py")
        result = subprocess.run(
            [venv_python, patch_script],
            stderr=sys.stderr,
            stdout=sys.stdout,
            stdin=sys.stdin,
            env=env
        )
        sys.exit(result.returncode)

    sys.stderr.write(f"Starting BioMCP server via: {venv_python}\n")
    sys.stderr.flush()

    result = subprocess.run(
        [venv_python, "-m", "biomcp", "run"],
        stderr=sys.stderr,
        stdout=sys.stdout,
        stdin=sys.stdin,
        env=env
    )
    sys.exit(result.returncode)
