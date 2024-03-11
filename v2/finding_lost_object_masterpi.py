# optimized code with each looping time = 0.06 seconds
import cv2
from ultralytics import YOLO
import cv2
import math 
import time  # Import the time module
find = "person"
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

while True:
    loop_start_time = time.time()  # Capture start time of the loop
    ret, img = cap.read()
    if not ret:
        print("Error: Couldn't read frame")
        break

    results = model(img, stream=True)
    # coordinates
    for r in results:
        boxes = r.boxes

        # Filter boxes by target class and confidence level > 0.5
        filtered_boxes = [box for box in boxes if int(box.cls[0]) == target_class_index and math.ceil((box.conf[0]*100))/100 > 0.5]

        for box in filtered_boxes:
            # At this point, 'box' already matches the target class and has a high confidence
            cls = int(box.cls[0])
            confidence = math.ceil((box.conf[0]*100))/100
            print("Confidence --->", confidence)
            
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            # object details
            org = [x1, y1]
            font = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 1
            color = (255, 0, 0)
            thickness = 2
            cv2.putText(img, classNames[cls] + " found", org, font, fontScale, color, thickness)

    cv2.imshow('Webcam', img)
    if cv2.waitKey(1) == ord('q'):
        break
    
    loop_end_time = time.time()  # Capture end time of the loop
    loop_duration = loop_end_time - loop_start_time  # Calculate the duration of the loop
    print(f"Loop Time: {loop_duration:.2f} seconds")  # Print the duration of each loop iteration

# Release the VideoCapture object and close OpenCV windows
cap.release()
cv2.destroyAllWindows()








