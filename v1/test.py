import cv2
import socket
import pickle
import struct

# Initialize socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#client_socket.settimeout(10)  # Increase timeout to 10 seconds
client_socket.connect(('192.168.149.1', 8000))

data = b""
payload_size = struct.calcsize("L")

while True:
    while len(data) < payload_size:
        data += client_socket.recv(4096)
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("L", packed_msg_size)[0]
    
    while len(data) < msg_size:
        data += client_socket.recv(4096)
    frame_data = data[:msg_size]
    data = data[msg_size:]
    
    frame = pickle.loads(frame_data)
    
    cv2.imshow('frame', frame)
    cv2.waitKey(1)
