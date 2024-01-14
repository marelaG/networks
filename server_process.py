# imported modules
import socket               # Python implementation of Berkeley Software Distribution (BSD) socket interface
import sys
import threading
import unreliable_network


def run_server(process_id, expected_clients_nr, file_name, failure_probability, pipeline_type, window_size):
    """
    Runs server process for synchronously transmitting file to multiple client processes with simulated network
    unreliability and using the specified pipelining mechanism

    :param process_id: identification number for transmission session process
    :param expected_clients_nr: total number of client processes joining the session
    :param file_name: name of file to be transmitted by server process to client processes
    :param failure_probability: probability of unsuccessful datagram transmission over UDP (float between 0 and 1)
    :param pipeline_type: pipelining mechanism for custom protocol over UDP (Go-Back-N or Selective Repeat)
    :param window_size: size of sliding window
    :return: None
    """

    ################################################################################################################
    # file chunking part

    # dummy files for testing purposes were generated via UNIX "dd" command (with size=50 for 50MB and =1000 for 1GB):
    # dd if=/dev/urandom (random source generator) of=dummy_file_<size>MB.txt (destination file)
    #    bs=1000000 (block size in bytes) count=<size> (how many read/write operations from source to destination)
    ################################################################################################################

    # use Python function open() to read data ("r") in binary/byte mode ("b") from file with specified file name
    with open(file_name, "rb") as download_file:
        # read data from file object "download_file" into bytes object "file_data"
        file_data = download_file.read()

        # prepare file data chunks to be transmitted to client processes
        data_chunks = list()
        for byte in range(0, len(file_data), 5000):
            # append file byte data chunks of 5KB size to list
            bulk_slicing = slice(byte, byte + 5000)
            data_chunks.append(file_data[bulk_slicing])

            # slicing of file data into equally sized parts may not be possible, last file chunk may be smaller
            if (byte + 5000) + 5000 >= len(file_data):
                end_slicing = slice(byte + 5000, len(file_data))
                data_chunks.append(file_data[end_slicing])

        # attribute sequence number to each file data chunk for pipelining mechanism (indexing)
        sequenced_data_chunks = list()
        sequence_number = 0
        for chunk in data_chunks:
            sequenced_data_chunks.append((sequence_number, data_chunks[sequence_number]))
            sequence_number += 1

    ################################################################################################################
    # bootstrapping downloading clients
    ################################################################################################################

    # for security & demonstration reasons, server address is IPv4 loopback address (inaccessible to outer networks)
    # IPv4 address used instead of "localhost" domain to avoid non-deterministic behaviour through DNS resolution
    server_ip = "127.0.0.1"
    # arbitrary server port for server process identification (bigger than 1023 though to avoid OS conflicts)
    server_port = 2024

    # instantiate Berkeley Internet socket for IPv4 address family (AF_INET) & UDP socket type (SOCK_DGRAM)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # bind UDP server socket to IPv4 address at specified port to receive any incoming data from client processes
    server_socket.bind((server_ip, server_port))

    print(f"Server {process_id} is reachable at address {server_ip}:{server_port}")
    print(f"and ready to receive clients requesting download of file '{file_name}'.")
    print("")
    print("")

    # register previously specified instances of client processes (no timeout as server assumed to wait for everyone)
    registered_clients_nr = 0
    registered_clients_addr = set()              # set of client addresses = set of 2-tuples (<IPv4 address>,<port>)

    while registered_clients_nr < expected_clients_nr:
        # recvfrom()-method returns 2-tuple, 2nd element containing sending socket address included in UDP datagram
        # 4096 indicates socket buffer size (in bytes)
        _, client_addr = server_socket.recvfrom(4096)

        # add only yet unknown client addresses to registered client addresses backlog
        if client_addr not in registered_clients_addr:
            registered_clients_addr.add(client_addr)
            registered_clients_nr += 1

            print(f"Client {registered_clients_nr} at address {client_addr[0]}:{client_addr[1]} "
                  f"registered at server {process_id}.")

            greeting_message = (f"Welcome at server {process_id}! "
                                f"{registered_clients_nr}/{expected_clients_nr} clients connected. "
                                f"Waiting for {expected_clients_nr-registered_clients_nr} remaining clients ...")
            server_socket.sendto(greeting_message.encode(), client_addr)

    # communicate that all expected client processes successfully connected to server
    print("")
    print("")
    print(f"All clients registered at server {process_id}. Initiating transfer of file '{file_name}' ...")

    ################################################################################################################
    # handling retransmissions differently depending on pipelining mechanism
    ################################################################################################################

    # Go-Back-N pipelining
    if pipeline_type == "gbn":
        # initialise parameters of sender sliding window
        window_base = 0
        next_sequence_number = 1
        window_end = min(window_base + window_size - 1, len(sequenced_data_chunks) - 1)

        # keep track whether all clients have acknowledged given sequence number (synchronisation) via dictionary
        last_ack_rcvd_from_client = dict()
        for client in registered_clients_addr:
            last_ack_rcvd_from_client[client] = 0

        # Go-Back-N communication loop (file transmission)
        while window_base <= len(sequenced_data_chunks) - 1:

            #####################################################################################################
            # sending part of server Go-Back-N
            #####################################################################################################

            # iteratively sending each message with sequence number in current sender window...
            for sqn_nr in range(window_base, window_end + 1):
                # ...to all clients registered at the server
                for registered_client in registered_clients_addr:
                    # construct segment payload, packaged with checksum and sequence number metadata (pseudo-header)
                    sender_checksum = unreliable_network.checksum(
                                        sqn_nr.to_bytes(1, byteorder=sys.byteorder) + data_chunks[sqn_nr]).encode()
                    encoded_sqn_nr = sqn_nr.to_bytes(1, byteorder=sys.byteorder)
                    byte_message = (sender_checksum + ":".encode() +
                                    encoded_sqn_nr + ":".encode()
                                    + data_chunks[sqn_nr])

                    # transmit same-sequence-number message via underlying (unreliable) network stack to all clients
                    unreliable_network.prob_send(server_socket, byte_message, registered_client, failure_probability)
                    print(f"Sent file data chunk {sqn_nr}/{len(data_chunks)} to client {registered_client[0]}:{registered_client[1]}")

                    # for each client, start timer for each message
                    # -> expiration of message-related timer (timeout event) will trigger retransmission of ALL
                    #    messages, i.e. the timed-out message and all other messages in the consecutive window
                    # -> arrival of ACK before timeout resets timeout for next message burst
                    client_timer = threading.Timer(10, retransmission)
                    client_timer.start()
                    # TODO: implement method and provide maybe args and kwargs !!!!!!!!!!!!!!!!!!
                    # but do only include in retransmission() the clients which did not receive an acknowledgment!

            #####################################################################################################
            # receiving part of server Go-Back-N
            #####################################################################################################

            # handling of acknowledgment messages from registered client processes
            client_message_data, ack_client_addr = server_socket.recvfrom(4096)

            # analyse content of client message
            client_message_fields = client_message_data.decode().split(":", 2)
            sender_checksum = client_message_fields[0]
            ack_sqn_nr = client_message_fields[1]

            recv_checksum = unreliable_network.checksum(ack_sqn_nr.encode() + client_message_fields[2].encode())
            # check whether ACK message was not corrupted by unreliable network channel...
            if sender_checksum == recv_checksum:
                # ... if ACK message was not corrupted, acknowledge every message up to the acknowledged number
                # (Go-Back-N uses cumulative acknowledgments scheme)
                for client in last_ack_rcvd_from_client:
                    if client == ack_client_addr:
                        last_ack_rcvd_from_client[ack_client_addr] = int(ack_sqn_nr)

            # check after each message burst whether all clients have received a certain sequence number
            isSynchronised = False

            # TODO: check in last_ack_rcvd_from_client whether all clients got the same packet to advance sender window





    # Selective Repeat pipelining
    # elif protocol == "sr":


# run server script if server process is launched via start_session.py
if __name__ == "__main__":
    process_id = int(sys.argv[1])
    expected_clients_nr = int(sys.argv[2])
    file_name = sys.argv[3]
    failure_probability = float(sys.argv[4])
    pipeline_type = sys.argv[5]
    window_size = int(sys.argv[6])

    run_server(process_id, expected_clients_nr, file_name, failure_probability, pipeline_type, window_size)
