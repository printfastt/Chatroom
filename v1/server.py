"""
Carson Pautz
March 20 2025
Midterm Project
cwphv9
cs4850:networking
last 4 id: 1259
"""

import socket

HOST = '127.0.0.1'
PORT = 11259

users = {}
current_user = None
file_created = False

def load_users():
    global users, file_created
    try:
        with open("users.txt", "r") as file:
            for line in file:
                username, password = line.strip("()\n").split(", ")
                users[username] = password
        print("Users loaded successfully.")
    except FileNotFoundError:
        print("users.txt not found. Creating a new one.")
        open("users.txt", "w").close()
        file_created = True
    except ValueError:
        print("Warning: users.txt not formatted correctly.")

def save_user(user, password):
    global file_created
    with open("users.txt", "r+") as file:
        content = file.read().rstrip()
        if file_created:
            file.write(f"({user}, {password})")
        else:
            file.write(f"\n({user}, {password})")
    file_created = False

def handle_login(command, conn):
    global current_user
    _, user, password = command.split()
    if current_user is not None:
        conn.sendall(b"Denied. Already logged in.")
        return
    if user in users and users[user] == password:
        current_user = user
        conn.sendall(b"login confirmed")
    else:
        conn.sendall(b"Denied. User name or password incorrect.")

def handle_newuser(command, conn):
    global current_user
    _, user, password = command.split()
    if current_user is not None:
        conn.sendall(b"Denied. Already logged in.")
        return
    users[user] = password
    save_user(user, password)
    conn.sendall(b"New user account created. Please login.")

def handle_logout(conn):
    global current_user
    if current_user is None:
        conn.sendall(b"Denied. Please login first.")
        return False
    else:
        print(f"Client {current_user}:{addr} logged out.")
        current_user = None
        conn.sendall(b"Logout successful.")
        conn.close()
        return True

def handle_send(command, conn):
    global current_user
    if current_user is None:
        conn.sendall(b"Denied. Please login first.")
        return
    _, message = command.split(maxsplit=1)
    response = f"{current_user}: {message}"
    conn.sendall(response.encode())

def handle_who(command, conn):
    if current_user is None:
        conn.sendall(b"You are logged out.")
    else:
        message = f"{current_user, {addr}}"
        conn.sendall(message.encode())

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Server listening on {HOST}:{PORT}...")
load_users()

while True:
    if current_user is None:
        print("Waiting for client...")
        conn, addr = server_socket.accept()
        print(f"Connected by {addr}")

        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            print(f"Received: {data}")

            if data.startswith("login "):
                handle_login(data, conn)
            elif data.startswith("newuser "):
                handle_newuser(data, conn)
            elif data == "logout":
                if handle_logout(conn):
                    break
            elif data.startswith("send "):
                handle_send(data, conn)
            elif data == "who":
                handle_who(data, conn)
            else:
                conn.sendall(b"Invalid command.")
