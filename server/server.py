import socket
import threading
import http.client

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

def handle_connection(conn):
    while True:
        try:
            msg_type, payload = read_message(conn)
            if not payload:
                break

            request_line = payload.split(b"\r\n", 1)[0].decode()

            if request_line.startswith("CONNECT"):
                host_port = request_line.split(" ")[1]
                host, port = host_port.split(":")
                port = int(port)
                try:
                    remote = socket.create_connection((host, port))
                    response = b"HTTP/1.1 200 Connection Established\r\n\r\n"
                    send_message(conn, 1, response)
                    t1 = threading.Thread(target=forward_raw, args=(conn, remote))
                    t2 = threading.Thread(target=forward_raw, args=(remote, conn))
                    t1.start()
                    t2.start()
                    t1.join()
                    t2.join()
                except Exception as e:
                    err = f"HTTP/1.1 502 Bad Gateway\r\n\r\n{e}".encode()
                    send_message(conn, 1, err)
                break

            else:
                lines = payload.split(b"\r\n")
                method, url, version = lines[0].decode().split(" ")
                headers = {}
                body = b""

                empty_index = lines.index(b"")
                for h in lines[1:empty_index]:
                    key, val = h.decode().split(":", 1)
                    headers[key.strip()] = val.strip()
                if empty_index + 1 < len(lines):
                    body = b"\r\n".join(lines[empty_index+1:])

                host = headers.get("Host")
                conn_type = http.client.HTTPConnection(host, 80, timeout=10)
                conn_type.request(method, url, body, headers)
                resp = conn_type.getresponse()
                resp_bytes = f"HTTP/1.1 {resp.status} {resp.reason}\r\n".encode()
                for k, v in resp.getheaders():
                    resp_bytes += f"{k}: {v}\r\n".encode()
                resp_bytes += b"\r\n" + resp.read()
                send_message(conn, 1, resp_bytes)

        except Exception:
            break

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 9999))
    server.listen(5)
    print("Offshore proxy running on port 9999...")
    while True:
        conn, addr = server.accept()
        print("Client connected:", addr)
        threading.Thread(target=handle_connection, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    main()
