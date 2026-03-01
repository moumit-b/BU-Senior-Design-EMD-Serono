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
        sys.stderr.write(f"[BioMCP] Error: Python executable not found at {venv_python}\n")
        sys.stderr.write(f"[BioMCP] Please check your virtual environment setup.\n")
        sys.stderr.flush()
        sys.exit(1)

    # Build environment, passing through SSL config vars
    env = os.environ.copy()
    
    # Load environment variables from .env file if available
    try:
        from dotenv import load_dotenv
        from pathlib import Path
        env_path = Path(__file__).parent / '..' / '..' / 'streamlit-app' / '.env'
        if env_path.exists():
            # Load .env into a temp dict and merge with current env
            temp_env = {}
            load_dotenv(dotenv_path=env_path, override=True, interpolate=True)
            # Get the value after loading
            biomcp_disable = os.getenv("BIOMCP_DISABLE_SSL", "")
            if biomcp_disable:
                env["BIOMCP_DISABLE_SSL"] = biomcp_disable
                sys.stderr.write(f"[BioMCP] Loaded BIOMCP_DISABLE_SSL={biomcp_disable} from .env\n")
    except ImportError:
        pass
    except Exception as e:
        sys.stderr.write(f"[BioMCP] Warning: Could not load .env file: {e}\n")

    # Option 1: Disable SSL verification entirely (corporate proxy workaround) - CHECK FIRST!
    if env.get("BIOMCP_DISABLE_SSL", "").lower() == "true":
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

    # Option 2: Custom CA certificate bundle (fallback for production)
    custom_cert = env.get("SSL_CERT_PATH", "")
    
    # Auto-detect Merck certificates if not explicitly set
    if not custom_cert:
        # Look for combined certificate file in certs directory
        possible_certs = [
            os.path.join(os.path.dirname(__file__), '..', '..', 'streamlit-app', 'certs', 'merck_group_combined_cert.crt'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'streamlit-app', 'certs', 'certs.pem'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'streamlit-app', 'certs', 'ssldecrypt2022.pem')
        ]
        
        for cert_path in possible_certs:
            if os.path.isfile(cert_path):
                custom_cert = os.path.abspath(cert_path)
                sys.stderr.write(f"[BioMCP] Auto-detected SSL cert: {custom_cert}\n")
                break
    
    if custom_cert and os.path.isfile(custom_cert):
        env["SSL_CERT_FILE"] = custom_cert
        env["REQUESTS_CA_BUNDLE"] = custom_cert
        env["CURL_CA_BUNDLE"] = custom_cert
        sys.stderr.write(f"[BioMCP] Using custom SSL cert: {custom_cert}\n")
        sys.stderr.flush()

    # If we get here, use default SSL behavior
    else:
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
