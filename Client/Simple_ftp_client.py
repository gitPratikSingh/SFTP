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
localtime =  None

def start_client():
    global client_name
    global client_port
    global file_name
    global go_back_N
    global MSS
    global data_flag
    global client_socket
    global lock
    global localtime
    localtime = time.time()

    condition = threading.Condition()
    lock = Lock()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # no need to bind to a port, it's in the packet

    if len(sys.argv) != 6:
        raise ValueError('Input list format should be: Simple_ftp_client '
                         'client_host_name client_port# file_name N MSS')
    sys.argv.pop(0)
    client_name, client_port, file_name, go_back_N, MSS = sys.argv
    client_port = int(client_port)
    go_back_N = int(go_back_N)
    client_socket.bind(('0.0.0.0', client_port))

    buffer_list = list()
    with open(file_name, "r") as file:  # with encapsulates common preparation and cleanup tasks
        while 1:
            MSS_string = file.read(int(MSS))
            if MSS_string != '':  # the end of a file is '' not false
                buffer_list.append(MSS_string)
            else:
                break
    try:
        thread_first = threading.Thread(target=recv_ack, args=(condition,))
        thread_first.daemon = True
        thread_first.start()
        thread_second = threading.Thread(target=rdt_send, args=(buffer_list, condition))
        thread_second.daemon = True
        thread_second.start()
        thread_second.join()
    except KeyboardInterrupt:
        sys.exit(0)


def recv_ack(condition):
    global last_ack_num
    global lock
    global ack_flag
    global client_socket
    try:
        while 1:
            ack_byte, addr = client_socket.recvfrom(1024)
            ack_num, zeros, ack_flag = pickle.loads(ack_byte)
            #print("received ack_num: " + str(ack_num))

            if zeros == '0000000000000000' and ack_flag == ack_flag:
                with condition:  # automatically call acquire at beginning and release at the end of block
                    if last_ack_num is None:
                        last_ack_num = ack_num
                        condition.notify()
                        #print("Updated ack")
                    elif ack_num > last_ack_num:
                        last_ack_num = ack_num
                        condition.notify()
                        #print("Updated ack")
    except KeyboardInterrupt:
        sys.exit(0)


def checksum(pkt):
    return 0xfff

def sendWindow(window):
    global client_socket
    global server_hostname
    global server_port
    for win in window:
        #print(server_hostname)
        client_socket.sendto(win, (server_hostname, server_port))


def rdt_send(buffer_list, condition):
    global last_ack_num
    global go_back_N
    global data_flag
    global server_hostname
    global server_port
    global client_socket
    global lock
    global localtime

    RTT = 0.2
    max_ack = len(buffer_list) - 1

    while True:
        # add seq#
        # add checksum
        # add data_flag
        with condition:
            before_ack_number = last_ack_num
            #print("Last ack val: "+str(last_ack_num))

        if before_ack_number < max_ack:
            window = list()
            last_packet_ack_number = before_ack_number
            # implement lock
            while len(window) < go_back_N and last_packet_ack_number < max_ack:
                # send the next n packets
                packet = list()
                header = list()
                header.append(last_packet_ack_number + 1)
                header.append(checksum(buffer_list[last_packet_ack_number + 1]))
                header.append(data_flag)
                packet.append(header)
                packet.append(buffer_list[last_packet_ack_number + 1])

                last_packet_ack_number += 1
                #print("Sending " + str(last_packet_ack_number))
                packet = pickle.dumps(packet)
               # print(type(packet))
                window.append(packet)

            sendWindow(window)
            with condition:
                after_ack_number = last_ack_num
                if after_ack_number == before_ack_number:
                    condition.wait(float(RTT))  # should wake up upon last_ack_num changes!
        else:

            #completed,send the end packet
            last_packet_ack_number = before_ack_number
            # implement lock
            # send the next n packets
            packet = list()
            header = list()
            header.append(last_packet_ack_number + 1)
            header.append(checksum(end_flag))
            header.append(end_flag)
            packet.append(header)
            packet.append(end_flag)

            last_packet_ack_number += 1
            #print("Sending end packet" + str(last_packet_ack_number))
            packet = pickle.dumps(packet)

            window.append(packet)
            sendWindow(window)

            finaltime = time.time()

            print("Time Passed: "+ str(finaltime - localtime))
            break;



if __name__ == "__main__":
    start_client()
