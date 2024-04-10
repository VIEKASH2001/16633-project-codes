import pyrealsense2 as rs
import numpy as np
import cv2
import time

# Initialize ORB detector
orb = cv2.ORB_create()

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start streaming
pipeline.start(config)

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 480))

start_time = time.time()
try:
    while True:
        # Break the loop after 20 seconds
        if time.time() - start_time > 20:
            break
        
        # Wait for a coherent pair of frames: color only
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        if not color_frame:
            continue

        # Convert images to numpy arrays
        color_image = np.asanyarray(color_frame.get_data())

        # Detect ORB features
        keypoints, descriptors = orb.detectAndCompute(color_image, None)

        # Draw keypoints on the color image
        output_image = cv2.drawKeypoints(color_image, keypoints, None, color=(0, 255, 0), flags=0)

        # Write the frame with detected features to the output video
        out.write(output_image)

        # Display the output image
        cv2.imshow('ORB Features', output_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Release everything if job is finished
    pipeline.stop()
    out.release()
    cv2.destroyAllWindows()
