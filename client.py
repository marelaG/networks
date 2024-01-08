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
    start_port = (9005 - id_process)

    server_address = ('localhost', 12345)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind(('localhost', start_port))
    client_socket.sendto(b"Joining", server_address)

    received_data = b""
    while True:
        data, server_addr = client_socket.recvfrom(4096)
        if data:
            # Acknowledge the receipt of data to the server
            client_socket.sendto(b"ACK", server_addr)
            received_data += data
        else:
            break

    client_socket.close()
    return received_data

if __name__ == "__main__":
    assembled_data = main()
    
