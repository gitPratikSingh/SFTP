import socket
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
ack_flag = '1010101010101010'
end_flag = "1111111111111111"

last_ack_num = -1
client_socket = None
server_hostname = 'localhost'
server_port = 7735
lock = None

def start_client():
    global client_name
    global client_port
    global file_name
    global go_back_N
    global MSS
    global data_flag
    global client_socket
    global lock
    lock = Lock()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if len(sys.argv) != 6:
        raise ValueError('Input list format should be: Simple_ftp_client '
                         'client_host_name client_port# file_name N MSS')
    sys.argv.pop(0)
    client_name, client_port, file_name, go_back_N, MSS = sys.argv
    client_port = int(client_port)
    go_back_N = int(go_back_N)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind((client_name, client_port))

    file = open(file_name, "r")
    buffer_list = list()
    while 1:
        str_data = file.read(int(MSS))
        if str_data:
            byte_data = str_data
            buffer_list.append(byte_data)
        else:
            break
    try:
        thread_first = threading.Thread(target=recv_ack, args=(client_socket,))
        thread_first.daemon = True
        thread_first.start()
        thread_second = threading.Thread(target=rdt_send, args=(buffer_list,))
        thread_second.daemon = True
        thread_second.start()

        thread_second.join()
        time.sleep(10)
    except KeyboardInterrupt:
        sys.exit(0)


def recv_ack(client_socket):
    global last_ack_num
    global lock
    global ack_flag
    try:
        while 1:
           # print(client_socket)
            ack_byte, addr = client_socket.recvfrom(1024)
            ack_num, zeros, ack_flag = pickle.loads(ack_byte)
            print("ack_num recievedL "+ str(ack_num))

            if zeros == '0000000000000000' and ack_flag == ack_flag:
                if last_ack_num is None:
                    last_ack_num = ack_num
                elif ack_num > last_ack_num:
                    lock.acquire()
                    last_ack_num = ack_num
                    lock.release()
                print("Updated ack")
    except KeyboardInterrupt:
        sys.exit(0)


def checksum(pkt):
    return 0xfff

def sendWindow(window, client_socket, server_hostname, server_port):
    for win in window:
       # print(client_socket)
        client_socket.sendto(win, (server_hostname, server_port))


def rdt_send(buffer_list):
    global last_ack_num
    global go_back_N
    global data_flag
    global server_hostname
    global server_port
    global client_socket
    global lock

    RTT = 0.2

    maxack = len(buffer_list) - 1

    while True:
        # add seq#
        # add checksum
        # add data_flag

        lock.acquire()
        beforeacknumber = last_ack_num
        print("Last ack val: "+str(last_ack_num))
        lock.release()

        if beforeacknumber < maxack:

            window = list()

            lastpacketacknumber = beforeacknumber
            # implement lock
            while len(window) < go_back_N and lastpacketacknumber < maxack:
                # send the next n packets
                packet = list()
                header = list()
                header.append(lastpacketacknumber + 1)
                header.append(checksum(buffer_list[lastpacketacknumber + 1]))
                header.append(data_flag)
                packet.append(header)
                packet.append(buffer_list[lastpacketacknumber + 1])

                lastpacketacknumber += 1
                print("Sending " + str(lastpacketacknumber))
                packet = pickle.dumps(packet)

               # print(type(packet))
                window.append(packet)

            sendWindow(window, client_socket, server_hostname, server_port)

            lock.acquire()
            afteracknumber = last_ack_num
            lock.release()

            if afteracknumber == beforeacknumber:
                time.sleep(RTT)

        else:
            # completed,send the end packet
            lastpacketacknumber = beforeacknumber
            # implement lock
            # send the next n packets
            packet = list()
            header = list()
            header.append(lastpacketacknumber + 1)
            header.append(checksum(buffer_list[lastpacketacknumber + 1]))
            header.append(data_flag)
            packet.append(header)
            packet.append(end_flag)

            lastpacketacknumber += 1
            print("Sending end packet" + str(lastpacketacknumber))
            packet = pickle.dumps(packet)

            window.append(packet)
            sendWindow(window, client_socket, server_hostname, server_port)


            break


if __name__ == "__main__":
    start_client()
    print('Client is ready to go!')
