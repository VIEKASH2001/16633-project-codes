#!/usr/bin/env python3
# encoding:utf-8
import pyrealsense2 as rs
import numpy as np
import cv2
## /usr/bin/python3 /home/pi/Desktop/realsense_stream.py to run
# Create a pipeline
pipeline = rs.pipeline()

# Create a config and configure the pipeline to stream
# depth frames at 640x480 resolution and 30 frames per second
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

# Start streaming
pipeline.start(config)

try:
    while True:
        # Wait for a coherent pair of frames: depth
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        if not depth_frame:
            continue

        # Convert depth frame to numpy array to render image in opencv
        depth_image = np.asanyarray(depth_frame.get_data())

        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        # Show depth frame
        cv2.imshow('Depth Frame', depth_colormap)

        # Press 'q' on the keyboard to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    # Stop streaming
    pipeline.stop()
    cv2.destroyAllWindows()
