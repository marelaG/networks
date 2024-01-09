
import socket
import sys
import random
import time


def send_file_to_clients(file_name, probability, window_size, number_of_processes):
    with open(file_name, "rb") as file:
        file_data = file.read()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 12345)
    server_socket.bind(server_address)

    clients = set()
    num_clients = 0
    expected_clients = int(number_of_processes)
    server_socket.settimeout(30.0)

    print("Waiting for all clients to join...")

    while num_clients < expected_clients:
        try:
            data, client_address = server_socket.recvfrom(4096)
            if client_address not in clients:
                clients.add(client_address)
                num_clients += 1
                print(f"Client {num_clients} connected: {client_address}")
        except socket.timeout:
            print("Timeout occurred. No more clients joining or data received within the timeout.")
            break

    print("All clients have joined. Initiating file transfer...")
    # go back n
    for client_address in clients:
        server_socket.sendto(b"Start", client_address)
    sequence_number = 0
    base = 0
    packets = [file_data[i:i + window_size] for i in range(0, len(file_data), window_size)]
    ack_received = [False] * len(packets)

    while base < len(packets):
        packets_to_send = min(base + window_size, len(packets))
        for i in range(base, packets_to_send):
            if not ack_received[i]:
                try:
                    if probability < random.random():
                        packet = f"{sequence_number}:{packets[i].decode()}"
                        server_socket.sendto(packet.encode(), list(clients)[0])
                        print(f"Sent packet {sequence_number} to client.")
                    else:
                        # Simulate error by delaying packet
                        time.sleep(5)
                        packet = f"{sequence_number}:{packets[i].decode()}"
                        server_socket.sendto(packet.encode(), list(clients)[0])
                        print(f"Sent packet {sequence_number} (with delay) to client.")
                    sequence_number += 1
                except socket.error as e:
                    print(f"Error sending packet: {e}")

        # Receiving ACKs
        try:
            server_socket.settimeout(2)  # Set a timeout for ACK reception
            ack, _ = server_socket.recvfrom(4096)
            ack_parts = ack.decode().split(":")
            if len(ack_parts) >= 2:
                ack_number = int(ack_parts[1])
                if ack_number >= base and ack_number < packets_to_send:
                    ack_received[ack_number] = True
                    print(f"Received ACK for packet {ack_number}")
                    while base < len(packets) and ack_received[base]:
                        base += 1  # Move the base of the window
        except socket.timeout:
            print("Timeout occurred waiting for ACK.")
            # Resend packets from base to packets_to_send
        except socket.error as e:
            print(f"Socket error while receiving ACK: {e}")

        # Check if all packets are acknowledged
        if all(ack_received):
            break  # All packets have been acknowledged, exit the loop

    server_socket.close()
    print("File sent to all clients.")


if __name__ == "__main__":
    # Get arguments from command line
    toolname = sys.argv[1]
    id_process = sys.argv[2]
    number_of_processes = sys.argv[3]
    file_name = sys.argv[4]
    probability = float(sys.argv[5])
    protocol = sys.argv[6]
    window_size = int(sys.argv[7])

    send_file_to_clients(file_name, probability, window_size, number_of_processes)