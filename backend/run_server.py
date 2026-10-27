"""
MedIntel AI — Dual-Stack Server Launcher
Binds a dual-stack IPv4/IPv6 socket on port 8000 so that both 127.0.0.1,
::1, and LAN IP connections work reliably with ADB reverse on Windows.
"""

import socket
import sys
import uvicorn
from app.main import app


def main():
    port = 8000
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    except (AttributeError, OSError):
        pass
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("::", port))
    sock.listen(128)
    print(f"MedIntel AI Dual-Stack Server listening on port {port} (IPv4 + IPv6 + LAN)")
    sys.stdout.flush()
    config = uvicorn.Config(app, log_level="info", access_log=True)
    server = uvicorn.Server(config)
    server.run(sockets=[sock])


if __name__ == "__main__":
    main()
