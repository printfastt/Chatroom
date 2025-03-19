import socket

HOST = '127.0.0.1'
PORT = 11259

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

print("Connected to the server. Type a command:")

while True:
    command = input("> ").strip()
    parts = command.split(maxsplit=2)

    if command.startswith("login "):
        if len(parts) != 3:
            print("Error: Usage -> login <username> <password>")
            continue

    elif command.startswith("newuser "):
        if len(parts) != 3:
            print("Error: Usage -> newuser <username> <password>")
            continue
        username, password = parts[1], parts[2]
        if not (3 <= len(username) <= 32 and 4 <= len(password) <= 8):
            print("Error: Username must be 3-32 characters, password 4-8 characters.")
            continue

    elif command == "logout":
        pass

    elif command.startswith("send "):
        if len(parts) < 2:
            print("Error: Usage -> send <message>")
            continue
        if len(parts[1]) > 256:
            print("Error: Message must be 1-256 characters.")
            continue

    elif command == "who":
        pass

    else:
        print("Error: Invalid command.")
        continue

    client_socket.sendall(command.encode())
    response = client_socket.recv(1024).decode()
    print(f"{response}")

    if command.lower() == "logout" and response == "Logout successful.":
        print("Disconnected from the server")
        client_socket.close()
        break
