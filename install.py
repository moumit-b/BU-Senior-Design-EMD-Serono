#!/usr/bin/env python3
"""
install.py — One-shot cross-platform setup for the Pharma Research Intelligence System.

Run this once on a new machine from the repo root:
    python install.py          # Windows
    python3 install.py         # macOS / Linux

What it does:
  1. Checks Python and Node.js versions
  2. Creates a Python virtual environment inside streamlit-app/venv
  3. Installs all Python dependencies (pip install -r requirements.txt)
  4. Installs uv / uvx (required for BioContext KB MCP server)
  5. Runs npm install in every MCP server directory
  6. Runs npm run build for TypeScript servers (pubchem-augmented)
  7. Scaffolds a .env file if one doesn't exist
  8. Prints a clear summary of what's ready vs. what still needs manual steps

Supported platforms: Windows 10/11, macOS (Intel + Apple Silicon), Linux
"""

import os
import sys
import subprocess
import shutil

# Force UTF-8 output on Windows (cp1252 can't print ✓ ✗ ⚠ etc.)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path

# ── Platform detection ─────────────────────────────────────────────────────────
IS_WINDOWS = os.name == "nt"
IS_MACOS   = sys.platform == "darwin"
IS_LINUX   = sys.platform.startswith("linux")

# ── Paths ──────────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).parent.resolve()
APP_DIR     = REPO_ROOT / "streamlit-app"
VENV_DIR    = APP_DIR / "venv"
REQ_FILE    = APP_DIR / "requirements.txt"
ENV_FILE    = APP_DIR / ".env"
ENV_EXAMPLE = APP_DIR / ".env.example"
SERVERS_DIR = REPO_ROOT / "servers"

# Node.js MCP servers that need npm install
NODE_SERVERS = [
    "pubchem-augmented",   # TypeScript — also needs a build step
    "literature",
    "data_analysis",
    "web_knowledge",
    "medrxiv",
    "biorxiv",
    "opentargets",
    "stringdb",
]

# Servers that need a build step after npm install (TypeScript → JS)
BUILD_SERVERS = {
    "pubchem-augmented": ["npm", "run", "build"],
}

# ── macOS PATH augmentation ────────────────────────────────────────────────────
# Homebrew installs node/npm to /opt/homebrew/bin (Apple Silicon) or
# /usr/local/bin (Intel). These may not be in PATH when running via python3
# directly (especially in non-login shells / IDEs).
if IS_MACOS:
    _homebrew_paths = [
        "/opt/homebrew/bin",   # Apple Silicon (M1/M2/M3)
        "/opt/homebrew/sbin",
        "/usr/local/bin",      # Intel Homebrew
        "/usr/local/sbin",
    ]
    current_path = os.environ.get("PATH", "")
    extra = [p for p in _homebrew_paths if p not in current_path and Path(p).is_dir()]
    if extra:
        os.environ["PATH"] = ":".join(extra) + ":" + current_path

# ── Colours (stripped on Windows if not supported) ─────────────────────────────
def _supports_colour():
    if IS_WINDOWS:
        # Windows Terminal and modern VS Code support ANSI; classic cmd.exe does not
        return bool(os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM"))
    return sys.stdout.isatty()

GREEN  = "\033[92m" if _supports_colour() else ""
YELLOW = "\033[93m" if _supports_colour() else ""
RED    = "\033[91m" if _supports_colour() else ""
BOLD   = "\033[1m"  if _supports_colour() else ""
RESET  = "\033[0m"  if _supports_colour() else ""

def ok(msg):   print(f"  {GREEN}OK{RESET}  {msg}")
def warn(msg): print(f"  {YELLOW}WARN{RESET} {msg}")
def err(msg):  print(f"  {RED}FAIL{RESET} {msg}")
def step(msg): print(f"\n{BOLD}{msg}{RESET}")
def info(msg): print(f"       {msg}")

# ── Helpers ────────────────────────────────────────────────────────────────────
def run(cmd, cwd=None, env=None):
    """Run a command, return (returncode, stdout+stderr)."""
    result = subprocess.run(
        cmd, cwd=cwd, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        # Windows requires shell=True to resolve .cmd wrappers (npm.cmd, node.cmd).
        # macOS/Linux find executables directly on PATH.
        shell=IS_WINDOWS,
    )
    return result.returncode, result.stdout

def venv_python():
    if IS_WINDOWS:
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python3"

def venv_pip():
    if IS_WINDOWS:
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip3"

def venv_uvx():
    if IS_WINDOWS:
        return VENV_DIR / "Scripts" / "uvx.exe"
    return VENV_DIR / "bin" / "uvx"

# ── Step 1: Version checks ─────────────────────────────────────────────────────
def check_prerequisites():
    step("Step 1/5 — Checking prerequisites")
    all_ok = True

    # Python version
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 10):
        ok(f"Python {major}.{minor} (>= 3.10 required)")
    else:
        err(f"Python {major}.{minor} detected — Python 3.10+ required")
        all_ok = False

    # Node.js
    rc, out = run(["node", "--version"])
    if rc == 0:
        ver = out.strip()
        try:
            major_node = int(ver.lstrip("v").split(".")[0])
        except ValueError:
            major_node = 0
        if major_node >= 18:
            ok(f"Node.js {ver} (>= 18 required)")
        else:
            err(f"Node.js {ver} detected — Node.js 18+ required")
            if IS_MACOS:
                info("Install with Homebrew:  brew install node")
            else:
                info("Download from https://nodejs.org (LTS recommended)")
            all_ok = False
    else:
        err("Node.js not found")
        if IS_MACOS:
            info("Install with Homebrew:  brew install node")
            info("Don't have Homebrew?   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        else:
            info("Download from https://nodejs.org (LTS recommended)")
        all_ok = False

    # npm
    rc, out = run(["npm", "--version"])
    if rc == 0:
        ok(f"npm {out.strip()}")
    else:
        err("npm not found — usually bundled with Node.js")
        all_ok = False

    if not all_ok:
        print(f"\n{RED}Prerequisites not met. Fix the above and re-run.{RESET}")
        sys.exit(1)

# ── Step 2: Virtual environment ────────────────────────────────────────────────
def setup_venv():
    step("Step 2/5 — Python virtual environment")

    if VENV_DIR.exists():
        ok(f"venv already exists at {VENV_DIR}")
    else:
        info(f"Creating venv at {VENV_DIR} ...")
        rc, out = run([sys.executable, "-m", "venv", str(VENV_DIR)])
        if rc != 0:
            err(f"Failed to create venv:\n{out}")
            sys.exit(1)
        ok("venv created")

    # Upgrade pip — use 'python -m pip' to avoid Windows file-lock issues
    rc, out = run([str(venv_python()), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    if rc == 0:
        ok("pip upgraded")
    else:
        warn(f"pip upgrade failed (non-fatal):\n{out}")

# ── Step 3: Python dependencies ────────────────────────────────────────────────
def install_python_deps():
    step("Step 3/5 — Python dependencies")

    if not REQ_FILE.exists():
        err(f"requirements.txt not found at {REQ_FILE}")
        sys.exit(1)

    info("Running pip install -r requirements.txt (this may take a few minutes) ...")
    rc, out = run([str(venv_pip()), "install", "--quiet", "-r", str(REQ_FILE)])
    if rc == 0:
        ok("All Python packages installed")
    else:
        err("pip install failed. Output:")
        print(out)
        sys.exit(1)

# ── Step 3b: uv / uvx (required for BioContext KB MCP server) ─────────────────
def install_uv():
    step("Step 3b/5 — uv / uvx (required for BioContext KB)")

    # Check if uvx is already in the venv or on PATH
    uvx_in_venv = venv_uvx()
    if uvx_in_venv.exists():
        rc, out = run([str(uvx_in_venv), "--version"])
        if rc == 0:
            ok(f"uvx already in venv: {out.strip()}")
            return

    # Also check system PATH
    rc, out = run(["uvx", "--version"])
    if rc == 0:
        ok(f"uvx found on PATH: {out.strip()}")
        return

    info("Installing uv into venv (provides the uvx command) ...")
    rc, out = run([str(venv_pip()), "install", "--quiet", "uv"])
    if rc == 0:
        ok("uv installed — uvx command now available inside the venv")
    else:
        warn(f"uv installation failed (BioContext KB server may not start):\n{out}")

# ── Step 4: npm install for all MCP servers ────────────────────────────────────
def install_node_servers():
    step("Step 4/5 — Node.js MCP servers (npm install + build)")

    for name in NODE_SERVERS:
        server_dir = SERVERS_DIR / name
        if not server_dir.exists():
            warn(f"{name}: directory not found at {server_dir} — skipping")
            continue

        pkg_json = server_dir / "package.json"
        if not pkg_json.exists():
            warn(f"{name}: no package.json — skipping")
            continue

        node_modules = server_dir / "node_modules"
        if node_modules.exists():
            ok(f"{name}: already installed")
        else:
            info(f"{name}: running npm install ...")
            rc, out = run(["npm", "install", "--silent"], cwd=str(server_dir))
            if rc == 0:
                ok(f"{name}: installed")
            else:
                err(f"{name}: npm install failed:\n{out}")
                continue

        # Run build step if required (e.g., TypeScript compilation)
        build_cmd = BUILD_SERVERS.get(name)
        if build_cmd:
            build_output = server_dir / "build" / "index.js"
            if build_output.exists():
                ok(f"{name}: already built")
                continue

            info(f"{name}: running build ({' '.join(build_cmd)}) ...")
            rc_build, out_build = run(build_cmd, cwd=str(server_dir))
            if rc_build == 0:
                ok(f"{name}: built successfully")
            else:
                # On Windows, the build script contains 'chmod +x' which is a
                # no-op; check if the actual output file was produced anyway.
                if build_output.exists():
                    ok(f"{name}: built successfully (chmod warning ignored on Windows)")
                else:
                    err(f"{name}: build failed:\n{out_build}")

# ── Step 5: .env scaffolding ───────────────────────────────────────────────────
ENV_TEMPLATE = """\
# ─── LLM Provider ────────────────────────────────────────────────────────────
# Select which LLM to use: anthropic | ollama
LLM_PROVIDER=anthropic

# Anthropic (Claude) — get your key at https://console.anthropic.com
ANTHROPIC_API_KEY=

# Ollama (local) — only needed if LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=qwen3:235b-thinking

# ─── NCI Clinical Trials API ─────────────────────────────────────────────────
# Required for nci_intervention_searcher and nci_biomarker_searcher tools.
# Free key — register at: https://clinicaltrialsapi.cancer.gov/
NCI_API_KEY=

# ─── SSL (corporate / Merck network) ─────────────────────────────────────────
# If biomcp tools fail with SSL certificate errors, set this to true.
# For Merck networks, prefer SSL_CERT_PATH pointing to the combined cert bundle.
# BIOMCP_DISABLE_SSL=true
# SSL_CERT_PATH=/path/to/merck_group_combined_cert.crt

# ─── Tavily web search ────────────────────────────────────────────────────────
# Optional — enables web search in the chat agent.
# Free tier available at: https://tavily.com
# TAVILY_API_KEY=
"""

def setup_env():
    step("Step 5/5 — Environment file (.env)")

    if ENV_FILE.exists():
        ok(f".env already exists at {ENV_FILE}")
    else:
        ENV_FILE.write_text(ENV_TEMPLATE, encoding="utf-8")
        ok(f".env created at {ENV_FILE}")

    # Write .env.example (safe to commit)
    example_text = ENV_TEMPLATE.replace(
        "ANTHROPIC_API_KEY=\n",
        "ANTHROPIC_API_KEY=your_anthropic_key_here\n"
    ).replace(
        "NCI_API_KEY=\n",
        "NCI_API_KEY=your_nci_key_here\n"
    )
    ENV_EXAMPLE.write_text(example_text, encoding="utf-8")
    ok(f".env.example written at {ENV_EXAMPLE}")

# ── Final summary ──────────────────────────────────────────────────────────────
def print_summary():
    print(f"\n{'─'*60}")
    print(f"{BOLD}Setup complete.{RESET} Manual steps still required:\n")

    env_content = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else ""

    if "ANTHROPIC_API_KEY=" in env_content:
        val = [l.split("=", 1)[1].strip() for l in env_content.splitlines()
               if l.startswith("ANTHROPIC_API_KEY=")]
        if val and val[0]:
            ok("ANTHROPIC_API_KEY is set")
        else:
            warn("ANTHROPIC_API_KEY is empty — add your key to streamlit-app/.env")
            info("Get one at: https://console.anthropic.com")

    if "NCI_API_KEY=" in env_content:
        val = [l.split("=", 1)[1].strip() for l in env_content.splitlines()
               if l.startswith("NCI_API_KEY=")]
        if val and val[0]:
            ok("NCI_API_KEY is set — nci_* tools will work")
        else:
            warn("NCI_API_KEY is empty — nci_* tools will fail")
            info("Free key at: https://clinicaltrialsapi.cancer.gov/")

    # Platform-specific startup instructions
    if IS_WINDOWS:
        activate = r"venv\Scripts\activate"
        python_note = ""
    else:
        activate = "source venv/bin/activate"
        python_note = "  # macOS: use python3 if 'python' isn't found\n"

    print(f"""
{BOLD}To start the app:{RESET}
  cd streamlit-app
  {activate}
  {python_note}streamlit run app.py

{BOLD}First-run note:{RESET}
  BioContext KB downloads packages via uvx on its first connection.
  The app may take up to 3 minutes to finish initialising on first boot.
  Subsequent starts are near-instant.
""")

    if IS_MACOS:
        print(f"""{BOLD}macOS notes:{RESET}
  - If 'node' or 'npm' is not found, install Node.js via Homebrew:
      brew install node
  - WeasyPrint (PDF export) requires system libraries:
      brew install pango cairo gdk-pixbuf libffi
  - If you see SSL errors on biomcp tools, add to .env:
      BIOMCP_DISABLE_SSL=true
""")
    elif IS_WINDOWS:
        print(f"""{BOLD}Windows notes:{RESET}
  - WeasyPrint (PDF export) requires GTK3:
      https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
  - Run PowerShell / Windows Terminal as a regular user (not Administrator).
""")

# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    platform_label = "macOS" if IS_MACOS else ("Windows" if IS_WINDOWS else "Linux")
    print(f"\n{BOLD}Pharma Research Intelligence System — Installer{RESET}")
    print(f"Platform : {platform_label}")
    print(f"Repo root: {REPO_ROOT}\n")

    check_prerequisites()
    setup_venv()
    install_python_deps()
    install_uv()
    install_node_servers()
    setup_env()
    print_summary()
