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
PORT = 11259   # 1 + 1259

users = {}
current_user = None 
file_created = False #allows for interfunction communication so save_user() can format properly.

"""
args: none
return: none
desc: called at the beginning of the program to load users. 
    if new users.txt is created, change flag.
    if catch valuerror, print error.
"""
def load_users():
    global users
    global file_created
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
args: user;str, password;str
returns: none
desc: responsible for formatting and saving new users into users.txt.
"""
def save_user(user, password):
    global file_created
    with open("users.txt", "r+") as file:
        content = file.read().rstrip()   

        if file_created == True:
            file.write(f"({user}, {password})") 
        else:
            file.write(f"\n({user}, {password})")  
    file_created = False


"""
args: command;str, conn;socket
return: none
desc: responsible for ensuring correct command format, denying already logged in users, and validating password's to users.
"""
def handle_login(command, conn):
    global current_user
    parts = command.split()
    if len(parts) != 3:
        conn.sendall(b"Invalid command format.")
        return
    
    _, user, password = parts

    if current_user is not None:
        conn.sendall(b"Denied. Already logged in.")
        return

    if user in users and users[user] == password:
        current_user = user
        conn.sendall(b"login confirmed")
    else:
        conn.sendall(b"Denied. User name or password incorrect.")

"""
args: command;str, conn;socket
returns: none
desc: responsible for ensuring correct command format, denying already logged in users, validating correct password and username conditions, and calling the save function. 
"""
def handle_newuser(command, conn):
    global current_user
    parts = command.split()
    if len(parts) != 3:
        conn.sendall(b"Invalid command format.")
        return
    
    _, user, password = parts

    if current_user is not None:
        conn.sendall(b"Denied. Already logged in.")
        return

    if not (3 <= len(user) <= 32 and 4 <= len(password) <= 8):
        conn.sendall(b"Denied. Invalid username/password.")
        return

    if user in users:
        conn.sendall(b"Denied. User account already exists.")
        return

    users[user] = password
    save_user(user, password)
    conn.sendall(b"New user account created. Please login.")

"""
args: conn;socket
returns: bool
desc: responsible for denying log out to those already logged out, and 1.resetting user 2.ending connection and 3.telling the while loop to break by returning True for valid logout attempts.
"""
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

"""
args: command;string, conn;socket
returns: none
desc: responsible for denying send requests to logged out users, validating message requirements, and sending messages back to clients.
"""
def handle_send(command, conn):
    global current_user
    if current_user is None:
        conn.sendall(b"Denied. Please login first.")
        return


    parts = command.split(maxsplit=1) 

    if len(parts) < 2:  
        conn.sendall(b"Denied. Message must be 1-256 characters.")
        return

    message = parts[1].strip() 

    if not message or len(message) > 256:
        conn.sendall(b"Denied. Message must be 1-256 characters.")
        return

    response = f"{current_user}: {message}"
    conn.sendall(response.encode())

"""
helper function for dev
"""
def handle_who(command,conn):
    if current_user is None:
        conn.sendall(b"You are logged out.")

    if current_user is not None:
        message = f"{current_user, {addr}}"
        conn.sendall(message.encode())


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       #declares new variable of type socket, with AF_INET for ipv4 and SOCK_STREAM for TCP.
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)     #allows reuse of address/port without having to wait a countdown.
server_socket.bind((HOST, PORT))                                        #binds host (local connection) to a port. 
server_socket.listen(1)                                                 #how many connections to listen for. only 1 for v1.

print(f"Server listening on {HOST}:{PORT}...")
load_users() 


while True:                                                                 #outer loop only enters if inner loop breaks (client disconnects), or for initial server launch.
    if current_user is None:
        print("Waiting for client...")
        conn, addr = server_socket.accept()                                 #allow incoming connection
        print(f"Connected by {addr}")

        while True:                                                         #main loop; receives incoming commands and processes them until user disconnects.
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            print(f"Received: {data}")                                      #print received data to server console.

            if data.startswith("login "):                                   #handles login commands
                handle_login(data, conn)

            elif data.startswith("newuser "):                               #handles newuser commands
                handle_newuser(data, conn)

            elif data == "logout":                                          #handles logout, breaks main loop if handle_logout returns True. otherwise, if no user logged in, continue.
                if (handle_logout(conn)) == True:
                    break

            elif data.lower().startswith("send"):                           #handles send commands
                handle_send(data, conn)

            elif data.lower() == "who":                                     #dev function
                handle_who(data,conn)

            else:
                if current_user is None:                                    #handles non-logged in invalid user commands.
                    conn.sendall(b"Denied. Please login first.")

                else:
                    conn.sendall(b"Invalid command.")





        
    


