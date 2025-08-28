import numpy as np
import math

def pixel_to_real_world(pixel_point, H):
    pt = np.array([[pixel_point[0], pixel_point[1], 1]], dtype=np.float32).T
    world = np.dot(H, pt)
    if world[2] == 0:
        raise ValueError("Invalid homography transform (division by zero).")
    return (world[0] / world[2])[0], (world[1] / world[2])[0]


def calculate_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
