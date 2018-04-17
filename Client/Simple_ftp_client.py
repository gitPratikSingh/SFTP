import socket
import hashlib
import pickle
import sys
import threading
from threading import Lock
import time

client_name = None
client_port = None
file_name = None
go_back_N = None
MSS = None
seq_num = 0
data_flag = '0101010101010101'
last_ack_num = None
client_socket = None
server_hostname = None
server_port = None


def start_client():
    global client_name
    global client_port
    global file_name
    global go_back_N
    global MSS
    global data_flag
    global client_socket
    client_socket = socket(socket.AF_INET, socket.SOCK_GRAM)
    if len(sys.argv) != 6:
        raise ValueError('Input list format should be: Simple_ftp_client '
                         'client_host_name client_port# file_name N MSS')
    sys.argv.pop(0)
    client_name, client_port, file_name, go_back_N, MSS = sys.argv

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    file = open(file_name, "r")
    buffer_list = list()
    while 1:
        str_data = file.read(int(MSS))
        if str_data:
            byte_data = pickle.dumps(str_data)
            buffer_list.append(byte_data)
        else:
            break
    try:
        thread_first = threading.Thread(target=recv_ack,arg=client_socket)
        thread_first.daemon = True
        thread_first.start()
        thread_first.join()
    except KeyboardInterrupt:
        sys.exit(0)
    rdt_send(buffer_list)


def recv_ack(client_socket):
    global last_ack_num
    lock = Lock()
    while 1:
        ack_byte = client_socket.recvfrom(2048)
        ack_num, zeros, ack_flag = pickle.loads(ack_byte)
        if zeros == 0 and ack_flag == '0101010101010101':
            if last_ack_num is None:
                last_ack_num = ack_num
            elif ack_num > last_ack_num:
                lock.acquire()
                last_ack_num = ack_num
                lock.release()


def generateCheckSum():
    return '1234567891234567'


def sendWindow(window, client_socket, server_hostname, server_port):
    for win in range(len(window)):
        client_socket.sendto(window[win], (server_hostname, server_port))


def rdt_send(buffer_list):
    global last_ack_num
    global go_back_N
    global data_flag
    global server_hostname
    global server_port
    global client_socket

    RTT = 2

    maxack = len(buffer_list) - 1

    while lastack < maxack:
        # add seq#
        # add checksum
        # add data_flag

        window = list()
        lastpacketacknumber = lastack
        # implement lock
        while len(window) < N and lastpacketacknumber < maxack:
            # send the next n packets
            packet = list()
            header = list()
            header.append(lastpacketacknumber + 1)
            header.append(generateCheckSum())
            header.append(data_flag)
            packet.append(header)
            packet.append(buffer_list[lastpacketacknumber + 1])

            lastpacketacknumber += 1

            window.append(packet)

            sendWindow(window, client_socket, server_hostname, server_port)

            time.sleep(RTT)


if __name__ == "__main__":
    print('Client is ready to go!')
    start_client()
