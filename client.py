import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import os

OFFSHORE_HOST = os.getenv("OFFSHORE_HOST", "127.0.0.1")
OFFSHORE_PORT = int(os.getenv("OFFSHORE_PORT", 9999))

# Retry until the offshore server is available
def create_persistent_socket():
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((OFFSHORE_HOST, OFFSHORE_PORT))
            print(f"Connected to offshore proxy at {OFFSHORE_HOST}:{OFFSHORE_PORT}")
            return sock
        except Exception:
            print("Offshore server not ready, retrying in 3s...")
            time.sleep(3)

persistent_sock = create_persistent_socket()

def send_message(sock, msg_type, payload):
    length = len(payload)
    header = length.to_bytes(4, "big") + msg_type.to_bytes(1, "big")
    sock.sendall(header + payload)

def read_message(sock):
    header = sock.recv(5)
    if not header:
        return None, None
    length = int.from_bytes(header[:4], "big")
    msg_type = header[4]
    payload = b""
    while len(payload) < length:
        chunk = sock.recv(length - len(payload))
        if not chunk:
            break
        payload += chunk
    return msg_type, payload

def forward_raw(src, dst):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        try: src.close()
        except: pass
        try: dst.close()
        except: pass

class ProxyHandler(BaseHTTPRequestHandler):
    def do_CONNECT(self):
        tunnel_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tunnel_sock.connect((OFFSHORE_HOST, OFFSHORE_PORT))
        req_line = f"CONNECT {self.path} HTTP/1.1\r\n\r\n".encode()
        send_message(tunnel_sock, 0, req_line)
        _, resp_bytes = read_message(tunnel_sock)
        self.wfile.write(resp_bytes)

        if b"200 Connection Established" in resp_bytes:
            t1 = threading.Thread(target=forward_raw, args=(self.connection, tunnel_sock))
            t2 = threading.Thread(target=forward_raw, args=(tunnel_sock, self.connection))
            t1.start()
            t2.start()
            t1.join()
            t2.join()

    def do_GET(self): self.forward_request()
    def do_POST(self): self.forward_request()
    def do_PUT(self): self.forward_request()
    def do_DELETE(self): self.forward_request()

    def forward_request(self):
        req_line = f"{self.command} {self.path} {self.request_version}\r\n".encode()
        headers = b"".join([f"{k}: {v}\r\n".encode() for k, v in self.headers.items()])
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b""
        payload = req_line + headers + b"\r\n" + body

        send_message(persistent_sock, 0, payload)
        _, resp_bytes = read_message(persistent_sock)
        self.wfile.write(resp_bytes)

def run():
    server = HTTPServer(("0.0.0.0", 8080), ProxyHandler)
    print("Ship proxy running on port 8080...")
    server.serve_forever()

if __name__ == "__main__":
    run()
