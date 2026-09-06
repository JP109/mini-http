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
    # Request line: "GET /hello HTTP/1.1"
    request_line = client_file.readline().decode('utf-8').rstrip('\r\n')
    method, path, version = request_line.split(' ')

    # Headers: one per line, until blank line
    headers = {}
    while True:
        line = client_file.readline().decode('utf-8').rstrip('\r\n')
        if line == '':
            break
        name, value = line.split(':', 1)
        headers[name.strip()] = value.strip()

    return Request(method, path, version, headers)


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

print(f"Listening on port {PORT}...")

try:
    client_socket, addr = server_socket.accept()
    print(f"Connection from {addr}")

    client_file = client_socket.makefile('rb')  # 'rb' - binary mode, readline() on raw bytes
    request = parse_request(client_file)

    print(request)

    client_socket.close()
except KeyboardInterrupt:
    pass
finally:
    server_socket.close()