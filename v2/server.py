import socket
import threading
import time

HOST = '127.0.0.1'
PORT = 11259

users = {}
active_users = {}
file_created = False
MAXCLIENTS = 3
MAXMESSAGEBYTES = 1024
EXIT_SENTINEL = '7F3K9P2Q1SJ438FJAU3JFK' #random sentinel value for 
num_connections = 0





"""
Loads user credentials from 'users.txt' into the global users dictionary.  
Creates the file if missing and warns on formatting errors.  
"""
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




"""
Saves a user and password to 'users.txt'.  
Appends to the file unless it's newly created and empty.  
"""
def save_user(user, password):
    global file_created
    with open("users.txt", "r+") as file:
        content = file.read().rstrip()
        if file_created and isFileEmpty(file):
            file.write(f"({user}, {password})")
        else:
            file.write(f"\n({user}, {password})")
    file_created = False






"""
Checks if a file is empty by reading the first line.  
Restores the file pointer to its original position.  
"""
def isFileEmpty(file):
    current_pos = file.tell()
    file.seek(0)
    first_line = file.readline().strip()
    file.seek(current_pos)
    return first_line == ""





"""
Sends a message to all active users except the specified one.  
Silently ignores failed send attempts.  
"""

def broadcast(message, exclude_user=None):
    for username, (conn, addr) in active_users.items():
        if username != exclude_user:
            try:
                conn.sendall((message).encode())
            except:
                pass





"""
Handles user login by verifying credentials and updating active users.  
Denies login if already logged in or credentials are incorrect.  
"""

def handle_login(command, conn, addr, user):
    global active_users
    if user is not None:
        conn.sendall(b">> Denied. Already logged in.")
        return user
    else:
        _, username, password = command.split()
        if username in active_users:
            conn.sendall(b">> Denied. User already logged in.")
            return user
        if username in users and users[username] == password:
            active_users[username] = (conn, addr)
            conn.sendall(b">> Login Confirmed.")
            broadcast(f">> {username.strip()} joins.", exclude_user=username)
            print(f"Addr {addr} logged in to {username}")
            return username
        else:
            conn.sendall(b">> Denied. Username or password incorrect.")





"""
Creates a new user account if the username is not taken.  
Denies request if the user is already logged in.  
"""
def handle_newuser(command, conn, user):
    _, newusername, password = command.split()
    if user in active_users:
        conn.sendall(b">> Denied. Already logged in.")
        return
    if newusername in users:
        conn.sendall(f">> Denied. {newusername} already exists.".encode())
        return
    users[newusername] = password
    save_user(newusername, password)
    conn.sendall(b">> New user account created. Please login.")




"""
Logs out a user, removes them from active users, and updates connections.  
Notifies others and closes the connection.  
"""
def handle_logout(conn, user):
    global num_connections
    global active_users
    if user in active_users:
        print(f"Client {user} : {addr} logged out.")
        conn.sendall(EXIT_SENTINEL.encode())
        del active_users[user]
        broadcast(f">> {user} left.", exclude_user=user)
        num_connections = num_connections - 1
        print(f"Number of connections: {num_connections}")
        conn.close()

    
"""
Handles sending messages to all users or a specific user.  
Sends private messages if a target user is specified.  
"""
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
                if user.strip() != target.strip():
                    target_conn.sendall(f"> {user} [private]: {message}".encode())
                    conn.sendall(f"> {user} (to {target}): {message}".encode())
                else:
                    conn.sendall(f"> {user} (to {target}): {message}".encode())
                    time.sleep(.01)
                    target_conn.sendall(f"> {user} [private]: {message}".encode())
            except Exception as a:
                conn.sendall(b">> Error sending message.")
                print(a)
        else:
            conn.sendall(b">> Denied. User is not online.")



"""
Lists active users if the requester is logged in.  
Denies request if the user is not authenticated.  
"""
def handle_who(conn, user):
    if user in active_users:
        if active_users:
            user_list = " ".join(active_users.keys())
            conn.sendall(user_list.encode())
        else:
            conn.sendall(b">> No active logged-in users.")
    else:
        conn.sendall(b">> Denied. Please login first.")



"""
Handles a client's connection, processing commands in a continuous loop.  

Manages user authentication, messaging, and session handling.  
- Receives and decodes messages from the client.  
- Processes commands such as login, new user creation, sending messages, listing active users, and logout.  
- Handles unexpected disconnections by removing the user from active sessions and broadcasting their departure.  
- Ensures only logged-in users can send messages or access user-related features.  

Closes the connection when the client disconnects or encounters an error.  
"""
def handle_client(conn, addr):
    user = None
    global num_connections
    while True:
        try:
            data = conn.recv(MAXMESSAGEBYTES).decode().strip()
            print(f">> {user}: {data}")
            if data.strip() == "":
                print(f"User {user}:{addr} force quit.")
                num_connections = num_connections - 1
                print(f"Number of connections: {num_connections}")
                conn.close()
                break
            test = data.split()
            if not data:
                break
        except:
            break
        if data.startswith("/login "):
            user = handle_login(data, conn, addr, user)
        elif data.startswith("/newuser "):
            handle_newuser(data, conn, user)
        elif data == "/logout":
            if user == None:
                conn.sendall(b">> Denied. Please login first.")
            else:
                handle_logout(conn,user)
        elif data.startswith("/send "):
            if user == None:
                conn.sendall(b">> Denied. Please login first.")
            else:
                handle_send(data, conn, user)
        elif data == "/who":
            handle_who(conn,user)

    conn.close()
    if user and user in active_users:
        del active_users[user]
        broadcast(f">> {user} left.", exclude_user=user)





server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET specified ipv4, SOCK_STREAM specifies TCP
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #removes the timeout period to reuse an address/port.
server_socket.bind((HOST, PORT))
server_socket.listen(MAXCLIENTS)
print(f"Server listening on {HOST}:{PORT}...")
load_users()



"""
Accepts incoming client connections and manages the chat server.  

- Listens for new client connections and spawns a thread to handle each client.  
- Enforces a connection limit (`MAXCLIENTS`) by rejecting excess clients with a message.  
- Increments and tracks the number of active connections.  
- Gracefully handles errors, printing exceptions and shutting down the server if necessary.  
- Closes the server socket when the loop exits.  
"""
while True:
    try:
        conn, addr = server_socket.accept()
        print(f"Client {addr} connected...")
        if num_connections <= MAXCLIENTS:
            threading.Thread(target=handle_client, args=(conn, addr)).start()
            if num_connections == MAXCLIENTS:
                conn.sendall(b"Server full. Try again later")
                time.sleep(.01)
                conn.sendall(EXIT_SENTINEL.encode())
                conn.close()
                print(f"Chatroom full. Rejecting client (connections = {num_connections})")

            else:
                num_connections = num_connections + 1
                print(f"Number of connections: {num_connections}")

    except Exception as e:
        print(f"Error: {e}")
        print("Exiting...")
        break


server_socket.close()