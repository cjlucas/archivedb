import sys
sys.path.insert(0, "/Users/chris/repos/archivedb")
import archivedb.config as config
import socket
import archivedb.http.api

from gzip import GzipFile

try: import simplejson as json
except ImportError: import json

#_py3 = config._py3
_py3 = sys.version_info > (3,)
if _py3:
    from urllib.parse import urlsplit, parse_qs
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from io import BytesIO
else:
    from urlparse import urlsplit, parse_qs
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
    from StringIO import StringIO


class APIHandler(BaseHTTPRequestHandler):
    def add_header(self, key, value):
        self.out_headers[key] = value

    def _process_headers(self):
        # default headers
        self.add_header("Vary", "Accept-encoding")

        # support gzip compression
        if "gzip" in self.headers.get("Accept-Encoding", ""):
            self.add_header("Content-encoding", "gzip")
            self._use_compression = True
        else: self._use_compression = False

    def _send_headers(self):
        if hasattr(self, "out_headers"):
            for k in self.out_headers.keys():
                self.send_header(k, self.out_headers[k])

        self.end_headers()

    def _handle_json(self, results):
        if isinstance(results, (dict, list, tuple, bool, int)):
            results = json.dumps(results)
            self.add_header("Content-type", "application/json")
        else:
            self.add_header("Content-type", "text/plain")

        return(results)

    def _process_output(self, results):
        # TODO: handle exceptions raised by json
        results = self._handle_json(results)

        if _py3:
            # GzipFile and wfile both expect bytes in Python 3
            f = BytesIO()
            if isinstance(results, str): results = bytes(results, "utf-8")
        else: f = StringIO()

        #print(results)

        if self._use_compression:
            g = GzipFile(fileobj=f, mode="wb")
            g.write(results)
            g.close()
        else:
            f.write(results)

        f.seek(0)
        self.output = f.read()

    def _check_url(self):
        if len(self.path_split) == 3:
            doc_root, api_name, method_name = self.path_split[:3]
            api_dict = archivedb.http.api._find_apis()
            print(doc_root)
            print(api_name)
            print(method_name)
            print(api_dict)
        else:
            self.output = "invalid url"
            return

        api_dict = archivedb.http.api._api_dict

        if doc_root != "api":
            self.output = "invalid url"
        elif api_name not in api_dict:
            self.output = "'{0}' is not a valid api".format(self.path_split[1])
        elif method_name not in getattr(api_dict.get(api_name), "public_methods"):
            self.output = "'{0}' is not a valid method.".format(method_name)

    def do_GET(self):
        """ Handle GET request """
        self.parse_result = urlsplit(self.path)
        self.path = self.parse_result.path.lower()
        self.path_split = self.path.strip("/").split("/")
        self.query = self.parse_result.query
        self.out_headers = {}
        self.output = None

        self._process_headers()
        self._check_url()

        # test stuff
        print(self.path)
        print(self.client_address)
        print(self.sys_version)
        print(self.command)

        # if _check_url() found an error, write it and return
        if self.output is not None:
            self.wfile.write(self.output)
            return

        if self.output is not None: self._process_output(self.output)

        self.send_response(200)
        self._send_headers()

        if self.output is not None: self.wfile.write(self.output)

def run():
    ip = socket.gethostbyname(socket.gethostname())
    httpd = HTTPServer((ip, 9999), APIHandler)
    httpd.serve_forever()


if __name__ == '__main__':
    #print()
    run()
