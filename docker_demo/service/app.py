from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os


PORT = int(os.environ.get("PORT", "8080"))


class DemoServiceHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/health":
            self.sendJson(
                200,
                {
                    "status": "healthy",
                    "service": "resolve-demo-service"
                }
            )
            return

        if self.path == "/":
            self.sendJson(
                200,
                {
                    "message": "ReSolve demo service is running.",
                    "healthEndpoint": "/health"
                }
            )
            return

        self.sendJson(
            404,
            {
                "error": "Not found"
            }
        )

    def sendJson(self, statusCode, payload):
        body = json.dumps(payload).encode("utf-8")

        self.send_response(statusCode)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)

    def log_message(self, format, *args):
        print(
            "[resolve-demo-service]",
            format % args
        )


def main():
    server = HTTPServer(
        ("0.0.0.0", PORT),
        DemoServiceHandler
    )

    print(
        f"ReSolve demo service listening on port {PORT}"
    )

    server.serve_forever()


if __name__ == "__main__":
    main()
