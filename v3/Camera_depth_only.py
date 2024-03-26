#!/usr/bin/env python3
# encoding:utf-8
import sys
sys.path.append('/home/pi/MasterPi/')
import cv2
import pyrealsense2 as rs
import time
import threading
import numpy as np
from CameraCalibration.CalibrationConfig import *

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

class Camera:
    def __init__(self, resolution=(640, 480)):
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.width = resolution[0]
        self.height = resolution[1]
        self.frame = None
        self.opened = False
        # Load calibration parameters
        self.param_data = np.load(calibration_param_path + '.npz')
        
        # Get calibration parameters
        self.mtx = self.param_data['mtx_array']
        self.dist = self.param_data['dist_array']
        self.newcameramtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (self.width, self.height), 0, (self.width, self.height))
        
        self.th = threading.Thread(target=self.camera_task, args=(), daemon=True)
        self.th.start()

    def camera_open(self):
        try:
            # Configure the pipeline to stream depth frames
            self.config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, 30)
            # Start streaming
            self.pipeline.start(self.config)
            self.opened = True
        except Exception as e:
            print('Failed to open RealSense camera:', e)

    def camera_close(self):
        try:
            self.opened = False
            time.sleep(0.2)
            self.pipeline.stop()
        except Exception as e:
            print('Failed to close RealSense camera:', e)

    def camera_task(self):
        while True:
            try:
                if self.opened:
                    # Wait for a coherent pair of frames: depth
                    frames = self.pipeline.wait_for_frames()
                    depth_frame = frames.get_depth_frame()
                    if not depth_frame:
                        continue
                    
                    # Convert depth frame to numpy array to render image in opencv
                    depth_image = np.asanyarray(depth_frame.get_data())
                    
                    # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
                    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
                    self.frame = depth_colormap
                else:
                    time.sleep(0.01)
            except Exception as e:
                print('Error acquiring RealSense camera image:', e)
                time.sleep(0.01)

if __name__ == '__main__':
    my_camera = Camera()
    my_camera.camera_open()
    while True:
        img = my_camera.frame
        if img is not None:
            cv2.imshow('Depth Image', img)
            key = cv2.waitKey(1)
            if key == 27:  # Escape key
                break
    my_camera.camera_close()
    cv2.destroyAllWindows()
