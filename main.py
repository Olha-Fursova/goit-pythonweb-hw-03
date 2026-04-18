from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
from datetime import datetime
import pathlib
import mimetypes
from jinja2 import Environment, FileSystemLoader

BASE_DIR = pathlib.Path()
STORAGE_DIR = BASE_DIR / "storage"
DATA_FILE = STORAGE_DIR / "data.json"

env = Environment(loader=FileSystemLoader("templates"))

class HttpHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    pr_url = urllib.parse.urlparse(self.path)

    if pr_url.path == "/":
      self.send_html_file("index.html")
    elif pr_url.path == "/message":
      self.send_html_file("message.html")
    
    elif pr_url.path == "/read":
      self.render_read_page()

    else:
      if pathlib.Path().joinpath(pr_url.path[1:]).exists():
        self.send_static()
      else:
        self.send_html_file("error.html", 404)

  def do_POST(self):
    data = self.rfile.read(int(self.headers["Content-Length"]))
    data_parse = urllib.parse.unquote_plus(data.decode())

    data_dict = {
      key: value for key, value in [el.split("=") for el in data_parse.split("&")]
    }

    self.save_data(data_dict)
    self.send_response(302)
    self.send_header("Location", "/")
    self.end_headers()

  def send_html_file(self, filename, status=200):
    self.send_response(status)
    self.send_header("Content-type", "text/html")
    self.end_headers()

    with open(filename, "rb") as fd:
      self.wfile.write(fd.read())

  def send_static(self):
    self.send_response(200)
    mt = mimetypes.guess_type(self.path)
    if mt:
      self.send_header("Content-type", mt[0])
    else:
      self.send_header("Content-type", "text/plain")

    self.end_headers()

    with open(f".{self.path}", "rb") as file:
      self.wfile.write(file.read())

  def save_data(self, data):
    STORAGE_DIR.mkdir(exist_ok=True)

    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        json_data = json.load(f)
    except:
      json_data = {}

    json_data[str(datetime.now())] = data

    with open(DATA_FILE, "w", encoding="utf-8") as f:
      json.dump(json_data, f, indent=4, ensure_ascii=False)
    
  def render_read_page(self):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        messages = json.load(f)
    except:
      messages = {}

    template = env.get_template("read.html")
    output = template.render(messages=messages)
    
    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()

    self.wfile.write(output.encode("utf-8"))


def run():
  server_address = ("", 3000)
  http = HTTPServer(server_address, HttpHandler)
  print("Server running on http://localhost:3000")

  try:
    http.serve_forever()
  except KeyboardInterrupt:
    http.server_close()

if __name__ == "__main__":
  run()