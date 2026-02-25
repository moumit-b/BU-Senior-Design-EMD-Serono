import sys
import os
import asyncio

# Monkeypatch BioMCP to disable SSL verification
try:
    import biomcp.http_client as hc
    import biomcp.http_client_simple as hcs
    
    # Patch http_client.call_http
    orig_call_http = hc.call_http
    async def patched_call_http(method, url, params=None, **kwargs):
        # Force verify=False for httpx
        kwargs['verify'] = False
        return await orig_call_http(method, url, params, **kwargs)
    hc.call_http = patched_call_http
    
    # Patch http_client_simple.execute_http_request
    orig_execute = hcs.execute_http_request
    async def patched_execute(method, url, **kwargs):
        # Force verify=False for httpx
        kwargs['verify'] = False
        return await orig_execute(method, url, **kwargs)
    hcs.execute_http_request = patched_execute
    
    print("[BioMCP Patch] SSL verification disabled for biomcp.http_client and biomcp.http_client_simple", file=sys.stderr)
except ImportError as e:
    print(f"[BioMCP Patch] Warning: Could not patch BioMCP SSL: {e}", file=sys.stderr)

# Now run the BioMCP server
try:
    from biomcp.cli.server import run_server
    if __name__ == "__main__":
        # run_server defaults to stdio mode
        run_server()
except ImportError as e:
    print(f"[BioMCP Patch] Error: Could not import run_server: {e}", file=sys.stderr)
    sys.exit(1)
