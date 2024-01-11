# imported modules
import random


def is_sent(success_probability):
    """
    Helper function simulating a Bernoulli trial with specified success probability. Randomness is simulated using
    random module for deterministic, pseudo-random number generation of a uniform distribution between 0 and 1.

    :param success_probability: probability of "success" event
    :return: True if Bernoulli variable has "success" value, False if it has "failure" value
    """

    # initialise pseudo-random number generator via OS-specific randomness source (e.g. current system time)
    random.seed()
    # generate pseudo-random uniform distribution between 0 and 1 (both included)
    random_float = random.uniform(0, 1)

    # if generated value lies in success range, return true
    if random_float <= success_probability:
        return True
    # otherwise, return false
    else:
        return False


def send_dgram(send_socket, byte_data, recv_address, success_probability):
    """
    Wrapper function for sendto()-method of socket module, simulating network unreliability (i.e. bit-flipping errors &
    packet loss) via pseudo-randomness

    :param send_socket: socket of sending host
    :param byte_data: data to be transmitted (in byte format)
    :param recv_address: 2-tuple (<host>, <port>) specifying host and port of receiving socket
    :param success_probability: success probability of transmission
    :return: True if packet is actually transmitted, False otherwise
    """
    
    if is_sent(success_probability):
        send_socket.sendto(byte_data, recv_address)
    else:
        return False
