import sys
import socket
# Function which takes care of the clients namely sends info about joining to the server
def main():
    # Declaration of all the parameters from command-line arguments
    toolname = sys.argv[1]
    id_process = int(sys.argv[2])
    number_of_processes = int(sys.argv[3])
    filename = sys.argv[4]
    probability = float(sys.argv[5])
    protocol = sys.argv[6]
    windowsize = int(sys.argv[7])
    start_port = 1000 + id_process

    # I am not sure with the client port sasha told me its better to make a new port for each but for me it worked
    # better with just one so im still wokring on ti


    # Connect to the server using UDP
    server_address = ('localhost', 12345)  # Server address and port
    # Send info that client is joining to server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create socket

    #client_socket.bind(('localhost', start_port))  # Bind the socket to a specific port for this client
    client_socket.bind(('localhost', 0))
    client_socket.sendto(b"Joining", server_address)  # Send the socket

    # Receive file data from the server
    received_data = b""  # Initialize variable to store received data
    while True:
        data, _ = client_socket.recvfrom(4096)  # Receive data from server
        # If still data continue else break
        if data:
            received_data += data  # Add received data to the variable
        else:
            break  # Break the loop if no more data is received

    client_socket.close()  # Close the socket after receiving data

    return received_data



if __name__ == "__main__":
    assembled_data = main()


