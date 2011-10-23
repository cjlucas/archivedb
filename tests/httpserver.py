from gzip import GzipFile
from urllib.parse import urlparse, parse_qs
import http.server
import socket
import json
import io

class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        """ Handle GET request """

        parse_result = urlparse(self.path)
        self.path = parse_result.path
        self.query = parse_result.query

        # support gzip compression
        if "gzip" in self.headers.get("Accept-Encoding"):
            use_gzip = True
        else:
            use_gzip = False

        if self.path == "/":
            self.args = parse_qs(self.query)
            b = io.BytesIO()
            j = bytes(json.dumps(self.args), "utf-8")

            if use_gzip:
                f = GzipFile(fileobj=b, mode="wb")
                f.write(j)
                f.close()
            else:
                b.write(j)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Vary", "Accept-encoding")
            if use_gzip: self.send_header("Content-encoding", "gzip")
            self.end_headers()

            b.seek(0)
            self.wfile.write(b.read())


if __name__ == '__main__':
    ip = socket.gethostbyname(socket.gethostname())
    httpd = http.server.HTTPServer((ip, 9999), MyHandler)
    httpd.serve_forever()
