import socket

HOST = '127.0.0.1'
PORT = 11259

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #declares new variable of type socket, with AF_INET for ipv4 and SOCK_STREAM for TCP.
client_socket.connect((HOST, PORT)) #binds host and port.

print("Connected to the server. Type a command:")

while True:
    command = input("> ")

    client_socket.sendall(command.encode())                      #sends client commands.
    response = client_socket.recv(1024).decode()                #receives server responses.
    print(f"{response}")

    if command.lower() == "logout" and response == "Logout successful.": #confirms response from server, then breaks connection and ends program.
        print("Disconnected from the server")
        client_socket.close()
        break

