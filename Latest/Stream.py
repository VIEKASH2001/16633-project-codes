import cv2
from ultralytics import YOLO
import math 
import socket
import time
import numpy as np

# Assuming you have the Raspberry Pi's IP address and a chosen port
RASPBERRY_PI_IP = '192.168.149.1'  # Example IP, replace with your Raspberry Pi's IP
PORT = 65432  # Example port, choose an unused port
# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the Raspberry Pi
client_socket.connect((RASPBERRY_PI_IP, PORT))
stream_url = 'http://192.168.149.1:8080'

# Create VideoCapture object
cap = cv2.VideoCapture(stream_url)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Couldn't open the stream")
    exit()



while True:
    loop_start_time = time.time()  # Capture start time of the loop
    ret, img = cap.read()
    if not ret:
        print("Error: Couldn't read frame")
        break
    cv2.imshow('Webcam', img)
    if cv2.waitKey(1) == ord('q'):
        break

# Don't forget to close the socket when done
client_socket.close()
# Release the VideoCapture object and close OpenCV windows
cap.release()
cv2.destroyAllWindows()