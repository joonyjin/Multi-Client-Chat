import socket

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 55555
MESSAGE_SIZE = 1024

client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

client_sock.connect((SERVER_HOST, SERVER_PORT))
print(f'Successfully connected to Server: {SERVER_HOST}, {SERVER_PORT}')

while True:
    message = input(">>> ")
    client_sock.sendall(message.encode('utf-8'))
    message = client_sock.recv(MESSAGE_SIZE)
    print(f"Server: {message.decode()}")

client_sock.close()

