import socket
import threading
import time
import sys
import select

HOST = '127.0.0.1'
PORT = 11259

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
exit_event = threading.Event()
#serverintercepts = ("> ", "Server: ")

def receive():
    """
    note: if starts with's to catch if message begins with 'Server' or '>' 
    """
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            #if data.strip().startswith(serverintercepts[0]) or data.strip().startswith(serverintercepts[1]):
            if data.strip() == "Logout successful.":
                exit_event.set()
                break
            else:
                print(data)
                #sys.stdout.write('\r\033[K')
        except:
            break

threading.Thread(target=receive, daemon=True).start()

def stdinIsReady():
    ready,_,_ = select.select([sys.stdin], [], [], .5)
    return True

def stdoutIsReady():
    _,ready,_ = select.select([], [sys.stdout], [], .5)
    if ready:
        return False
    else:
        return True



print("Connected to the server. Type a command:")
while not exit_event.is_set():
    time.sleep(.01)
    print("//", end = "", flush = True)
    
    while not exit_event.is_set():
        if stdinIsReady():
            command = sys.stdin.readline().strip()
            parts = command.split(maxsplit=2)

            if command.startswith("login "):
                if len(parts) != 3:
                    print("Error: Usage -> login <username> <password>")
                    break

            elif command.startswith("newuser "):
                if len(parts) != 3:
                    print("Error: Usage -> newuser <username> <password>")
                    continue
                username, password = parts[1], parts[2]
                if not (3 <= len(username) <= 32 and 4 <= len(password) <= 8):
                    print("Error: Username must be 3-32 characters, password 4-8 characters.")
                    continue

            elif command == "logout":
                client_socket.sendall(command.encode())                    
                if not exit_event.wait(timeout=.01):                    #waits .01 seconds for response from server to decide if loop should break.
                    break
                                                        

            elif command.startswith("send "):
                if len(parts) < 2:
                    print("Error: Usage -> send all <message> OR send <username> <message>")
                    break
                if len(parts[1]) < 1 or len(parts[1]) > 256:
                    print("Error: Message must be 1-256 characters.")
                    break
                if len(parts) == 2:
                    print("Error: Usage -> send all <message> OR send <username> <message>")
                    break

                
            elif command == "who":
                pass

            else:
                print("Error: Invalid command.")


            client_socket.sendall(command.encode())
            break

client_socket.close()

####NOTE
####NOTE
####NOTE
####CARSON
####YOU NEED TO REPLACE A LOT OF SENDALL'S WITH A LOT OF BROADCASTS.