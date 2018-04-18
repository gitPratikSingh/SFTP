import argparse
import socket
import pickle
import random

SERVER_PORT = None
SERVER_FILE_NAME = None
PROBABILITY_LOSS = None
HOST_NAME = None
CLIENT_PORT = None

next_sequence_num = None
server_socket = None


def init():
    parser = argparse.ArgumentParser()
    parser.add_argument("--p", help="Server port number", default=7735, type=int, required=False)
    parser.add_argument("--f", help="File name", default='write.txt', required=False)
    parser.add_argument("--h", help="Host name", default='localhost', required=False)
    parser.add_argument("--l", help="Probability of packet loss", default=0.20, type=float, required=False)
    parser.add_argument("--cp", help="Client port", default=12345, type=int, required=False)

    args = parser.parse_args()

    global SERVER_PORT
    global SERVER_FILE_NAME
    global PROBABILITY_LOSS
    global HOST_NAME
    global next_sequence_num
    global server_socket
    global CLIENT_PORT

    SERVER_PORT = args.p
    SERVER_FILE_NAME = args.f
    PROBABILITY_LOSS = args.l
    HOST_NAME = args.h
    CLIENT_PORT = args.cp

    next_sequence_num = 0
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((HOST_NAME, SERVER_PORT))

    # empty the existing file
    open(SERVER_FILE_NAME, 'w').close()


def recvStream():
    global server_socket
    msg, claddr = server_socket.recvfrom(65636)
    return msg, claddr

def checksum(pkt):
    return 0xfff

def verifyChecksum(packet_checksum, packet_mss):
    val = checksum(packet_mss) == packet_checksum
    print("Checksum: "+ str(val))
    return val


def sendackmessage(acknum, clientaddr):
    global CLIENT_PORT
    PADDING = "0000000000000000"
    ACK = "1010101010101010"

    ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   #why need another socket?
    ack_packet = [acknum, PADDING, ACK]  # why padding?
    ack_packet = pickle.dumps(ack_packet)

    ack_socket.sendto(ack_packet, clientaddr)
    ack_socket.close()


def processdata(packet_mss, ack_sequence_num, clientaddr):
    global SERVER_FILE_NAME
    with open(SERVER_FILE_NAME, 'a') as file:
        file.write(packet_mss)

    sendackmessage(ack_sequence_num, clientaddr)


def start_server():
    global PROBABILITY_LOSS
    global next_sequence_num
    global server_socket

    DATA_TYPE = "0101010101010101"
    END = "1111111111111111"

    init()

    while True:
        clientData, clientaddr = recvStream()
        clientData = pickle.loads(clientData)

        packet_header, packet_mss = clientData[0], clientData[1]
        packet_sequence_number, packet_checksum, packet_type = packet_header[0], packet_header[1], packet_header[2]

        print("Received Packet" + str(packet_sequence_number))

        if type == END:  # type variable hasn't initialized yet?
            print("Received File!")
            print("Closing Socket")
            server_socket.close()
            break

        if next_sequence_num == packet_sequence_number and verifyChecksum(packet_checksum,
                                                                          packet_mss) and packet_type == DATA_TYPE:
            # good packet
            # generate a random number
            if PROBABILITY_LOSS >= random.uniform(0, 1):
                print("Packet loss, sequence number =" + str(packet_sequence_number))
            else:
                # process packet and send ack
                processdata(packet_mss, next_sequence_num, clientaddr)
                next_sequence_num += 1
        elif next_sequence_num > packet_sequence_number and verifyChecksum(packet_checksum,
                                                                          packet_mss) and packet_type == DATA_TYPE:
            sendackmessage(next_sequence_num, clientaddr)
        else:
            # discard packet
            print("Packet dropped, sequence number =" + str(packet_sequence_number) + " Seqno desired" + str(next_sequence_num))


if __name__ == "__main__":
    print("Starting Server")
    start_server()
