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

# Change mode for different streams - 0 for RGB, 1 for Depth
class Camera:
    def __init__(self, resolution=(640, 480), mode=1):  # Changed mode default to 1 for Depth
        """
        Initialize the camera.
        
        Parameters:
            resolution (tuple): The resolution of the camera images.
            mode (int): Determines the type of images captured by the camera.
                        0 for RGB 2D images, 1 for 3D depth images.
        """
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.width, self.height = resolution
        self.frame = None
        self.opened = False
        self.mode = mode  # 0 for RGB, 1 for Depth

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
            if self.mode == 1:
                self.config.enable_stream(rs.stream.depth, self.width, self.height, rs.format.z16, 30)
            self.config.enable_stream(rs.stream.color, self.width, self.height, rs.format.bgr8, 30)
            
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
                    frames = self.pipeline.wait_for_frames()
                    if self.mode == 1:  # Depth mode
                        depth_frame = frames.get_depth_frame()
                        if not depth_frame:
                            continue
                        depth_image = np.asanyarray(depth_frame.get_data())
                        self.frame = depth_image
                    else:  # RGB mode
                        color_frame = frames.get_color_frame()
                        if not color_frame:
                            continue
                        self.frame = np.asanyarray(color_frame.get_data())
                else:
                    time.sleep(0.01)
            except Exception as e:
                print('Error acquiring RealSense camera image:', e)
                time.sleep(0.01)

if __name__ == '__main__':
    mode = 1  # Set this to 1 for depth images explicitly
    my_camera = Camera(mode=mode)
    my_camera.camera_open()
    while True:
        img = my_camera.frame
        if img is not None:
            # If you want to visualize the depth image, you'll need to convert it to a format suitable for display
            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(img, alpha=0.03), cv2.COLORMAP_JET)
            cv2.imshow('Depth Image', depth_colormap)  # Changed window name to 'Depth Image'
            key = cv2.waitKey(1)
            if key == 27:  # Escape key
                break
    my_camera.camera_close()
    cv2.destroyAllWindows()
