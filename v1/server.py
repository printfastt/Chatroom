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
EXITSENTINEL = 'G7WJ4N3S' #sentinel code to confirm proper logout to client.

users = {}
current_user = None
file_created = False

"""
load_users():
responsible for loading users.txt.
    if no users.txt, create one
        set file_created = True to tell save_users to not print a newline before next entry.
"""
def load_users():
    global users, file_created
    try:
        with open("users.txt", "r") as file:
            for line in file:
                username, password = line.strip("()\n").split(", ")
                users[username] = password
    except FileNotFoundError:
        print("users.txt not found. Creating a new one.")
        open("users.txt", "w").close()
        file_created = True
    except ValueError:
        print("Warning: users.txt not formatted correctly.")
    except Exception as e:
        print(e)

"""
save_user():
responsible for formatting input into users.txt.
    sets file_created to False. will be false for the rest of the program.

"""
def save_user(user, password):
    global file_created
    with open("users.txt", "r+") as file:
        content = file.read().rstrip()
        if file_created:
            file.write(f"({user}, {password})")
        else:
            file.write(f"\n({user}, {password})")
    file_created = False



"""
handle_login():
responsible for handling login commands.
    if current_user
        deny for already logged in

    if user and password is correct, no current_user, and user exists in users.txt, confirm login.
        else pw or username is incorrect.

    if somehow an improper command was not caught by client side, try blocks prevent the server from crashing.
"""
def handle_login(command, conn):
    global current_user

    #try block since split() is prone to erroring out
    try:
        _, user, password = command.split()
    except ValueError:
        conn.sendall(b"Server Error: Usage -> login <username> <password>")
        return
    except Exception as e:
        conn.sendall(b"Denied. Incorrect usage")
        print(e)
        return

    if current_user is not None:
        conn.sendall(b"Denied. Already logged in.")
        return
    if user in users and users[user] == password:
        current_user = user
        conn.sendall(b"login confirmed")
        print(f"{current_user} login.")
    else:
        conn.sendall(b"Denied. User name or password incorrect.")





"""
handle_newuser():
responsible for handling newuser commands.
    if there is a current_user, deny for already logged in.
    if username already exists, deny for account already exists.
    otherwise, confirm newuser to server console and client.

    if somehow an improper command was not caught by client side, try blocks prevent the server from crashing.
"""
def handle_newuser(command, conn):
    global current_user

    try:
        _, user, password = command.split()
    except ValueError:
        conn.sendall(b"Server Error: Usage -> newuser <username> <password>")
        return
    except Exception as e:
        print(e)
        conn.sendall(b"Denied. Incorrect usage")
        return

    if current_user is not None:
        conn.sendall(b"Denied. Already logged in.")
        return
    elif user in users:
        conn.sendall(b"Denied. User account already exists.")
        return
    users[user] = password
    save_user(user, password)
    conn.sendall(b"New user account created. Please login.")
    print("New user account created")



"""
handle_logout:
responsible for handling logout commands.
    if there is current_user, deny for not logged in.
        otherwise, logout, send message to client and server, and reset current_user to None.
"""
def handle_logout(conn):
    try:
        global current_user
        if current_user is None:
            conn.sendall(b"Denied. Please login first.")
            return False
        else:
            conn.sendall(f"{EXITSENTINEL} {current_user} left.\n".encode())
            conn.close()
            print(f"{current_user} logout.")
            current_user = None
            return True
    except Exception as e:
        print("Error in logout: ", e)
        return False



"""
handle_send()
responsible for handling send commands.
    if no current_user, deny for not logged in
    if no message, deny
    if starts with send , attempt to split the message into 'send ' and message.
        if message not in length reqs, deny
        otherwise send to client and print to server console.
    
    else
        send client 'invalid command'.
"""
def handle_send(command, conn):
    global current_user
    if current_user is None:
        conn.sendall(b"Denied. Please login first.")
        return
        
    if command.strip() == 'send':
        conn.sendall(b"Server Error: message must be between 1 and 256 characters.")
        return
        
    if command.strip().startswith("send "):
        try:
            _, message = command.split(maxsplit=1)
            if len(message) < 1 or len(message) > 256:
                conn.sendall(b"Server Error: message must be between 1 and 256 characters.")
                return
            response = f"{current_user}: {message}"
            conn.sendall(response.encode())
            print(response)
        except ValueError:
            conn.sendall("Server Error: Usage -> send <message>".encode())
        except Exception as e:
            print(e)
    else:
        conn.sendall("Invalid Command.".encode())
        return



server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)           #AF_INET specifies ipv4, SOCK_STREAM specifies TCP.
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)         #allows reuse of addr and port without cooldown period.
server_socket.bind((HOST, PORT))
server_socket.listen(1)                                                     #listen for 1 connection.

print("My chat room server. Version One.\n")
load_users()


while True:     #outer loop only tests for whether or not there is a current user. if not, look to accept a client.
    if current_user is None:
        conn, addr = server_socket.accept()
        while True: #main loop. responsible for calling handle command functions based on data received.
            try:
                data = conn.recv(1024).decode().strip()
                if not data:                    #if client connection drops without logging out.
                    print(f"{current_user} disconnected unexpectedly.")
                    current_user = None
                    break
            except Exception as e:
                print("Error receiving data:", e)
    

            if data.startswith("login "):
                handle_login(data, conn)

            elif data.startswith("newuser "):
                handle_newuser(data, conn)

            elif data == "logout":
                if handle_logout(conn):
                    break

            elif data.startswith("send ") or data.startswith("send"):
                handle_send(data, conn)

            else:
                conn.sendall(b"Invalid command.")
