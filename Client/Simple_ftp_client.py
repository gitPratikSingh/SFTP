import socket
import pickle
import sys
import time

client_name = ''
client_port = ''
file_name = ''
go_back_N = ''
MSS = ''
seq_num = 0
data_flag = '0101010101010101'
lastack = None
N = 10
client_socket = None
server_hostname = None
server_port = None


def start_client():
    global client_name
    global client_port
    global file_name
    global go_back_N
    global MSS
    global client_socket

    if len(sys.argv) != 6:
        raise ValueError('Input Argument list should be: Simple_ftp_client'
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
    rdt_send(buffer_list)


def generateCheckSum():
    return '1234567891234567'


def sendWindow(window, client_socket, server_hostname, server_port):
    for win in range(len(window)):
        client_socket.sendto(window[win], (server_hostname, server_port))


def rdt_send(buffer_list):
    global lastack
    global N
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
