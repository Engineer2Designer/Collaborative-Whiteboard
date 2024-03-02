import socket
import threading
import time

# Define the host and port
HOST = '10.30.201.112'
PORT = 5050
# Timeout duration for server inactivity in seconds
INACTIVITY_TIMEOUT = 40

# Create a socket object
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))

# List to keep track of all client connections
clients = []

# Lock for thread-safe access to clients list
clients_lock = threading.Lock()

# Flag to indicate whether the server is active
server_active = True

# Function to handle client connections
def handle_client(client, address):
    global server_active
    while server_active:
        try:
            # Receive data from the client
            data = client.recv(10240).decode()
            # Broadcast the received data to all clients except the sender
            with clients_lock:
                for c in clients:
                    c.sendall(data.encode())
        except ConnectionResetError:
            break
        except Exception as e:
            print(f"Error handling client {address}: {e}")
            break

    # Remove the client if connection is closed
    with clients_lock:
        if client in clients:
            clients.remove(client)
    print(f"Client {address} disconnected.")
    client.close()

# Function to start the server and listen for incoming connections
# Function to start the server and listen for incoming connections
def start_server():
    global server_active
    server.listen()
    print(f'Server is listening on {HOST}:{PORT}')

    while server_active:
        try:
            # Accept incoming connection with timeout
            server.settimeout(1)  # Set a timeout for the accept call
            client, address = server.accept()
            server.settimeout(None)  # Disable the timeout after the connection is accepted
            print(f'Connection established with {address}')
            # Add the client to the list of clients
            with clients_lock:
                clients.append(client)
            # Start a thread to handle the client connection
            thread = threading.Thread(target=handle_client, args=(client, address), daemon=True)
            thread.start()
        except socket.timeout:
            pass  # Continue accepting connections if timeout occurs
        except Exception as e:
            if server_active:
                print(f"Error accepting connection: {e}")
            break

    # Close the server socket after exiting the loop
    server.close()


# Function to monitor server activity and shut down if no clients are connected after a certain time
def monitor_activity():
    global server_active
    global clients
    while server_active:
        time.sleep(INACTIVITY_TIMEOUT)
        with clients_lock:
            if not clients:
                print(f"No clients connected for {INACTIVITY_TIMEOUT} seconds. Shutting down server.")
                server_active = False
                exit()

# Start the server and monitor activity in separate threads
server_thread = threading.Thread(target=start_server, daemon=True)
activity_thread = threading.Thread(target=monitor_activity, daemon=True)

server_thread.start()
activity_thread.start()

# Join threads to ensure main thread waits for their completion
server_thread.join()
activity_thread.join()