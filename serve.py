#!/usr/bin/env python3
"""Local preview server for the generated site.

Rebuilds `docs/` and serves it on 0.0.0.0:8083 so it is reachable at:
    http://192.168.1.124:8083   (local network)
    http://dev.rebecchi.uk:8083 (tailnet)

Stop it with Ctrl+C.
"""
import http.server
import socketserver
import subprocess
import sys
from pathlib import Path

PORT = 8083
ROOT = Path(__file__).parent
DOCS = ROOT / "docs"


def build():
    print("Building site...")
    subprocess.run([sys.executable, str(ROOT / "generate.py")], check=True)


def main():
    build()
    if not DOCS.exists():
        sys.exit("No docs/ directory — run generate.py first.")

    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(
        *args, directory=str(DOCS), **kwargs
    )
    with socketserver.TCPServer(("0.0.0.0", PORT), handler) as httpd:
        print(f"\nServing {DOCS} on http://0.0.0.0:{PORT}")
        print(f"  local network: http://192.168.1.124:{PORT}")
        print(f"  tailnet:       http://dev.rebecchi.uk:{PORT}")
        print("Ctrl+C to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
