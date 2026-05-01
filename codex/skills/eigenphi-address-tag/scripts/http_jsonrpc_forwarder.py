#!/usr/bin/env python3

import argparse
import json
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def build_request(upstream: str, body: bytes, content_type: str):
    req = urllib.request.Request(upstream, data=body, method="POST")
    req.add_header("Content-Type", content_type or "application/json")
    return req


class ForwardHandler(BaseHTTPRequestHandler):
    upstream = ""

    def _write_json_error(self, code: int, message: str):
        payload = json.dumps({"error": message}).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "application/json")

        try:
            req = build_request(self.upstream, body, content_type)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as exc:
            data = exc.read()
            self.send_response(exc.code)
            self.send_header("Content-Type", exc.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as exc:
            self._write_json_error(502, f"upstream rpc proxy failed: {exc}")

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--listen-port", type=int, default=8545)
    parser.add_argument("--upstream", required=True)
    args = parser.parse_args()

    handler = type("BoundForwardHandler", (ForwardHandler,), {"upstream": args.upstream})

    class ReusableThreadingHTTPServer(ThreadingHTTPServer):
        allow_reuse_address = True

    server = ReusableThreadingHTTPServer((args.listen_host, args.listen_port), handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
