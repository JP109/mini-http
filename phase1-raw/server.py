import socket

HOST = ''
PORT = 8080

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

print(f"Listening on port {PORT}...")

try:
    client_socket, addr = server_socket.accept()
    print(f"Connection from {addr}")

    data = client_socket.recv(4096)
    print("--- RAW BYTES ---")
    print(data)
    print("--- DECODED ---")
    print(data.decode('utf-8', errors='replace'))

    client_socket.close()
except KeyboardInterrupt:
    pass
finally:
    server_socket.close()