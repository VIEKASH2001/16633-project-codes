import cv2
import numpy as np
import open3d as o3d
import socket
import time

def depth_image_to_point_cloud(depth_image, camera_intrinsics):
    """
    Convert a depth image to a 3D point cloud.

    Parameters:
        depth_image: A numpy array of the depth image, assumed to be a 16-bit unsigned integer array.
        camera_intrinsics: Open3D camera intrinsics object.
    Returns:
        An Open3D point cloud object.
    """
    depth_o3d = o3d.geometry.Image(depth_image)
    pcd = o3d.geometry.PointCloud.create_from_depth_image(
        depth_o3d, camera_intrinsics, depth_scale=1000.0, depth_trunc=3.0)
    return pcd

def estimate_camera_pose_and_update_map(current_pcd, previous_pcd, previous_pose):
    """
    Estimate the camera pose by aligning the current point cloud to the previous one and update the map.

    Parameters:
        current_pcd: Current point cloud.
        previous_pcd: Previous point cloud.
        previous_pose: The previous pose of the camera.
    Returns:
        The updated pose and updated map as a point cloud.
    """
    registration_result = o3d.pipelines.registration.registration_icp(
        current_pcd, previous_pcd, 0.02, previous_pose,
        o3d.pipelines.registration.TransformationEstimationPointToPlane())
    updated_pose = registration_result.transformation
    updated_map = previous_pcd + current_pcd.transform(updated_pose)
    return updated_pose, updated_map

# Assuming you have the Raspberry Pi's IP address and a chosen port
RASPBERRY_PI_IP = '192.168.149.1'  # Example IP
PORT = 65432  # Example port

# Connect to the Raspberry Pi
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((RASPBERRY_PI_IP, PORT))
stream_url = 'http://192.168.149.1:8080'

# Create VideoCapture object
cap = cv2.VideoCapture(stream_url)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Couldn't open the stream")
    exit()

# Setup for SLAM
camera_intrinsics = o3d.camera.PinholeCameraIntrinsic(
    o3d.camera.PinholeCameraIntrinsicParameters.PrimeSenseDefault)
global_map = o3d.geometry.PointCloud()
previous_pose = np.eye(4)  # Identity matrix for initial pose
previous_pcd = o3d.geometry.PointCloud()

# Begin SLAM loop
while True:
    ret, encoded_depth_image = cap.read()
    if not ret:
        print("Error: Couldn't read frame")
        break
    
    # Decode the received depth image (this step depends on how you encode/decode your depth data)
    # For demonstration, let's assume encoded_depth_image is directly in a 16-bit format
    # In reality, you may need to decode or convert this data based on your transmission method
    # Example: depth_image_uint16 = decode_depth_image(encoded_depth_image)
    depth_image_uint16 = np.array(encoded_depth_image, dtype=np.uint16)  # Placeholder conversion
    
    current_pcd = depth_image_to_point_cloud(depth_image_uint16, camera_intrinsics)
    
    if not previous_pcd.is_empty():
        updated_pose, global_map = estimate_camera_pose_and_update_map(
            current_pcd, previous_pcd, previous_pose)
        previous_pose = updated_pose

    previous_pcd = current_pcd
    
    # For visualization (this may slow down your loop significantly)
    o3d.visualization.draw_geometries([global_map])

    # Display the captured depth frame for reference
    # Note: You may want to visualize the depth image differently, as it's a 16-bit image
    cv2.imshow('Depth Stream', depth_image)
    if cv2.waitKey(1) == ord('q'):
        break

# Cleanup
client_socket.close()
cap.release()
cv2.destroyAllWindows()
