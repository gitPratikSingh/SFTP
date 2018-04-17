import socket
import hashlib
import pickle
import sys
import threading
from threading import Lock
client_name = ''
client_port = ''
file_name = ''
go_back_N = ''
MSS = ''
seq_num = 0
data_flag = '0101010101010101'
last_ack_num = -1

def start_client():
    global client_name
    global client_port
    global file_name
    global go_back_N
    global MSS
    global data_flag
    client_socket = socket(socket.AF_INET, socket.SOCK_GRAM)
    if len(sys.argv) != 6:
        raise ValueError('Input Argument list should be: Simple_ftp_client '
                         'client_host_name client_port# file_name N MSS')
    sys.argv.pop(0)
    client_name, client_port, file_name, go_back_N, MSS = sys.argv
    file = open(file_name, "r")
    buffer_list = list()
    while 1:
        str_data = file.read(int(MSS))
        if str_data:
            byte_data = pickle.dumps(str_data)
            buffer_list.append(byte_data)
        else:
            break
    rdt_send(buffer_list, client_socket)
    try:
        thread_first = threading.Thread(target=recv_ack,arg=client_socket)
        thread_first.daemon = True
        thread_first.start()
        thread_first.join()
    except KeyboardInterrupt:
        sys.exit(0)

def recv_ack(client_socket):
    global last_ack_num
    lock = Lock()
    while 1:
        ack_byte = client_socket.recvfrom(2048)
        ack_num, zeros, ack_flag = pickle.loads(ack_byte)
        if zeros == 0 and ack_flag == '0101010101010101':
            if ack_num > last_ack_num:
                lock.acquire()
                last_ack_num = ack_num
                lock.release()


def rdt_send(buffer_list, client_socket):


if __name__ == "__main__":
    print('Client is ready to go!')
    start_client()

