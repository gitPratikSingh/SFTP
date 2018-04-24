import argparse
import socket
import pickle
import random
import socket


SERVER_PORT = None
SERVER_FILE_NAME = None
PROBABILITY_LOSS = None
HOST_NAME = None
CLIENT_PORT = None
buffer = list()
next_sequence_num = None
server_socket = None
seq_lack_list = list()

class BufferData:
    def __init__(self, packet_mss='None', packet_sequence_num=-1):
        self.packet_mss = packet_mss
        self.packet_sequence_num = packet_sequence_num


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
    HOST_NAME = 'localhost'
        #socket.gethostbyname(socket.gethostname())
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
    #print("Checksum: "+ str(val))
    return val


def sendackmessage(acknum, clientaddr):
    global CLIENT_PORT
    PADDING = "0000000000000000"
    ACK = "1010101010101010"
    ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ack_packet = [acknum, PADDING, ACK]
    ack_packet = pickle.dumps(ack_packet)

    print("Send Ack:" +str(acknum))
    ack_socket.sendto(ack_packet, clientaddr)
    ack_socket.close()


def sendNakMessage(naknum, clientaddr):
    global CLIENT_PORT
    NAK = '1111111100000000'
    PADDING = "0000000000000000"
    nak_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    nak_packet = [naknum, PADDING, NAK]
    nak_packet = pickle.dumps(nak_packet)

    print("Send Nak:" + str(naknum))
    nak_socket.sendto(nak_packet, clientaddr)
    nak_socket.close()

def processdata(packet_mss, ack_sequence_num, clientaddr):
    global SERVER_FILE_NAME
    with open(SERVER_FILE_NAME, 'a') as file:
        file.write(packet_mss)

    sendackmessage(ack_sequence_num, clientaddr)


def start_server():
    global PROBABILITY_LOSS
    global next_sequence_num
    global server_socket
    global buffer
    buffered = False
    DATA_TYPE = "0101010101010101"
    END = "1111111111111111"

    init()

    while True:
        clientData, clientaddr = recvStream()
        clientData = pickle.loads(clientData)

        packet_header, packet_mss = clientData[0], clientData[1]
        packet_sequence_number, packet_checksum, packet_type = packet_header[0], packet_header[1], packet_header[2]

        print("Received Packet" + str(packet_sequence_number) + "," + str(packet_checksum) + "," + str(packet_type))

        if packet_type == END:
            print("Received File!")
            server_socket.close()
            break

        if next_sequence_num == packet_sequence_number and verifyChecksum(packet_checksum,
                                                                          packet_mss) and packet_type == DATA_TYPE:
            # good packet
            # generate a random number
            if PROBABILITY_LOSS >= random.uniform(0, 1):
                print("Packet loss, sequence number =" + str(packet_sequence_number))
            else:
                if buffered:
                    buffer.append(BufferData(packet_mss, packet_sequence_num))
                    buffer.sort(key=lambda x: x.packet_sequence_num)
                    buffered = False
                    for i in range(1, len(buffer)):
                        if (buffer[i].packet_num - buffer[i-1].packet_num) != 1:
                            next_sequence_num = buffer[i-1].packet_num + 1
                            buffered = True
                            break
                    if not buffered:
                        for data in buffer:
                            processdata(data.packet_mss, data.packet_num, clientaddr)
                        next_sequence_num = buffer[-1].packet_num + 1
                else:
                    processdata(packet_mss, next_sequence_num, clientaddr)
                    next_sequence_num += 1
                #print("next_sequence_num" + str(next_sequence_num))
        else:
            # send nak for the seq. num we want
            sendNakMessage(next_sequence_num, clientaddr)
            # buffering the out-of-order data
            buffer.append(BufferData(packet_mss, packet_sequence_num))
            buffered = True
            #print("Packet dropped, sequence number =" + str(packet_sequence_number))


if __name__ == "__main__":
    print("Starting Server")
    start_server()
