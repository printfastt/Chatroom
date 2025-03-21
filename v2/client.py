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
import sys
import select

HOST = '127.0.0.1'
PORT = 11259
MAXMESSAGEBYTES = 1024
EXIT_SENTINEL = '7F3K9P2Q1SJ438FJAU3JFK'
THREAD_SENTINEL = 'FN4NS4JWN3LQK3NB3N2JF3'
is_logged_in = False

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
exit_event = threading.Event()


"""
Receives messages from the server and prints them without interfering
with the user's typed but unsent input.
"""
def receive():
    global is_logged_in
    while True:
        try:
            data = client_socket.recv(MAXMESSAGEBYTES).decode().strip()
            if not data:
                break
            elif data == EXIT_SENTINEL:
                exit_event.set()
                break
            elif data.strip().startswith(THREAD_SENTINEL):
                try:
                    data = data.replace(THREAD_SENTINEL, "")
                    #sys.stdout.write("\r\033[K")
                    print(f"{data.strip()}")
                    time.sleep(.01)
                    print(">", end = "", flush = True)
                    continue

                except Exception as e:
                    print(f">Error in receive(): {e}")
                    break
            elif data.strip() == "login confirmed.":
                is_logged_in = True
                pass
            else:
                sys.stdout.write("\r\033[K")  
                sys.stdout.flush()
            print(f">{data.strip()}") 
    


        except Exception as e:
            print(f">Error in receive(): {e}")
            break

def stdinIsReady():
    """Check if there is input available on stdin."""
    ready, _, _ = select.select([sys.stdin], [], [], 0.1)
    return bool(ready)

threading.Thread(target=receive, daemon=True).start()
if not exit_event.wait(timeout=0.2):
    print(">Connected to the server. Type login or create newuser:")



"""
Handles client-side command input and communication with the server.  

- Continuously listens for user input while the exit event is not set.  
- Processes and validates commands before sending them to the server.  
  - Ensures correct syntax for login, new user creation, messaging, and logout.  
  - Enforces constraints on username and password length.  
  - Restricts message length between 1 and 256 characters.  
- Sends valid commands to the server via `client_socket`.  
- Handles logout by sending the command and waiting briefly before exiting.  
- Closes the client socket when the loop exits.  
"""
while not exit_event.is_set():
    time.sleep(0.01) 
    print(">", end = "", flush = True)
    while not exit_event.is_set():
        if stdinIsReady():

            try:
                command = sys.stdin.readline().strip()
                command = "/" + command
                parts = command.split()
            except ValueError:
                print(">Error: Invalid command.")
                break
            except Exception as e:
                print(f">Error: {e}")
                break


            if command.startswith("/login ") or parts[0] == "/login":
                if is_logged_in:
                    print(">Denied. Already logged in.")
                    break
                if len(parts) != 3:
                    print(">Error: Usage -> login <username> <password>")
                    break
                pass


            elif command.startswith("/newuser "):
                if is_logged_in:
                    print(">Denied. Already logged in.")
                    break
                if len(parts) != 3:
                    print(">Error: Usage -> newuser <username> <password>")
                    break
                username, password = parts[1], parts[2]
                if not (3 <= len(username) <= 32 and 4 <= len(password) <= 8):
                    print(">Error: Username must be 3-32 characters, password 4-8 characters.")
                    break
                pass


            elif command == "/logout":
                if not is_logged_in:
                    print(">Denied. Please login first.")
                    break
                client_socket.sendall(command.encode())                    
                if not exit_event.wait(timeout=0.01):
                    break
                pass


            elif command.startswith("/send ") or command.startswith("/send"):
                if not is_logged_in:
                    print(">Denied. Please login first.")
                    break
                elif (len(parts) >=3):
                    try:
                        parts = command.split(maxsplit=2)
                        if parts[0] == "/send" and (parts[1] == "all"):
                            message = parts[2]
                            if not (1 <= len(message) <= 256):
                                print(">Error: Message must be 1-256 characters.")
                                break
                        else:
                            message = parts[2]
                            if not (1 <= len(message) <= 256):
                                print(">Error: Message must be 1-256 characters.")
                                break
                        pass
                    except Exception as e:
                        print(f">Error: {e}")
                        break
                else:
                    print(">Error: Usage -> send all <message> OR send <username> <message>")
                    break
                

            elif command == "/who":
                pass

            else:
                print(">Error: Invalid command.")
                break

            client_socket.sendall(command.encode())
            break

client_socket.close()
