# imported modules
import socket               # Python implementation of Berkeley Software Distribution (BSD) socket interface
import sys
import unreliable_network


def run_server(process_id, expected_clients_nr, file_name, success_probability, pipeline_type, window_range):
    """
    Runs server process for synchronously transferring file to multiple client processes with simulated network
    unreliability and using the specified pipelining mechanism

    :param process_id: identification number for transfer session process
    :param expected_clients_nr: total number of client processes joining the session
    :param file_name: name of file to be transferred by server process to client processes
    :param success_probability: probability of successful transfer over UDP (float between 0 and 1)
    :param pipeline_type: pipelining mechanism for custom protocol over UDP (Go-Back-N or Selective Repeat)
    :param window_range: size of sliding window for Go-Back-N
    :return: None
    """

    # for security & demonstration reasons, server address is IPv4 loopback address (inaccessible to outer networks)
    # IPv4 address used instead of domain hostname (localhost) to avoid indeterministic behaviour through DNS resolution
    server_ip = "127.0.0.1"
    # arbitrary server port for server process identification (bigger than 1023 though to avoid OS conflicts)
    server_port = 2024

    # instantiate Berkeley Internet socket for IPv4 address family (AF_INET) & UDP socket type (SOCK_DGRAM)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # bind UDP server socket to IPv4 address at specified port to receive any incoming data from client processes
    server_socket.bind((server_ip, server_port))

    print(f"Server {process_id} is located at address {server_ip}:{server_port}")
    print(f"and ready to receive clients requesting transfer of file '{file_name}'.")
    print("")
    print("")

    # register previously specified instances of client processes (no timeout as server assumed to wait for everyone)
    registered_clients_nr = 0
    registered_clients_addr = set()              # set of client addresses = set of 2-tuples (<IPv4 address>,<port>)

    while registered_clients_nr < expected_clients_nr:
        # recvfrom() method returns 2-tuple, 2nd element containing sending socket address included in UDP datagram
        # 2048 indicates buffer size (in bytes) that can be received via one datagram
        client_data, client_addr = server_socket.recvfrom(2048)

        # add only yet unknown client addresses to registered client addresses backlog
        if client_addr not in registered_clients_addr:
            registered_clients_addr.add(client_addr)
            registered_clients_nr += 1
            print(f"Client {registered_clients_nr} at address {client_addr[0]}:{client_addr[1]} "
                  f"registered at server {process_id} !")

    # communicate that number of expected client processes successfully connected to server
    print("")
    print("")
    print(f"All clients registered at server {process_id}. Initiating transfer of file '{file_name}' ...")


    # handle retransmissions differently depending on pipelining mechanism

    # Go-Back-N pipelining approach
    if pipeline_type == "gbn":
        rt = 0

    # Selective Repeat pipelining approach
    # elif protocol == "sr":


# run either of the above methods if script is executed
if __name__ == "__main__":
    process_id = int(sys.argv[1])
    expected_clients_nr = int(sys.argv[2])
    file_name = sys.argv[3]
    success_probability = float(sys.argv[4])
    pipeline_type = sys.argv[5]
    window_range = int(sys.argv[6])

    run_server(process_id, expected_clients_nr, file_name, success_probability, pipeline_type, window_range)
