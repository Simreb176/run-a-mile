#!/usr/bin/env python3
"""Local preview server for the generated site.

Rebuilds `docs/` and serves it on 0.0.0.0:8080 so it is reachable at:
    http://simon-dev.rebecchi.uk:8080   (the development version)

(Run the deployed site from runamile.co.uk; this port is only for previews.)

Stop it with Ctrl+C.
"""
import http.server
import os
import socketserver
import subprocess
import sys
from pathlib import Path

# Port 8080 is the usual preview address. Set PORT to use a different one,
# e.g. `PORT=8090 .venv/bin/python serve.py`.
PORT = int(os.environ.get("PORT", 8080))
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
    class Server(socketserver.TCPServer):
        # Reuse the port immediately so a rapid restart isn't blocked by
        # leftover connections from the previous run.
        allow_reuse_address = True

    with Server(("0.0.0.0", PORT), handler) as httpd:
        print(f"\nServing {DOCS} on http://0.0.0.0:{PORT}")
        print(f"  development version: http://simon-dev.rebecchi.uk:{PORT}")
        print("Ctrl+C to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
