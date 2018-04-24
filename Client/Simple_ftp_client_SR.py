import socket
import pickle
import sys
import threading
import time
from threading import Lock

client_name = None
client_port = None
file_name = None
go_back_N = None
MSS = None
seq_num = 0
data_flag = '0101010101010101'
ack_flag = '1010101010101010'
nak_flag = '1111111100000000'
end_flag = "1111111111111111"
last_ack_num = -1
last_ack_lock = Lock()
client_socket = None
server_hostname = '152.46.19.25'
server_port = 7735
localtime = None
send_quota = None
send_quota_lock = Lock()
pending_list_lock = Lock()
pending_pkt_list = list()


class PendingPkt:
    def __init__(self, packet='None', pkt_num=-1, condition='None', status=-1):
        self.packet = packet
        self.pkt_num = pkt_num
        self.condition = condition
        self.status = status  # 0->nothing; 1->ack; 2->nak


def start_client():
    global client_name
    global client_port
    global file_name
    global go_back_N
    global MSS
    global data_flag
    global client_socket
    global localtime
    global send_quota
    global send_quota_lock

    localtime = time.time()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # no need to bind to a port, it's in the packet
    if len(sys.argv) != 6:
        raise ValueError('Input list format should be: Simple_ftp_client '
                         'client_host_name client_port# file_name N MSS')
    sys.argv.pop(0)
    client_name, client_port, file_name, go_back_N, MSS = sys.argv
    client_port = int(client_port)
    go_back_N = int(go_back_N)
    client_socket.bind(('0.0.0.0', client_port))
    with send_quota_lock:  ##
        send_quota = go_back_N
    buffer_list = list()
    with open(file_name, "r") as file:  # with encapsulates common preparation and cleanup tasks
        while 1:
            MSS_string = file.read(int(MSS))
            if MSS_string != '':  # the end of a file is '' not false
                buffer_list.append(MSS_string)
            else:
                break
    if len(buffer_list) < 2*go_back_N:  ##
        raise ValueError('sequence number must be larger than two times the window size'
                         ', please decrease either segment size or window size ')
    try:
        thread_first = threading.Thread(target=recv)
        thread_first.daemon = True
        thread_first.start()
        thread_second = threading.Thread(target=rdt_send, args=(buffer_list,))
        thread_second.daemon = True
        thread_second.start()
        thread_second.join()
    except KeyboardInterrupt:
        sys.exit(0)


def recv():
    global ack_flag
    global nak_flag
    global client_socket
    global send_quota
    global send_quota_lock
    global last_ack_lock
    global last_ack_num
    global pending_list_lock
    global pending_pkt_list
    try:
        while 1:
            k_byte, addr = client_socket.recvfrom(1024)
            k_num, zeros, flag = pickle.loads(k_byte)
            # print("received ack_num: " + str(ack_num))
            if zeros == '0000000000000000' and flag == nak_flag:  ## buffer the unacked pkts
                with pending_list_lock:
                    for pending_pkt in pending_pkt_list:
                        if pending_pkt.pkt_num == k_num:
                            pending_pkt.status = 2
                            with pending_pkt.condition:
                                pending_pkt.condition.notify()
            elif zeros == '0000000000000000' and flag == ack_flag:
                with send_quota_lock:  # automatically call acquire at beginning and release at the end of block
                    send_quota += 1
                with last_ack_lock:
                    if k_num > last_ack_num:
                        last_ack_num = k_num
                with pending_list_lock:
                    for pending_pkt in pending_pkt_list:
                        if pending_pkt.pkt_num <= k_num:
                            pending_pkt.status = 1
                            with pending_pkt.condition:
                                pending_pkt.condition.notify()
    except KeyboardInterrupt:
        sys.exit(0)


def checksum(pkt):
    return 0xfff


def sendWindow(window):
    global client_socket
    global server_hostname
    global server_port
    print(window)
    for win in window:
        #print(server_hostname)
        client_socket.sendto(win, (server_hostname, server_port))


def rdt_send(buffer_list):
    global go_back_N
    global data_flag
    global server_hostname
    global server_port
    global client_socket
    global localtime
    global send_quota
    global send_quota_lock
    global pending_list_lock
    global pending_pkt_list
    max_ack = len(buffer_list) - 1

    while True:
        # add seq#
        # add checksum
        # add data_flag
        before_ack_number = last_ack_num
        # print("Last ack val: "+str(last_ack_num))

        if before_ack_number < max_ack:
            window = list()
            last_packet_ack_number = before_ack_number
            # implement lock
            new_packet = False
            while send_quota > 0 and last_packet_ack_number < max_ack:
                # send the next n packets
                new_packet = True
                packet = list()
                header = list()
                header.append(last_packet_ack_number + 1)
                header.append(checksum(buffer_list[last_packet_ack_number + 1]))
                header.append(data_flag)
                packet.append(header)
                packet.append(buffer_list[last_packet_ack_number + 1])
                last_packet_ack_number += 1
                # print("Sending " + str(last_packet_ack_number))
                packet = pickle.dumps(packet)
                # print(type(packet))
                window.append(packet)
                pending_pkt = PendingPkt(packet, last_packet_ack_number, threading.Condition(), 0)
                with pending_list_lock:
                    pending_pkt_list.append(pending_pkt)
                thread_pending = threading.Thread(target=pkt_timer, args=(pending_pkt,))
                thread_pending.daemon = True
                thread_pending.start()
                with send_quota_lock:
                    send_quota -= 1
            if new_packet:
                sendWindow(window)
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

            print("Time Passed: " + str(finaltime - localtime))
            break;


def pkt_timer(pending_pkt):
    global pending_pkt_list
    timer = 0.2

    while 1:
        with pending_pkt.condition:
            pending_pkt.condition.wait(timer)
            if pending_pkt.status == 0 or pending_pkt.status == 2:
                sendWindow(pending_pkt.packet)
            elif pending_pkt.status == 1:
                for i in range(pending_pkt_list):
                    if pending_pkt_list[i] == pending_pkt:
                        pending_pkt_list.pop(i)
                break


if __name__ == "__main__":
    start_client()
