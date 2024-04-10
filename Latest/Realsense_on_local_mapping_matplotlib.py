import pyrealsense2 as rs
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

# Start streaming
profile = pipeline.start(config)

# Skip some frames to allow for auto-exposure stabilization
for _ in range(30):
    pipeline.wait_for_frames()

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

def update_frame():
    frames = pipeline.wait_for_frames()
    depth_frame = frames.get_depth_frame()
    if not depth_frame:
        return

    # Create a point cloud object
    pc = rs.pointcloud()
    points = pc.calculate(depth_frame)
    vtx = np.asanyarray(points.get_vertices())
    depth = np.asanyarray(depth_frame.get_data())

    # Extract x, y, z coordinates from vertices
    x = np.asanyarray(vtx['f0'], dtype=np.float32)
    y = np.asanyarray(vtx['f1'], dtype=np.float32)
    z = np.asanyarray(vtx['f2'], dtype=np.float32)

    # Filter out points with zero depth
    valid = z > 0
    x = x[valid]
    y = y[valid]
    z = z[valid]
    depth = depth.flatten()[valid]

    ax.clear()
    ax.scatter(x, y, z, c=depth, s=1, cmap='viridis', marker='.')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.draw()
    plt.pause(0.01)

try:
    plt.ion()
    while True:
        update_frame()

finally:
    plt.ioff()
    pipeline.stop()
    plt.show()
