import argparse
import socket
import pickle
import random
import hashlib
import sys

client_name = ''
client_port = ''
file_name = ''
go_back_N = ''
MSS = ''
seq_num = 0
data_flag = '0101010101010101'

def start_client():
    global client_name
    global client_port
    global file_name
    global go_back_N
    global MSS

    if len(sys.argv) != 6:
        raise ValueError('Input Argument list should be: Simple_ftp_client'
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
    rdt_send(buffer_list)


def rdt_send(buffer_list):


if __name__ == "__main__":
    print('Client is ready to go!')
    start_client()

