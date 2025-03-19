import socket
import threading

HOST = '127.0.0.1'
PORT = 11259

users = {}
active_users = {}
file_created = False
MAXCLIENTS = 3

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
        if file_created and isFileEmpty(file):
            file.write(f"({user}, {password})")
        else:
            file.write(f"\n({user}, {password})")
    file_created = False

def isFileEmpty(file):
    current_pos = file.tell()
    file.seek(0)
    first_line = file.readline().strip()
    file.seek(current_pos)
    return first_line == ""


def broadcast(message, exclude_user=None):
    for username, (conn, addr) in active_users.items():
        if username != exclude_user:
            try:
                conn.sendall((message).encode())
            except:
                pass


def handle_login(command, conn, addr, user):
    global active_users
    if user is not None:
        conn.sendall(b"Denied. Already logged in.")
        return user
    else:
        _, username, password = command.split()
        if username in users and users[username] == password:
            active_users[username] = (conn, addr)
            conn.sendall(b"Login Confirmed")
            print(username)
            broadcast(f"Sever: {username.strip()} joins.", exclude_user=username)
            return username
        else:
            conn.sendall(b"Denied. Username or password incorrect.\n")


def handle_newuser(command, conn, user):
    _, newusername, password = command.split()
    if user in active_users:
        conn.sendall(b"Denied. Already logged in.")
        return
    users[newusername] = password
    save_user(newusername, password)
    conn.sendall(b"New user account created. Please login.")

def handle_logout(conn, user):
    global active_users
    if user in active_users:
        print(f"Client {user} : {addr} logged out.")
        conn.sendall(b"Logout successful.")
        del active_users[user]
        #broadcast(f"Server: {user} left.", exclude_user=user)
        conn.close()

    

def handle_send(command, conn, user):
    parts = command.split(maxsplit=2)

    if parts[1].lower().strip() == "all":
        message = parts[2]
        broadcast(f"> {user}: {message}")
    else:
        target = parts[1]
        message = parts[2]
        if target in active_users:
            target_conn, _ = active_users[target]
            try:
                target_conn.sendall(f"[private] {user}: {message}".encode())
                #conn.sendall(f"{user} (to {target}): {message}".encode())
            except:
                conn.sendall(b"Error sending message")
        else:
            conn.sendall(b"Denied. User is not online.")
            

def handle_who(conn):
    if active_users:
        user_list = " ".join(active_users.keys())
        conn.sendall(user_list.encode())
    else:
        conn.sendall(b"No active logged-in users.")



####NOTE
####NOTE
####NOTE
####CARSON
####YOU NEED TO REPLACE A LOT OF SENDALL'S WITH A LOT OF BROADCASTS.



def handle_client(conn, addr):
    user = None
    while True:
        print(f"mainloop:{user}")
        try:
            data = conn.recv(1024).decode().strip()
            print(f"{user}:{data}")
            if not data:
                break
        except:
            break

        if data.startswith("login "):
            print(f"if login:{user}")
            user = handle_login(data, conn, addr, user)
            

        elif data.startswith("newuser "):
            handle_newuser(data, conn, user)

        elif data == "logout":
            print(f"if logout:{user}")
            if user == None:
                conn.sendall(b"Denied. Please login first.")
            else:
                handle_logout(conn,user)

        elif data.startswith("send "):
            if user == None:
                conn.sendall(b"Denied. Please login first.")
            else:
                handle_send(data, conn, user)

        elif data == "who":
            handle_who(conn)

    conn.close()
    if user and user in active_users:
        del active_users[user]
        broadcast(f"Server: {user}left.", exclude_user=user)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(MAXCLIENTS)
print(f"Server listening on {HOST}:{PORT}...")
load_users()

while True:
    conn, addr = server_socket.accept()
    print(f"Client {addr} connected...")
    threading.Thread(target=handle_client, args=(conn, addr)).start()
