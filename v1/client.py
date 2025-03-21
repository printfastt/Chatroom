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
EXITSENTINEL = 'G7WJ4N3S'


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET specifies ipv4, SOCK_STREAM specifies TCP.
client_socket.connect((HOST, PORT))

print("My chat room client. Version One.\n")

while True: #main loop
    try:
        command = input(">").strip()
        parts = command.split()             #try block because unexpected inputs can cause split() to crash the program.
    except Exception as e:
        print("Error: ",e)
        continue

    if command.startswith("login ") or command.startswith("login"):     #check for both with and without space rather then just ignoring it to catch incorrect commands like 'loginn' and 'login Tom Tom11 tom'
        if len(parts) != 3:
            print(">Error: Usage -> login <username> <password>")
            continue

    elif command.startswith("newuser ") or command.startswith("newuser"):
        if len(parts) != 3:
            print(">Error: Usage -> newuser <username> <password>")
            continue


        username, password = parts[1], parts[2]
        if not (3 <= len(username) <= 32 and 4 <= len(password) <= 8):
            print(">Error: Username must be 3-32 characters, password 4-8 characters.")
            continue
    elif command == "logout":
        pass
    
    elif command.startswith("send ") or command.startswith("send"):
        parts = command.split(maxsplit=1)
        if len(parts) > 1:
            if len(parts[1]) > 256:
                print(">Error: Message must be 1-256 characters.")
                continue
            else:
                pass
        else:
            pass
    else:
        print(">Error: Invalid command.")
        continue
    
    try:
        client_socket.sendall(command.encode())         #send command
    except Exception as e:
        print("Error sending data:", e)

    try:
        response = client_socket.recv(1024).decode()    #recv response.
        if not response:
            print("Connection lost.")
            break
    except Exception as e:
        print("Error receiving data:", e)
    
    if command == 'logout':
        try:
            parts = response.split(maxsplit=1)      #server sends "<SENTINELVALUE> <USER> left.", so split off the sentinel value where parts[0] == SENTINELVALUE
            if parts[0] == EXITSENTINEL:            #if received sentinel value, print parts[1], the message.
                print(f">{parts[1]}")
                break
        except Exception as e:
            print("Error logging out. Please Try again.")

    if response[-1] != '.' and response != '': #if no period at end and response is not empty.
        print(f">{response}.")                  #append period
    else:
        print(f">{response}")                   #if there is one, just send as is

