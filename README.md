# SFTP
Go-back-N automatic repeat request (ARQ)


Implementation of ARQ schemes and reliable data transfer protocols and build a number of fundamental skills related to writing
transport layer services, including:

• encapsulating application data into transport layer segments by including transport headers,

• buffering and managing data received from, or to be delivered to, the application,

• managing the window size at the sender,

• computing checksums, and

• using the UDP socket interface.


To run Client:
    python Simple_ftp_client.py localhost 12345 data_file.txt 10 1500

To run Server:
