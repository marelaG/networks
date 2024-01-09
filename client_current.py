import random
import sys
import socket

def main():
    # Parsing command-line arguments
    toolname = sys.argv[1]
    id_process = int(sys.argv[2])
    number_of_processes = int(sys.argv[3])
    filename = sys.argv[4]
    probability = float(sys.argv[5])
    protocol = sys.argv[6]
    window_size = int(sys.argv[7])
    start_port = (1000 + id_process)

    server_address = ('localhost', 12345)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(('localhost', start_port))
    client_socket.sendto(b"Joining", server_address)
    sequence_number = 0
    base = 0
    try:
        while True:
            data, _ = client_socket.recvfrom(4096)
            if data == b"Start":
                print("Received signal from server to start file transfer.")
                break
    except socket.error as e:
        print(f"Socket error while receiving signal from server: {e}")

    while True:
        packets_to_send = min(base + window_size, number_of_processes)
        for i in range(base, packets_to_send):
            try:
                if probability < random.random():
                    ack_msg = f"ACK:{i}"
                    client_socket.sendto(ack_msg.encode(), server_address)
                    print(f"Sent ACK for packet {i}")
                else:
                    # Simulate packet loss by not sending an ACK
                    print(f"Simulated ACK loss for packet {i}")
            except socket.error as e:
                print(f"Error sending ACK: {e}")

        try:
            client_socket.settimeout(2)  # Set a timeout for receiving retransmissions
            retransmission, _ = client_socket.recvfrom(4096)
            # Process the received retransmission packets if needed
            print(f"Received retransmission: {retransmission.decode()}")
        except socket.timeout:
            print("No retransmission received.")
        except socket.error as e:
            print(f"Socket error while receiving retransmission: {e}")

        base = packets_to_send  # Move the base of the window

        if base >= number_of_processes:
            break  # All packets have been acknowledged

    client_socket.close()


if __name__ == "__main__":
    main()
