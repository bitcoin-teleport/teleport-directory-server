
import http.server
from urllib.parse import parse_qs

from datetime import datetime, timedelta
from calendar import timegm
import time

import threading

#a relatively small amount at first, because theres no antispam
#then later we'll increase it a lot to reduce the frequency at
#which people need to hit the server
#once fidelity bonds get in we can perhaps use the locktimes of them
#or since the locktime will be several months, maybe x10 less
#e.g. locktime is 24 months, set expiry to be 2.4 months
TIME_TO_LIVE_DAYS = 1

ERROR_TEXT = "Something went wrong"

NETWORKS = ["mainnet", "testnet", "signet"]

allowed_txt_files = ["/makers-" + n + ".txt" for n in NETWORKS]
allowed_pages = allowed_txt_files + ["/received", "/submitmaker.html"]

file_lock = threading.Lock()

class TeleportDirectoryServerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in allowed_pages:
            response_code = 200
            if self.path == "/received":
                page = "<html><h1>Received your submission. Directory will update shortly.</h1>" \
                    + "Expiry unix time = <b>" + str(self.expiry_unixtime) + "</b></html>"
            else:
                return super().do_GET()
        else:
            response_code = 404
            page = "<html><h1>" + ERROR_TEXT + "</h1></html>"
        self.send_response(response_code)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(page))
        self.end_headers()
        self.wfile.write(page.encode('utf-8'))

    def do_POST(self):
        self.expiry_unixtime = 0
        if self.path != "/directoryserver" or "Content-Length" not in self.headers:
            self.path = "error"
            return self.do_GET()
        try:
            int(self.headers["Content-Length"])
        except:
            self.path = "error"
            return self.do_GET()
        if int(self.headers["Content-Length"]) > 200: #arbitrary max length
            self.path = "error"
            return self.do_GET()

        body = self.rfile.read(int(self.headers["Content-Length"]))
        post_data = parse_qs(body.decode())
        #post_data = {'address': ['myhiddenservice.onion:6102'], 'net': ['testnet']}

        address = None
        net = None
        try:
            address = post_data["address"][0].replace(",", "")
            net = post_data["net"][0]
        except:
            self.path = "error"
            return self.do_GET()
        expiry_datetime = datetime.now() + timedelta(days=TIME_TO_LIVE_DAYS)
        self.expiry_unixtime = timegm(expiry_datetime.timetuple())
        filename = "makers-"  + net + ".txt"
        with file_lock:
            refreshed_entry = False
            entries = []
            try:
                with open(filename, "r") as fd:
                    filedata = fd.read()
                    for file_entry in filedata.split("\n"):
                        if file_entry.find(",") == -1:
                            continue
                        file_address = file_entry.split(",")[1]
                        if address == file_address:
                            refreshed_entry = True
                            entries.append(str(self.expiry_unixtime) + "," + address)
                            print("[" + datetime.now().strftime("%Y-%m-%d %X")
                                + "] maker refreshed: " + address)
                        else:
                            entries.append(file_entry)
            except FileNotFoundError:
                pass
            if refreshed_entry:
                with open(filename, "w") as fd:
                    fd.write("\n".join(entries) + "\n")
            else:
                with open(filename, "a") as fd:
                    fd.write(str(self.expiry_unixtime) + "," + address + "\n")
                print("[" + datetime.now().strftime("%Y-%m-%d %X")
                    + "] maker added: " + address)
        self.path = "/received"
        return self.do_GET()

class ExpiryThread(threading.Thread):
    def run(self):
        filenames = ["makers-"  + net + ".txt" for net in NETWORKS]
        while True:
            time.sleep(60 * 30)
            with file_lock:
                for filename in filenames:
                    at_least_one_expiry = False
                    remaining_entries = []
                    try:
                        with open(filename, "r") as fd:
                            filedata = fd.read()
                            for file_entry in filedata.split("\n"):
                                if file_entry.find(",") == -1:
                                    continue
                                expiry_unixtime = int(file_entry.split(",")[0])
                                expiry_datetime = (datetime.utcfromtimestamp(0) +
                                    timedelta(seconds=expiry_unixtime))
                                if datetime.now() > expiry_datetime:
                                    print("[" + datetime.now().strftime("%Y-%m-%d %X")
                                        + "] maker expired: " + str(file_entry))
                                    at_least_one_expiry = True
                                else:
                                    remaining_entries.append(file_entry)
                    except FileNotFoundError:
                        continue
                    if at_least_one_expiry:
                        with open(filename, "w") as fd:
                            fd.write("\n".join(remaining_entries) + "\n")

expiry_thread = ExpiryThread()
expiry_thread.daemon = True
expiry_thread.start()

hostport = ("localhost", 8080)
httpd = http.server.HTTPServer(hostport, TeleportDirectoryServerHandler)
print("serving forever on " + str(hostport))
httpd.serve_forever()
