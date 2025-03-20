import socket
import threading
import time
import sys
import select

HOST = '127.0.0.1'
PORT = 11259
MAXMESSAGEBYTES = 1024
EXIT_SENTINEL = '7F3K9P2Q1SJ438FJAU3JFK'


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
exit_event = threading.Event()

def receive():
    """
    Receives messages from the server and prints them without interfering
    with the user's typed but unsent input.
    """
    while True:
        try:
            data = client_socket.recv(MAXMESSAGEBYTES).decode().strip()
            if not data:
                break
            elif data == EXIT_SENTINEL:
                exit_event.set()
                break
            else:
                sys.stdout.write("\r\033[K")  
                sys.stdout.flush()
            print(data.strip()) 


        except Exception as e:
            print(f"Error in receive(): {e}")
            break

def stdinIsReady():
    """Check if there is input available on stdin."""
    ready, _, _ = select.select([sys.stdin], [], [], 0.1)
    return bool(ready)

threading.Thread(target=receive, daemon=True).start()
if not exit_event.wait(timeout=0.2):
    print(">> Connected to the server. Type login or create newuser:")

while not exit_event.is_set():
    time.sleep(0.01) 
    while not exit_event.is_set():
        if stdinIsReady():
            command = sys.stdin.readline().strip()
            command = "/" + command
            parts = command.split(maxsplit=2)

            if command.startswith("/login "):
                if len(parts) != 3:
                    print(">> Error: Usage -> login <username> <password>")
                    continue

            elif command.startswith("/newuser "):
                if len(parts) != 3:
                    print(">> Error: Usage -> newuser <username> <password>")
                    continue
                username, password = parts[1], parts[2]
                if not (3 <= len(username) <= 32 and 4 <= len(password) <= 8):
                    print(">> Error: Username must be 3-32 characters, password 4-8 characters.")
                    continue

            elif command == "/logout":
                client_socket.sendall(command.encode())                    
                if not exit_event.wait(timeout=0.01):
                    break

            elif command.startswith("/send "):
                if len(parts) < 2:
                    print(">> Error: Usage -> send all <message> OR send <username> <message>")
                    continue
                if len(parts[1]) < 1 or len(parts[1]) > 256:
                    print(">> Error: Message must be 1-256 characters.")
                    continue
                if len(parts) == 2:
                    print(">> Error: Usage -> send all <message> OR send <username> <message>")
                    continue

            elif command == "/who":
                pass

            else:
                print(">> Error: Invalid command.")
                continue

            client_socket.sendall(command.encode())
            sys.stdout.flush()  

client_socket.close()
