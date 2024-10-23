import base64
import os
from math import sqrt

import numpy as np

from .box import *
from .general import *
from .points_conversion import *

def distance_to_line(point, line):
    p1, p2 = line
    p1 = np.array([p1.x(), p1.y()])
    p2 = np.array([p2.x(), p2.y()])
    p3 = np.array([point.x(), point.y()])
    if np.dot((p3 - p1), (p2 - p1)) < 0:
        return np.linalg.norm(p3 - p1)
    if np.dot((p3 - p2), (p1 - p2)) < 0:
        return np.linalg.norm(p3 - p2)
    if np.linalg.norm(p2 - p1) == 0:
        return 0
    return np.linalg.norm(np.cross(p2 - p1, p1 - p3)) / np.linalg.norm(p2 - p1)

def distance(p):
    return sqrt(p.x() * p.x() + p.y() * p.y())

def point_in_polygon(point, polygon):
    """
    Determine if a point is inside a polygon using the ray casting algorithm.

    Args:
        point: A tuple (x, y) representing the point to test.
        polygon: A list of tuples [(x1, y1), (x2, y2), ...], representing the polygon vertices.

    Returns:
        True if the point is inside the polygon; False otherwise.
    """
    x, y = point
    num = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(num + 1):
        p2x, p2y = polygon[i % num]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if p1y != p2y:
                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y + 1e-12) + p1x
                if p1x == p2x or x <= xinters:
                    inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def point_near_line(point, line_points, epsilon=1e-6):
    """
    Check if a point is within epsilon distance of a line segment.

    Args:
        point: A tuple (x, y) representing the point to test.
        line_points: A list of two tuples [(x1, y1), (x2, y2)], representing the line segment endpoints.
        epsilon: The maximum allowed distance.

    Returns:
        True if the point is near the line segment; False otherwise.
    """
    x0, y0 = point
    x1, y1 = line_points[0]
    x2, y2 = line_points[1]

    # Line segment length squared
    dx = x2 - x1
    dy = y2 - y1
    line_len_sq = dx * dx + dy * dy

    # Avoid division by zero
    if line_len_sq == 0:
        # Line segment is a point
        dx0 = x0 - x1
        dy0 = y0 - y1
        distance_sq = dx0 * dx0 + dy0 * dy0
        return distance_sq <= epsilon * epsilon

    # Projection parameter t
    t = ((x0 - x1) * dx + (y0 - y1) * dy) / line_len_sq
    t = max(0, min(1, t))

    # Closest point on the line segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    # Distance from point to closest point
    dx0 = x0 - closest_x
    dy0 = y0 - closest_y
    distance_sq = dx0 * dx0 + dy0 * dy0

    return distance_sq <= epsilon * epsilon

def base64_img_to_rgb_cv_img(base64_img, img_path=None):
    """
    Convert a base64-encoded image or an image from a path to an 8-bit RGB image.

    Args:
        base64_img (str): The base64-encoded image string.
        img_path (str, optional): The file path to the image. Defaults to None.

    Returns:
        numpy.ndarray: The image as an 8-bit RGB NumPy array.
    """
    # print(base64_img)
    if img_path is not None and os.path.exists(img_path):
        # Load image from path directly
        # Note: Potential issue - unable to handle the flipped image.
        # Temporary workaround: cv_image = cv2.imread(img_path)
        cv_image = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), -1)
        if cv_image is None:
            raise ValueError(f"Could not read image from path: {img_path}")
    else:
        # Decode base64 image
        # 去掉 Base64 前缀（如果有）
        if base64_img.startswith('data:image'):
            base64_img = base64_img.split(',')[1]
        img_data = base64.b64decode(base64_img)
        # img_data = img_data.split(",")[1]
        img_array = np.frombuffer(img_data, np.uint8)
        cv_image = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)
        if cv_image is None:
            raise ValueError("Could not decode base64 image")

    # Ensure the image is in 8-bit unsigned integer format
    if cv_image.dtype != np.uint8:
        cv_image = cv2.normalize(cv_image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Convert image to RGB format
    if len(cv_image.shape) == 2:
        # Grayscale image
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2RGB)
    elif len(cv_image.shape) == 3:
        if cv_image.shape[2] == 1:
            # Single-channel image, treat as grayscale
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2RGB)
        elif cv_image.shape[2] == 3:
            # BGR image
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        elif cv_image.shape[2] == 4:
            # BGRA image
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGRA2RGB)
        else:
            raise ValueError("Unsupported image format with 3 channels")
    else:
        raise ValueError("Unsupported image format")

    return cv_image