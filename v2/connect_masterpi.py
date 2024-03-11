import cv2

# URL of the MJPEG stream from the Raspberry Pi
stream_url = 'http://192.168.149.1:8080'

# Create VideoCapture object
cap = cv2.VideoCapture(stream_url)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Couldn't open the stream")
    exit()

# Read and display frames from the stream
while True:
    ret, frame = cap.read()

    if not ret:
        print("Error: Couldn't read frame")
        break

    cv2.imshow('MJPG Stream', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the VideoCapture object and close OpenCV windows
cap.release()
cv2.destroyAllWindows()
