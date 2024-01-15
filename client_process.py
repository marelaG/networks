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

    # each client process tracks next in-order sequence number expected to be sent by server process (Go-Back-N sender)
    receiver_base = 0

    # Go-Back-N (bidirectional) communication loop for file receipt and ACKs
    download_ongoing = True
    while download_ongoing:
        # receive incoming packet data sent by contacted server
        received_data, server_address = client_socket.recvfrom(4096)

        # analyse content of received data
        server_message_fields = received_data.decode().split(":", 2)
        sender_checksum = server_message_fields[0]
        sequence_number_field = server_message_fields[1].split(",")
        sequence_number = sequence_number_field[0]
        server_payload = server_message_fields[2]

        # check whether server message was not corrupted by unreliable network channel
        receiver_checksum = unreliable_network.checksum(sequence_number.encode() + server_payload.encode())

        if sender_checksum == receiver_checksum:
            # client reaction depending on received sequence number (and message content in case of completed download)
            if int(sequence_number) == receiver_base:
                # client receives expected sequence number -> acknowledge receipt by advancing client sliding window...
                receiver_base += 1

                # ... and sending ACK message to server for this sequence number
                acked_sequence_number = int(sequence_number).to_bytes(1, byteorder=sys.byteorder)
                ack_payload = "ACK".encode()
                ack_checksum = unreliable_network.checksum(acked_sequence_number + ack_payload).encode()
                byte_ack_message = ack_checksum + ":".encode() + acked_sequence_number + ":".encode() + ack_payload

                # try sending ACK message via underlying (unreliable) network to client
                was_acked = unreliable_network.prob_send(client_socket, byte_ack_message, server_address, failure_probability)

                # if ACK sending was successful, update receiving statistics
                if was_acked:
                    # if received file data was transmitted first time by server
                    if len(sequence_number_field) == 1:
                        file_bytes_received += len(server_payload.encode())
                        packets_received += 1
                    # if received message was re-transmitted by server
                    elif len(sequence_number_field) > 1:
                        retransmitted_file_bytes_received += len(server_payload.encode())
                        retransmitted_packets_received += 1

            elif (int(sequence_number) > receiver_base) and (int(sequence_number) <= receiver_base + window_size - 1):
                # received sequence number lies in Go-Back-N receiver window, BUT is not expected sequence number
                # -> client then acknowledges highest IN-ORDER, YET-RECEIVED sequence number receiver_base–1 to server
                # -> personal choice: NO buffering of received sequence numbers higher than receiver_base in window

                # send (duplicate) ACK message to server with receiver_base–1 as sequence number
                acked_sequence_number = int(receiver_base - 1).to_bytes(1, byteorder=sys.byteorder)
                ack_payload = "ACK".encode()
                ack_checksum = unreliable_network.checksum(acked_sequence_number + ack_payload).encode()
                byte_ack_message = ack_checksum + ":".encode() + acked_sequence_number + ":".encode() + ack_payload

                # try sending (duplicate) ACK via underlying (unreliable) network to client
                unreliable_network.prob_send(client_socket, byte_ack_message, server_address, failure_probability)

            elif int(sequence_number) == 12345:
                # upon receiving this particular sequence number, server indicates to client that download is complete
                download_ongoing = False
                break

    # release system resources by closing socket after file transmission completed and communicate statistics
    client_socket.close()
    print("")
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