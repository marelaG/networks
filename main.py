import socket
import sys
import random
import os
import subprocess
# Starting file which allows declaration of parameters from the command line as provided in the description


def main():
    # Declaration of all the start parameters
    toolname = sys.argv[1]
    id_process = sys.argv[2]
    number_of_processes = sys.argv[3]
    filename = sys.argv[4]
    probability = sys.argv[5]
    protocol = sys.argv[6]
    windowsize = sys.argv[7]


    # Start the server process with all parameters
    server_process = subprocess.Popen(
        ['python', 'server.py', toolname, id_process, number_of_processes, filename, probability, protocol, windowsize])

    # Start client processes with all parameters
    for i in range(int(number_of_processes)):
        client_process = subprocess.Popen(
            ['python', 'client.py', toolname, str(i), number_of_processes, filename, probability, protocol,
             windowsize])

    # Wait for the server process to finish
    server_process.wait()


if __name__ == "__main__":
    main()
