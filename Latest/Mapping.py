import cv2
import numpy as np
import open3d as o3d

def depth_to_pointcloud(depth_image, camera_intrinsics):
    fx, fy = camera_intrinsics['fx'], camera_intrinsics['fy']
    cx, cy = camera_intrinsics['cx'], camera_intrinsics['cy']
    rows, cols = depth_image.shape
    c, r = np.meshgrid(np.arange(cols), np.arange(rows), sparse=True)
    z = depth_image  # Assuming depth_image is already in meters
    x = (c - cx) * z / fx
    y = (r - cy) * z / fy
    return np.dstack((x, y, z)).reshape((-1, 3))

camera_intrinsics = {
    'fx': 525.0,  # Focal length in x
    'fy': 525.0,  # Focal length in y
    'cx': 319.5,  # Optical center in x
    'cy': 239.5,  # Optical center in y
}

stream_url = 'http://192.168.149.1:8080'
cap = cv2.VideoCapture(stream_url)

if not cap.isOpened():
    print("Error: Couldn't open the stream")
    exit()

vis = o3d.visualization.Visualizer()
vis.create_window()

pcd = o3d.geometry.PointCloud()
vis.add_geometry(pcd)  # Add the point cloud geometry to the visualizer here, before the loop

while True:
    ret, depth_image = cap.read()
    if not ret:
        print("Error: Couldn't read frame")
        break

    # Convert the depth image to a floating point representation in meters
    depth_in_meters = cv2.cvtColor(depth_image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    depth_in_meters = np.clip(depth_in_meters, 0, 4)  # Valid depth range

    points = depth_to_pointcloud(depth_in_meters, camera_intrinsics)
    if len(points) > 0:
        pcd.points = o3d.utility.Vector3dVector(points)
        vis.update_geometry(pcd)  # Update the geometry with new points
        vis.poll_events()
        vis.update_renderer()
    else:
        print("No valid points in point cloud.")

    if cv2.waitKey(1) == ord('q'):
        break

vis.destroy_window()
cap.release()
cv2.destroyAllWindows()
