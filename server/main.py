import socket

HOST = '0.0.0.0'
PORT = 55555
MESSAGE_SIZE = 1024

parent_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
parent_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

parent_sock.bind((HOST, PORT))
parent_sock.listen(5)
print(f'Server running on IP: {HOST}, Port Num: {PORT} ...')

child_sock, child_addr = parent_sock.accept()
print(f'Accessed from {child_addr}')

try:
    while True:
        message = child_sock.recv(MESSAGE_SIZE)
        if not message:
            print(f'{child_addr} ended')
            break

        print(f'{child_addr}: {message.decode()}')
        child_sock.sendall(message)

except ConnectionResetError:
    print(f'Connection with {child_addr} has been forced to stop')

finally:
    child_sock.close()
    parent_sock.close()
    print('Server has closed')

