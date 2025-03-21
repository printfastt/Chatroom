"""
Carson Pautz
March 20 2025
Midterm Project v2
cwphv9
cs4850:networking
last 4 id: 1259
"""
import socket
import threading
import time

HOST = '127.0.0.1'
PORT = 11259
DEBUG = 'OFF' #'ON' or 'OFF'

users = {}
active_users = {}
file_created = False
MAXCLIENTS = 3
MAXMESSAGEBYTES = 1024
EXIT_SENTINEL = '7F3K9P2Q1SJ438FJAU3JFK'        #random sentinel value for 
THREAD_SENTINEL = 'FN4NS4JWN3LQK3NB3N2JF3'
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
        debugstatement("Users loaded successfully.")
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
                message = f"{THREAD_SENTINEL} {message}"
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
        conn.sendall(b"Denied. Already logged in.")
        return user
    else:


        try:
            _, username, password = command.split()
        except ValueError:
            conn.sendall(b"Error: Usage -> login <username> <password>")
            return user
        except Exception as e:
            debugstatement("Server error: ",e)
            return user


        if username in active_users:
            conn.sendall(b"Denied. User already logged in.")
            return user
        if username in users and users[username] == password:
            active_users[username] = (conn, addr)
            conn.sendall(b"login confirmed.")
            broadcast(f"{username.strip()} joins.", exclude_user=username)
            debugstatement(f"Addr {addr} logged in to {username}")
            return username
        else:
            conn.sendall(b"Denied. Username or password incorrect.")





"""
Creates a new user account if the username is not taken.  
Denies request if the user is already logged in.  
"""
def handle_newuser(command, conn, user):

    try:
        _, newusername, password = command.split()
    except ValueError:
        conn.sendall(b"Error: Usage -> newuser <username> <password>")
        return
    except Exception as e:
        debugstatement("Server error: ",e)
        return



    if user in active_users:
        conn.sendall(b"Denied. Already logged in.")
        return
    if newusername in users:
        conn.sendall(f"Denied. {newusername} already exists.".encode())
        return
    users[newusername] = password
    save_user(newusername, password)
    conn.sendall(b"New user account created. Please login.")




"""
Logs out a user, removes them from active users, and updates connections.  
Notifies others and closes the connection.  
"""
def handle_logout(conn, user):
    global num_connections
    global active_users
    if user in active_users:
        debugstatement(f"Client {user} : {addr} logged out.")
        print(f"{user} logout.")
        conn.sendall(EXIT_SENTINEL.encode())
        del active_users[user]
        broadcast(f"{user} left.", exclude_user=user)
        num_connections = num_connections - 1
        debugstatement(f"Number of connections: {num_connections}")
        conn.close()
        return True
    return False

    
"""
Handles sending messages to all users or a specific user.  
Sends private messages if a target user is specified.  
"""
def handle_send(command, conn, user):
    if user not in active_users:
        conn.sendall(b"Denied. Please login first.")
        return
    
    if command.strip() == "/send":
        conn.sendall(b"Server Error: Usage -> send all <message> OR send <username> <message>")
        return
    
    try:
        parts = command.split(maxsplit=2)
    except ValueError:
        conn.sendall(b"Server Error: Usage -> send all <message> OR send <username> <message>")
        return
    except Exception as e:
        conn.sendall(b"Server Error sending message.")
        debugstatement("Server error: ",e)
        return  
    
    if parts[1].strip() == "all":
        message = parts[2]
        broadcast(f"{user}: {message}", exclude_user=user)
        #conn.sendall(f"{user}: {message}".encode())
    else:
        target = parts[1]
        message = parts[2]
        if target in active_users:
            target_conn, _ = active_users[target]
            try:
                if user == target:
                    target_conn.sendall(f"{user}: {message}".encode())
                else:
                    target_conn.sendall(f"{THREAD_SENTINEL} {user}: {message}".encode())
                print(f"{user} (to {target}): {message}")
            except Exception as a:
                conn.sendall(b"Server Error: message couldn't be completed.")
                debugstatement("Server error: ",a)
        else:
            conn.sendall(b"Denied. User is not online.")



"""
Lists active users if the requester is logged in.  
Denies request if the user is not authenticated.  
"""
def handle_who(conn, user):
    if user in active_users:
        if active_users:
            user_list = ", ".join(active_users.keys())
            conn.sendall(user_list.encode())
        else:
            conn.sendall(b"No active logged-in users.")
    else:
        conn.sendall(b"Denied. Please login first.")

def debugstatement(message):
    if DEBUG == 'ON':
        print(f"=->{message}")
    else:
        pass   


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
            debugstatement(f">> {user}: {data}")


            if data.strip() == "":
                debugstatement(f"User {user}:{addr} force quit.")
                num_connections = num_connections - 1
                debugstatement(f"Number of connections: {num_connections}")
                conn.close()
                break
        except OSError:
            debugstatement("Server full. Closing thread: {addr}")
            return
        except TypeError:
            debugstatement("Server full. Closing thread: {addr}")
            return
        except Exception as e:
            debugstatement("Sever error: ",e)            
            break


        if data.startswith("/login "):
            user = handle_login(data, conn, addr, user)
        elif data.startswith("/newuser "):
            handle_newuser(data, conn, user)
        elif data == "/logout":
            if handle_logout(conn,user):
                break
        elif data.startswith("/send "):
            if user == None:
                conn.sendall(b"Denied. Please login first.")
            else:
                handle_send(data, conn, user)
        elif data == "/who":
            handle_who(conn,user)

    conn.close()
    if user and user in active_users:
        del active_users[user]
        broadcast(f"{user} left.", exclude_user=user)







server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET specified ipv4, SOCK_STREAM specifies TCP
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #removes the timeout period to reuse an address/port.
server_socket.bind((HOST, PORT))
server_socket.listen(MAXCLIENTS)
debugstatement(f"Server listening on {HOST}:{PORT}...")
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
        debugstatement(f"Client {addr} connected...")
        if num_connections <= MAXCLIENTS:
            threading.Thread(target=handle_client, args=(conn, addr)).start()
            if num_connections == MAXCLIENTS:
                conn.sendall(b"Server full. Try again later")
                time.sleep(.01)
                conn.sendall(EXIT_SENTINEL.encode())
                conn.close()
                debugstatement(f"Chatroom full. Rejecting client (connections = {num_connections})")

            else:
                num_connections = num_connections + 1
                debugstatement(f"Number of connections: {num_connections}")

    except Exception as e:
        debugstatement(f"Server Error: {e}")
        break


server_socket.close()