import pyrealsense2 as rs
import numpy as np
import cv2
import time

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# Start streaming
profile = pipeline.start(config)
depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()

# Create an align object
align = rs.align(rs.stream.color)

# Define the codec and create VideoWriter object to record the video
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('overlay_output.avi', fourcc, 20.0, (640, 480))

start_time = time.time()  # Record the start time

try:
    while True:
        # Stop recording after 10 seconds
        if time.time() - start_time > 10:
            break

        frames = pipeline.wait_for_frames()

        # Align the depth frame to color frame
        aligned_frames = align.process(frames)

        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()

        if not depth_frame or not color_frame:
            continue

        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=255/depth_image.max()), cv2.COLORMAP_JET)

        # Overlay the depth colormap onto the color image
        overlay = cv2.addWeighted(color_image, 0.6, depth_colormap, 0.4, 0)

        # Save the overlay to a video file
        out.write(overlay)

        # Display the overlay
        cv2.imshow('Overlay', overlay)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Stop streaming
    pipeline.stop()
    # Release the video writer
    out.release()
    # Close all OpenCV windows
    cv2.destroyAllWindows()
