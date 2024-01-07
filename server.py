import random
import socket
import os
import sys
import time


# Server file which will send files to the clients


def send_file_to_clients(file_name, probability, window_size):
    # Open the file to be sent
    with open(file_name, "rb") as file:
        file_data = file.read()

    # Create UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set adress
    server_address = ('localhost', 12345)
    # Bind the socket to the adress to listen for packets
    server_socket.bind(server_address)

    # Tracking clients
    clients = set()  # List of clients
    num_clients = 0  # Track the number of connected clients
    expected_clients = int(number_of_processes)  # Total number of expected clients
    # In case of an error
    server_socket.settimeout(10.0)

    # Joining of the clients
    print("Waiting for all clients to join...")

    while num_clients < expected_clients:
        try:
            # Get confirmation that client wants to join
            data, client_address = server_socket.recvfrom(4096)
            # Add new client
            if client_address not in clients:
                clients.add(client_address)
                num_clients += 1
                print(f"Client {num_clients} connected: {client_address}")
        except socket.timeout:
            print("Timeout occurred. No more clients joining or data received within the timeout.")
            break

    print("All clients have joined. Initiating file transfer...")

    # Send the file data to all connected clients
    # Sending the data
    while file_data:
        chunk = file_data[:window_size]  # Extract data chunk
        file_data = file_data[window_size:]  # Move to the next chunk

        for client_address in clients:
            if probability > random.random():  # Simulate probability of success by comparint pb with random number 0-1
                server_socket.sendto(chunk, client_address)
            else :
                # If mamy issue to sleep 5 seconds and resend
                time.sleep(5)
                server_socket.sendto(chunk, client_address)

    # Close server socket
    server_socket.close()
    print("File sent to all clients.")

if __name__ == "__main__":

    toolname = sys.argv[1]
    id_process = sys.argv[2]
    number_of_processes = sys.argv[3]
    file_name = sys.argv[4]
    probability = float(sys.argv[5])
    protocol = sys.argv[6]
    window_size = int(sys.argv[7])

    send_file_to_clients(file_name, probability, window_size)
