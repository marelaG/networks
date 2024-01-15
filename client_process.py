# imported modules
import random
import socket                # Python implementation of Berkeley Software Distribution (BSD) socket interface
import sys
import unreliable_network


def run_client(filename, failure_probability, protocol, window_size, file_bytes_received, packets_received,
               retransmitted_file_bytes_received, retransmitted_packets_received):
    """
    Runs client process for downloading a file from a content distributing server with simulated network unreliability.
    
    :param filename: name of file to be downloaded from server
    :param failure_probability: probability of unsuccessful data transmission over UDP (float between 0 and 1)
    :param protocol: pipelining mechanism for custom protocol over UDP (Go-Back-N or Selective Repeat)
    :param window_size: size of sliding receiver window
    :return: None
    """

    # for security & demonstration reasons, client address is IPv4 loopback address (inaccessible to outer networks)
    # IPv4 address used instead of "localhost" domain to avoid non-deterministic behaviour through DNS resolution
    client_ip = "127.0.0.1"
    # arbitrary port for client process identification (but bigger than 1023 to avoid system port conflicts)
    # generate random client port number between 4000 and 8000 (included) via Python's random module
    client_port = random.randint(4000, 8000)

    # instantiate Berkeley Internet socket for IPv4 address family (AF_INET) & UDP socket type (SOCK_DGRAM)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # bind UDP client socket to IPv4 address at specified port to receive any incoming data from download server
    client_socket.bind((client_ip, client_port))

    # server address must be known beforehand (usually cannot be determined by the client !)
    server_ip = "127.0.0.1"
    server_port = 2024
    server_address = (server_ip, server_port)

    # contacting server to request file download (server process registers on first-come, first-serve basis)
    # indicate to server process which file (identified by file name) shall be retrieved
    print(f"Client {client_ip}:{client_port} requesting {filename}...")
    print("")
    print("")

    download_request = f"Send {filename}"
    client_socket.sendto(download_request.encode(), server_address)

    #############################################################################################################
    # Go-Back-N receiver-side implementation
    #############################################################################################################

    # client process tracks next in-order sequence number expected to be sent by server process (Go-Back-N sender)
    receiver_base = 0

    HERE !

    # !!! -> implementation choice: no buffering of sequence numbers higher than next-highest, in-order

    # release system resources by closing socket after file transmission completed and communicate statistics
    client_socket.close()
    print(f"--------------------------------------------------------------------------------------------")
    print(f"--------------------------------------------------------------------------------------------")
    print(f"File '{file_name}' has been downloaded by client at {client_ip}:{client_port}.")
    print("")
    print(f"File bytes received directly: {file_bytes_received} bytes")
    print(f"File packets received directly: {packets_received}")
    print(f"Retransmitted file bytes received: {retransmitted_file_bytes_received} bytes")
    print(f"Retransmitted file packets received: {retransmitted_packets_received}")
    print(f"--------------------------------------------------------------------------------------------")
    print(f"--------------------------------------------------------------------------------------------")

    # Selective Repeat receiver-side implementation
    # ...


# run client script if client process is launched via start_session.py
if __name__ == "__main__":
    file_name = sys.argv[1]
    failure_probability = float(sys.argv[2])
    pipeline_type = sys.argv[3]
    window_size = int(sys.argv[4])

    # global variables for receiving statistics, displayed after completion of file transmission
    file_bytes_received = 0
    packets_received = 0
    retransmitted_file_bytes_received = 0
    retransmitted_packets_received = 0

    run_client(file_name, failure_probability, pipeline_type, window_size,
               file_bytes_received, packets_received, retransmitted_file_bytes_received, retransmitted_packets_received)