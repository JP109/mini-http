import socket

HOST = ''
PORT = 8080


class Request:
    def __init__(self, method, path, version, headers):
        self.method = method
        self.path = path
        self.version = version
        self.headers = headers

    def __repr__(self):
        return f"Request(method={self.method!r}, path={self.path!r}, version={self.version!r}, headers={self.headers!r})"


def parse_request(client_file):
    request_line = client_file.readline().decode('utf-8').rstrip('\r\n')
    method, path, version = request_line.split(' ')

    headers = {}
    while True:
        line = client_file.readline().decode('utf-8').rstrip('\r\n')
        if line == '':
            break
        name, value = line.split(':', 1)
        headers[name.strip()] = value.strip()

    return Request(method, path, version, headers)


def build_response(status_code, status_text, body, content_type='text/plain'):
    body_bytes = body.encode('utf-8')
    response_lines = [
        f"HTTP/1.1 {status_code} {status_text}",
        f"Content-Type: {content_type}",
        f"Content-Length: {len(body_bytes)}",
        "",
        "",  # trailing blank line -> the \r\n\r\n after headers
    ]
    header_bytes = "\r\n".join(response_lines).encode('utf-8')
    return header_bytes + body_bytes


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

print(f"Listening on port {PORT}...")

try:
    client_socket, addr = server_socket.accept()
    print(f"Connection from {addr}")

    client_file = client_socket.makefile('rb')
    request = parse_request(client_file)
    print(request)

    response = build_response(200, "OK", "hello\n")
    client_socket.sendall(response)

    client_socket.close()
except KeyboardInterrupt:
    pass
finally:
    server_socket.close()