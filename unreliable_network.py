# imported modules
import random
import sys


def is_sent(failure_probability):
    """
    Helper function simulating a Bernoulli trial with specified failure probability. Randomness is simulated using
    random module for deterministic, pseudo-random number generation of a uniform distribution between 0 and 1.

    :param failure_probability: probability of "failure" event
    :return: True if Bernoulli variable has "success" value, False if it has "failure" value
    """

    # initialise pseudo-random number generator via OS-specific randomness source (e.g. current system time)
    random.seed()
    # generate pseudo-random uniform distribution between 0 and 1 (both included)
    random_float = random.uniform(0, 1)

    # if generated value lies in failure range, return false
    if random_float <= failure_probability:
        return False
    # otherwise, return true
    else:
        return True


def checksum(byte_data):
    """
    Function to compute 16-bit checksum of data provided in byte format according to the Internet checksum specification
    in RFC 1071 (1988).

    :param byte_data: bytestring for which 16-bit checksum shall be computed
    :return: string containing checksum in binary (without "0b" prefix)
    """

    # convert data into binary (checksum invariant under byte-swapping in bytestring, i.e. big-endian or little-endian)
    # convert to integer number (base 10), then to binary number (base 2), without "0b" prefix
    binary_data = bin(int.from_bytes(byte_data, byteorder=sys.byteorder))[2:]

    # generate 16-bit chunks from binary data
    binary_chunks = []

    if len(binary_data) % 16 != 0:
        # pad leading bits with 0's to obtain first 16-bit block if perfect chunking into 16-bit blocks not possible
        remaining_bits_padded = "0" * (16 - len(binary_data) % 16)
        remaining_bits_padded = remaining_bits_padded + binary_data[0:len(binary_data) % 16]
        binary_chunks.append(remaining_bits_padded)

        # append remaining 16-bit blocks
        for i in range(len(binary_data) % 16, len(binary_data), 16):
            binary_chunks.append(binary_data[i:i+16])
    else:
        for i in range(0, len(binary_data), 16):
            binary_chunks.append(binary_data[i:i + 16])

    # sum up individual binary number strings in list as integers, then convert back to binary (without "0b" prefix)
    binary_sum = bin(sum(int(x, 2) for x in binary_chunks))[2:]

    # possible carry wrap-around (remove possible 16-bit-overflowing carry bit and add it back to 16-bit register)
    if len(binary_sum) > 16:
        # add back to 16-bit register via binary addition
        binary_sum = bin(int(binary_sum[0], 2) + int(binary_sum[1:], 2))[2:]
    # or padding with 0's if cumulative binary sum above would have leading 0's in 16-bit register
    elif len(binary_sum) < 16:
        binary_sum = "0" * (16 - len(binary_sum)) + binary_sum

    # compute 16-bit checksum via one's complement of previous result (convert 0 to 1 and 1 to 0 respectively)
    checksum = ""
    for bit in binary_sum:
        if bit == "1":
            checksum += "0"
        elif bit == "0":
            checksum += "1"

    return checksum


def prob_send(sender_socket, byte_data, receiver_address, failure_probability):
    """
    Wrapper function for sendto()-method of socket module, simulating network unreliability (i.e. bit-flipping errors &
    packet loss) via pseudo-randomness

    :param sender_socket: socket of sending host
    :param byte_data: data to be transmitted (in bytestring format)
    :param receiver_address: 2-tuple (<host>, <port>) specifying host (domain or address) and port of receiving socket
    :param failure_probability: failure probability of transmission
    :return: True if packet is actually transmitted, False otherwise
    """
    
    if is_sent(failure_probability):
        sender_socket.sendto(byte_data, receiver_address)
        return True
    else:
        return False
