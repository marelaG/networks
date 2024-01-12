# imported modules
import random


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


def prob_send(sender_socket, byte_data, receiver_address, failure_probability):
    """
    Wrapper function for sendto()-method of socket module, simulating network unreliability (i.e. bit-flipping errors &
    packet loss) via pseudo-randomness

    :param sender_socket: socket of sending host
    :param byte_data: data to be transmitted (in bytestring format)
    :param receiver_address: 2-tuple (<host>, <port>) specifying host (domain name or address) and port of receiving socket
    :param failure_probability: failure probability of transmission
    :return: True if packet is actually transmitted, False otherwise
    """
    
    if is_sent(failure_probability):
        sender_socket.sendto(byte_data, receiver_address)
        return True
    else:
        return False
