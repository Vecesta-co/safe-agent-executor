"""REST API server for safe-agent-executor."""
from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding="utf-8")

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from .executor import SafeAgentExecutor
from .tools import TOOL_REGISTRY

EXECUTOR = SafeAgentExecutor()
TRACE_CACHE = []

class SafeAgentHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _json(self, data, status=200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._json({"status": "ok", "tools": list(TOOL_REGISTRY.keys())})
        elif parsed.path == "/tools":
            tools_data = {k: v["def"].model_dump() for k, v in TOOL_REGISTRY.items()}
            self._json(tools_data)
        elif parsed.path == "/traces":
            self._json([t.model_dump() for t in TRACE_CACHE])
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")

        if parsed.path == "/execute":
            goal = body.get("goal", "compute 10 + 10")
            dry_run = body.get("dry_run", False)
            auto_approve = body.get("auto_approve", False)

            def approver(tool, args):
                return auto_approve

            exec_inst = SafeAgentExecutor(approval_callback=approver)
            trace = exec_inst.run(goal, dry_run=dry_run)
            TRACE_CACHE.append(trace)
            self._json(trace.model_dump(), 200)
        else:
            self._json({"error": "not found"}, 404)

def run_server(host="0.0.0.0", port=8080):
    server = HTTPServer((host, port), SafeAgentHandler)
    print(f"Safe Agent Executor server running on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
