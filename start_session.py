# imported modules
import subprocess
import sys


def main():
    """Launcher method for a file transmission session"""

    # retrieve characteristics for transmission session from command line arguments
    id_process = int(sys.argv[1])
    number_of_processes = int(sys.argv[2])
    filename = sys.argv[3]
    probability = float(sys.argv[4])
    protocol = sys.argv[5]
    window_size = int(sys.argv[6])

    # start server child process from this parent process (here)
    server_process = subprocess.Popen(["python", "server_process.py",
                                       id_process, number_of_processes, filename, probability, protocol, window_size])

    # start client child process(es) from this parent process (here)
    for client_instance in range(number_of_processes):
        client_process = subprocess.Popen(["python", "client_process.py",
                                           filename, probability, protocol, window_size])

    # wait until server process has completed file transmission to ALL child processes before application shutdown
    server_process.wait()


# __name__ runtime attribute indicates "role" of file in Python runtime environment
# -> if __name__ is called within executed script, __name__ == __main__
# -> if __name__ is called within imported module, __name__ = <moduleName> (without .py)
if __name__ == "__main__":
    # execute main()-method above only if start_session.py is executed as main script (e.g. via terminal)
    main()
