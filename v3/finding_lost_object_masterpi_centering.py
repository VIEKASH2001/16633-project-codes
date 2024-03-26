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
find = "dog"
# model
model = YOLO("yolo-Weights/yolov8n.pt")
# object classes
classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
              "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
              "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
              "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
              "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
              "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
              "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
              "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
              "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
              "teddy bear", "hair drier", "toothbrush"
              ]
# Find the index of the class you're looking for
target_class_index = classNames.index(find)

# URL of the MJPEG stream from the Raspberry Pi
stream_url = 'http://192.168.149.1:8080'

# Create VideoCapture object
cap = cv2.VideoCapture(stream_url)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Couldn't open the stream")
    exit()





size = (640,480)
def map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def getAreaMaxContour (contours): 
    contour_area_temp = 0 
    contour_area_max = 0
    areaMaxContour = None #
    for c in contours:
        contour_area_temp = math.fabs(cv2.contourArea(c))
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp > 300: 
                areaMaxContour = c
    return areaMaxContour, contour_area_max 

while True:
    loop_start_time = time.time()  # Capture start time of the loop
    ret, img = cap.read()
    if not ret:
        print("Error: Couldn't read frame")
        break
    img_h, img_w = img.shape[:2]
    frame_center = (img_w // 2, img_h // 2)
    cv2.circle(img, frame_center, radius=5, color=(0, 0, 255), thickness=-1)

    results = model(img, stream=True)

    for r in results:
        boxes = r.boxes

        filtered_boxes = [box for box in boxes if int(box.cls[0]) == target_class_index and math.ceil((box.conf[0]*100))/100 > 0.5]

        for box in filtered_boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            bounding_box_area = (x2 - x1) * (y2 - y1)
            areaMaxContour = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])
            (center_x, center_y), radius = cv2.minEnclosingCircle(areaMaxContour)
            center_x = int(map(center_x, 0, size[0], 0, img_w))
            center_y = int(map(center_y, 0, size[1], 0, img_h))
            radius = int(map(radius, 0, size[0], 0, img_w))
            object_center = (center_x, center_y)
            disp_text = f"X: {center_x}, Y: {center_y}"
            cv2.putText(img, disp_text, object_center, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 160, 160), 2)
            data = f"{center_x},{center_y}"
            client_socket.sendall(data.encode())

    cv2.imshow('Webcam', img)
    if cv2.waitKey(1) == ord('q'):
        break
    
    loop_end_time = time.time()  # Capture end time of the loop
    loop_duration = loop_end_time - loop_start_time  # Calculate the duration of the loop
    print(f"Loop Time: {loop_duration:.2f} seconds")  # Print the duration of each loop iteration

# Don't forget to close the socket when done
client_socket.close()
# Release the VideoCapture object and close OpenCV windows
cap.release()
cv2.destroyAllWindows()
