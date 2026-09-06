import socket
import os

HOST = ''
PORT = 8080
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')

MIME_TYPES = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.txt': 'text/plain',
    '.json': 'application/json',
}
DEFAULT_MIME_TYPE = 'application/octet-stream'


class Request:
    def __init__(self, method, path, version, headers):
        self.method = method
        self.path = path
        self.version = version
        self.headers = headers

    def __repr__(self):
        return f"Request(method={self.method!r}, path={self.path!r}, version={self.version!r}, headers={self.headers!r})"


class ClientDisconnected(Exception):
    """Raised when the client closes the connection instead of sending a new request."""
    pass


def parse_request(client_file):
    request_line_bytes = client_file.readline()

    if request_line_bytes == b'':
        raise ClientDisconnected()

    request_line = request_line_bytes.decode('utf-8').rstrip('\r\n')
    method, path, version = request_line.split(' ')

    headers = {}
    while True:
        line = client_file.readline().decode('utf-8').rstrip('\r\n')
        if line == '':
            break
        name, value = line.split(':', 1)
        headers[name.strip()] = value.strip()

    return Request(method, path, version, headers)


def build_response(status_code, status_text, body, content_type='text/plain', extra_headers=None):
    return build_response_bytes(status_code, status_text, body.encode('utf-8'), content_type, extra_headers)


def build_response_bytes(status_code, status_text, body_bytes, content_type='application/octet-stream', extra_headers=None):
    response_lines = [
        f"HTTP/1.1 {status_code} {status_text}",
        f"Content-Type: {content_type}",
        f"Content-Length: {len(body_bytes)}",
    ]
    if extra_headers:
        for name, value in extra_headers.items():
            response_lines.append(f"{name}: {value}")
    response_lines.append("")
    response_lines.append("")
    header_bytes = "\r\n".join(response_lines).encode('utf-8')
    return header_bytes + body_bytes


# --- Route handlers ---

def handle_hello(request):
    return build_response(200, "OK", f"You requested: {request.path}\n")


ROUTES = {
    '/hello': handle_hello,
}


# --- Static file serving ---

def get_mime_type(path):
    _, ext = os.path.splitext(path)
    return MIME_TYPES.get(ext, DEFAULT_MIME_TYPE)


def serve_static_file(request_path):
    if request_path == '/':
        request_path = '/index.html'

    relative_path = request_path.lstrip('/')
    full_path = os.path.abspath(os.path.join(STATIC_DIR, relative_path))

    if not full_path.startswith(STATIC_DIR + os.sep) and full_path != STATIC_DIR:
        return None

    if not os.path.isfile(full_path):
        return None

    with open(full_path, 'rb') as f:
        body_bytes = f.read()

    content_type = get_mime_type(full_path)
    return build_response_bytes(200, "OK", body_bytes, content_type)


def not_found():
    return build_response(404, "Not Found", "404 - page not found\n")


def route_request(request):
    handler = ROUTES.get(request.path)
    if handler:
        return handler(request)

    static_response = serve_static_file(request.path)
    if static_response is not None:
        return static_response

    return not_found()


# --- Connection handling ---

def client_wants_close(request):
    connection_header = request.headers.get('Connection', '').lower()
    if connection_header == 'close':
        return True
    if request.version == 'HTTP/1.0' and connection_header != 'keep-alive':
        return True
    return False


def handle_connection(client_socket, addr):
    client_file = client_socket.makefile('rb')

    try:
        while True:
            try:
                request = parse_request(client_file)
            except ClientDisconnected:
                print(f"{addr} disconnected")
                break

            print(request)

            should_close = client_wants_close(request)

            response = route_request(request)

            extra_headers = {'Connection': 'close' if should_close else 'keep-alive'}
            response = attach_connection_header(response, extra_headers['Connection'])

            client_socket.sendall(response)

            if should_close:
                print(f"{addr} closing (Connection: close)")
                break
    except (ConnectionResetError, BrokenPipeError):
        print(f"{addr} connection reset")
    finally:
        client_socket.close()


def attach_connection_header(response_bytes, connection_value):
    header_end = response_bytes.index(b'\r\n\r\n')
    headers_part = response_bytes[:header_end].decode('utf-8')
    body_part = response_bytes[header_end:]
    headers_part += f"\r\nConnection: {connection_value}"
    return headers_part.encode('utf-8') + body_part


# --- Server loop ---

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

print(f"Listening on port {PORT}...")
print(f"Serving static files from {STATIC_DIR}")

try:
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        handle_connection(client_socket, addr)
except KeyboardInterrupt:
    pass
finally:
    server_socket.close()