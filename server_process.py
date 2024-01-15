# imported modules
import socket               # Python implementation of Berkeley Software Distribution (BSD) socket interface
import sys
import threading            # module for thread-based parallelism (no true concurrency due to Global Interpreter Lock)
import unreliable_network


def retransmission_handler_gbn(server_socket, failure_probability, registered_client, last_ack_rcvd_from_client,
                                data_chunks, sqn_nr, window_end, file_bytes_retransmitted, packets_retransmitted):
    """
    Handler function for Go-Back-N retransmission of timed-out packets (see also run_server function)

    :param server_socket: socket of Go-Back-N server (protocol sender side)
    :param registered_client: client to which timed-out packet was addressed
    :param last_ack_rcvd_from_client: highest, in-order (!) sequence number acknowledged by respective client process
    :param sqn_nr: sequence number of timed-out packet (corrupted, lost or extensively delayed)
    :param window_end: last sequence number within sender sliding window
    :return: None
    """

    # if client-specific packet timer expires and packet was already ACKed by client to server, no action needed
    if last_ack_rcvd_from_client[registered_client] >= sqn_nr:
        return

    # if client-specific timer for packet n expires, retransmit all packets from sequence number n to current window end
    else:
        for packet_nr in range(sqn_nr, window_end + 1):
            # construct segment payload, packaged with checksum and sequence number metadata (pseudo-header)
            sender_checksum = (unreliable_network.checksum(packet_nr.to_bytes(1, byteorder=sys.byteorder) +
                                                           data_chunks[packet_nr]).encode())
            encoded_sqn_nr = packet_nr.to_bytes(1, byteorder=sys.byteorder)
            # indicate after sequence number that it is a re-transmitted packet by appending "R"
            byte_message = (sender_checksum + ":".encode() +
                            encoded_sqn_nr + "R:".encode()
                            + data_chunks[packet_nr])

            # try resending sequenced packet(s) via underlying (unreliable) network stack to client
            was_sent = unreliable_network.prob_send(server_socket, byte_message, registered_client, failure_probability)

            # if packet retransmission was successful, update sending statistics
            if was_sent:
                print(f"RESENT FILE DATA CHUNK {sqn_nr}/{len(data_chunks)} "
                      f"TO CLIENT {registered_client[0]}:{registered_client[1]}.")
                file_bytes_retransmitted += len(data_chunks[packet_nr])
                packets_retransmitted += 1

        return


def run_server(process_id, expected_clients_nr, file_name, failure_probability, pipeline_type, window_size,
               file_bytes_sent, packets_sent, file_bytes_retransmitted, packets_retransmitted):
    """
    Runs server process for synchronously transmitting file to multiple client processes with simulated network
    unreliability and using the specified pipelining mechanism

    :param process_id: identification number for transmission session process
    :param expected_clients_nr: total number of client processes joining the session
    :param file_name: name of file to be transmitted by server process to client processes
    :param failure_probability: probability of unsuccessful data transmission over UDP (float between 0 and 1)
    :param pipeline_type: pipelining mechanism for custom protocol over UDP (Go-Back-N or Selective Repeat)
    :param window_size: size of sliding sender window
    :return: None
    """

    ################################################################################################################
    # file chunking part

    # dummy files for testing purposes were generated via UNIX "dd" command (with size=50 for 50MB and =1000 for 1GB):
    # dd if=/dev/urandom (random source generator) of=dummy_file_<filesize>.txt (destination file)
    #    bs=1000000 (block size in bytes, 1MB) count=<size> (how many read/write operations from source to destination)
    ################################################################################################################

    # use Python function open() to read data ("r") in binary/byte mode ("b") from file with specified file name
    with open(file_name, "rb") as download_file:
        # read data from file object "download_file" into bytes object "file_data"
        file_data = download_file.read()

        # prepare file data chunks of "block_size" bytes (except possibly last chunk) to be transmitted to clients
        data_chunks = list()
        block_size = 5000000
        for byte in range(0, len(file_data), block_size):
            # append file data chunks of "block_size" bytes to list
            bulk_slicing = slice(byte, byte + block_size)
            data_chunks.append(file_data[bulk_slicing])

            # slicing of file data into equally sized parts may not be possible, last file chunk may be smaller
            if (byte + block_size) + block_size >= len(file_data):
                end_slicing = slice(byte + block_size, len(file_data))
                data_chunks.append(file_data[end_slicing])

    ################################################################################################################
    # bootstrapping downloading clients
    ################################################################################################################

    # for security & demonstration reasons, server address is IPv4 loopback address (inaccessible to outer networks)
    # IPv4 address used instead of "localhost" domain to avoid non-deterministic behaviour through DNS resolution
    server_ip = "127.0.0.1"
    # arbitrary port for server process identification (but bigger than 1023 to avoid system port conflicts)
    # even though traffic is not leaving local host, it was still checked that port 2024 is unassigned by IANA
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
        # recvfrom()-method returns 2-tuple, 2nd element containing sender socket address included in UDP datagram
        # 4096 indicates socket buffer size (in bytes)
        _, client_addr = server_socket.recvfrom(4096)       # 2-tuple with format (<host>,<port>)

        # add only yet unknown client addresses to registered client addresses backlog
        if client_addr not in registered_clients_addr:
            registered_clients_addr.add(client_addr)
            registered_clients_nr += 1

            print(f"Client {registered_clients_nr} at address {client_addr[0]}:{client_addr[1]} "
                  f"registered at server {process_id}.")

            # keep already registered clients updated on server bootstrapping process
            for client_addr in registered_clients_addr:
                greeting_message = (f"Welcome at server {process_id}! "
                                    f"{registered_clients_nr}/{expected_clients_nr} clients connected. "
                                    f"Waiting for {expected_clients_nr-registered_clients_nr} remaining clients ...")
                server_socket.sendto(greeting_message.encode(), client_addr)

    # communicate that all expected client processes successfully connected to server
    print("")
    print("")
    print(f"All clients registered at server {process_id}. Initiating transfer of file '{file_name}' ...")
    print(f"--------------------------------------------------------------------------------------------")

    ################################################################################################################
    # handling retransmissions differently depending on pipelining mechanism
    ################################################################################################################

    # Go-Back-N pipelining
    if pipeline_type == "gbn":
        # initialise parameters of sender sliding window
        window_base = 0
        window_end = min(window_base + window_size - 1, len(data_chunks) - 1)

        # keep track what is the highest, in-order (!!!) sequence number each client has respectively acknowledged
        # !!! sender window only advances by n if ALL clients have ACKed first n sequence numbers in window !!!
        last_ack_rcvd_from_client = dict()
        for client in registered_clients_addr:
            last_ack_rcvd_from_client[client] = -1      # sequence number -1 indicates no acknowledged packet

        # Go-Back-N (bidirectional) communication loop for file transmission and ACKs
        while window_base <= len(data_chunks) - 1:

            #####################################################################################################
            # sending part of server Go-Back-N
            #####################################################################################################

            # iteratively sending all packets with sequence number in current sender window...
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

                    # try sending sequenced packet via underlying (unreliable) network stack to client
                    was_sent = unreliable_network.prob_send(server_socket, byte_message, registered_client, failure_probability)

                    # if packet sending was successful, update sending statistics
                    if was_sent:
                        print(f"Sent file data chunk {sqn_nr}/{len(data_chunks)} "
                              f"to client {registered_client[0]}:{registered_client[1]}.")
                        file_bytes_sent += len(data_chunks[sqn_nr])
                        packets_sent += 1

                    # for each client, start timer for each packet sent
                    # -> expiration of packet timer (timeout) without its ACK triggers retransmission of pipelined
                    #    packets, i.e. the timed-out packet and all higher-sequence-number packets in usable window
                    # -> arrival of ACK before timeout does not trigger any reaction by retransmission_handler function
                    client_packet_timer = threading.Timer(
                        15,
                        retransmission_handler_gbn,
                        [server_socket, failure_probability, registered_client, last_ack_rcvd_from_client,
                               data_chunks, sqn_nr, window_end, file_bytes_retransmitted, packets_retransmitted])
                    client_packet_timer.start()

            #####################################################################################################
            # receiving part of server Go-Back-N
            #####################################################################################################

            timeout_s = 10
            try:
                # receipt of acknowledgment (ACK) messages from registered client processes within socket timeout
                server_socket.settimeout(timeout_s)
                client_message_data, ack_client_addr = server_socket.recvfrom(4096)

                # analyse content of client message
                client_message_fields = client_message_data.decode().split(":", 2)
                sender_checksum = client_message_fields[0]
                ack_sqn_nr = client_message_fields[1]

                recv_checksum = unreliable_network.checksum(ack_sqn_nr.encode() + client_message_fields[2].encode())
                # check whether ACK message was not corrupted by unreliable network channel
                if sender_checksum == recv_checksum:
                    # acknowledge received ACK sequence number for that client, if it is NOT an "outdated" ACK !!!
                    if int(ack_sqn_nr) > last_ack_rcvd_from_client[ack_client_addr]:
                        # update entry of highest sequence number acknowledged for that client
                        # -> Go-Back-N uses "cumulative acknowledgment" scheme
                        last_ack_rcvd_from_client[ack_client_addr] = int(ack_sqn_nr)
                        print(f"Received ACK up to file part {ack_sqn_nr}/{len(data_chunks)} "
                              f"from client {ack_client_addr[0]}:{ack_client_addr[1]}.")
            except socket.timeout:
                print("")
                print(f"Resending packets after {timeout_s}s waiting for ACK messages from clients ...")
                print("")

            #####################################################################################################
            # window management and transmission termination
            #####################################################################################################

            # Go-Back-N uses "cumulative acknowledgment" scheme
            # -> sliding window synchronisation among clients is custom property required here
            advance_window = True
            while advance_window:
                # check whether ALL clients have ACKed sequence number higher or equal to current window base
                for client in last_ack_rcvd_from_client:
                    # if one client-specific sequence number is smaller than window base, do not shift window frame
                    if last_ack_rcvd_from_client[client] < window_base:
                        advance_window = False
                        break

                if advance_window:
                    # shift sender window one to the right
                    window_base += 1
                    window_end = min(window_base + window_size - 1, len(data_chunks) - 1)

            # check whether all clients successfully downloaded all file data chunks to possibly exit communication loop
            download_finished = True
            for client in last_ack_rcvd_from_client:
                # only if all clients have ACKed last sequence number, file transmission is complete
                if last_ack_rcvd_from_client[client] != (len(data_chunks) - 1):
                    # download is NOT finished if a single client did not acknowledge last sequence number
                    download_finished = False
                    break

            if download_finished:
                break

        # inform clients that download is complete and session shall be terminated
        closing_message = f"terminate_session"
        for client_addr in registered_clients_addr:
            server_socket.sendto(closing_message.encode(), client_addr)

        # release system resources by closing socket after file transmission and communicate termination (+ statistics)
        server_socket.close()
        print(f"--------------------------------------------------------------------------------------------")
        print(f"--------------------------------------------------------------------------------------------")
        print(f"File '{file_name}' from  server process {process_id} has been successfully sent to all clients. "
              f"Downloading session closed.")
        print("")
        print(f"File bytes sent directly: {file_bytes_sent} bytes")
        print(f"File packets sent directly: {packets_sent}")
        print(f"File bytes retransmitted: {file_bytes_retransmitted} bytes")
        print(f"File packets retransmitted: {packets_retransmitted}")
        print(f"--------------------------------------------------------------------------------------------")
        print(f"--------------------------------------------------------------------------------------------")

    # Selective Repeat pipelining
    # elif pipeline_type == "sr":
    #   ...


# run server script if server process is launched via start_session.py
if __name__ == "__main__":
    process_id = int(sys.argv[1])
    expected_clients_nr = int(sys.argv[2])
    file_name = sys.argv[3]
    failure_probability = float(sys.argv[4])
    pipeline_type = sys.argv[5]
    window_size = int(sys.argv[6])

    # global variables for sending statistics, displayed after completion of file transmission
    file_bytes_sent = 0
    packets_sent = 0
    file_bytes_retransmitted = 0
    packets_retransmitted = 0

    run_server(process_id, expected_clients_nr, file_name, failure_probability, pipeline_type, window_size,
               file_bytes_sent, packets_sent, file_bytes_retransmitted, packets_retransmitted)
