import cv2
import numpy as np
import re
import math
import textwrap
import platform
import subprocess
from typing import Iterator, Tuple
from importlib_metadata import version as get_package_version

class Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def letterbox(
    im,
    new_shape,
    color=(114, 114, 114),
    auto=False,
    scaleFill=False,
    scaleup=True,
    stride=32,
):
    """
    Resize and pad image while meeting stride-multiple constraints
    Returns:
        im (array): (height, width, 3)
        ratio (array): [w_ratio, h_ratio]
        (dw, dh) (array): [w_padding h_padding]
    """
    shape = im.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):  # [h_rect, w_rect]
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # only scale down, do not scale up (for better val mAP)
        r = min(r, 1.0)

    # Compute padding
    ratio = r, r  # wh ratios
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))  # w h
    dw, dh = (
        new_shape[1] - new_unpad[0],
        new_shape[0] - new_unpad[1],
    )  # wh padding

    if auto:  # minimum rectangle
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding
    elif scaleFill:  # stretch
        dw, dh = 0.0, 0.0
        new_unpad = (new_shape[1], new_shape[0])  # [w h]
        ratio = (
            new_shape[1] / shape[1],
            new_shape[0] / shape[0],
        )  # [w_ratio, h_ratio]

    dw /= 2  # divide padding into 2 sides
    dh /= 2
    if shape[::-1] != new_unpad:  # resize
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(
        im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
    )
    return im, ratio, (dw, dh)


def softmax(x):
    """
    Applies the softmax function to the input array.

    Args:
        x (numpy.ndarray): Input array.

    Returns:
        numpy.ndarray: Output array after applying softmax.
    """
    x = x.reshape(-1)
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)


def refine_contours(contours, img_area, epsilon_factor=0.001):
    """
    Refine contours by approximating and filtering.

    Parameters:
    - contours (list): List of input contours.
    - img_area (int): Maximum factor for contour area.
    - epsilon_factor (float, optional): Factor used for epsilon calculation in contour approximation. Default is 0.001.

    Returns:
    - list: List of refined contours.
    """
    # Refine contours
    approx_contours = []
    for contour in contours:
        # Approximate contour
        epsilon = epsilon_factor * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        approx_contours.append(approx)

    # Remove too big contours ( >90% of image size)
    if len(approx_contours) > 1:
        areas = [cv2.contourArea(contour) for contour in approx_contours]
        filtered_approx_contours = [
            contour
            for contour, area in zip(approx_contours, areas)
            if area < img_area * 0.9
        ]

    # Remove small contours (area < 20% of average area)
    if len(approx_contours) > 1:
        areas = [cv2.contourArea(contour) for contour in approx_contours]
        avg_area = np.mean(areas)

        filtered_approx_contours = [
            contour
            for contour, area in zip(approx_contours, areas)
            if area > avg_area * 0.2
        ]
        approx_contours = filtered_approx_contours

    return approx_contours


def point_in_bbox(point, bbox):
    """
    Check if a point is inside a bounding box.

    Parameters:
    - point: Tuple (x, y) representing the point coordinates.
    - bbox: List [xmin, ymin, xmax, ymax] representing the bounding box.

    Returns:
    - True if the point is inside the bounding box, False otherwise.
    """
    x, y = point
    xmin, ymin, xmax, ymax = bbox

    # Check if the point is within the bounding box.
    if xmin <= x <= xmax and ymin <= y <= ymax:
        return True
    else:
        return False


def format_bold(text):
    return f"\033[1m{text}\033[0m"


def format_color(text, color_code):
    return f"\033[{color_code}m{text}\033[0m"


def gradient_text(
    text: str,
    start_color: Tuple[int, int, int] = (0, 0, 255),
    end_color: Tuple[int, int, int] = (255, 0, 255),
    frequency: float = 1.0,
) -> str:

    def color_function(t: float) -> Tuple[int, int, int]:
        def interpolate(start: float, end: float, t: float) -> float:
            # Use a sine wave for smooth, periodic interpolation
            return (
                start
                + (end - start) * (math.sin(math.pi * t * frequency) + 1) / 2
            )

        return tuple(
            round(interpolate(s, e, t)) for s, e in zip(start_color, end_color)
        )

    def gradient_gen(length: int) -> Iterator[Tuple[int, int, int]]:
        return (color_function(i / (length - 1)) for i in range(length))

    gradient = gradient_gen(len(text))
    return "".join(
        f"\033[38;2;{r};{g};{b}m{char}\033[0m"
        for char, (r, g, b) in zip(text, gradient)
    )  # noqa: E501


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def indent_text(text, indent=4):
    return textwrap.indent(text, " " * indent)


def is_chinese(s="人工智能"):
    # Is string composed of any Chinese characters?
    return bool(re.search("[\u4e00-\u9fff]", str(s)))


def is_possible_rectangle(points):
    if len(points) != 4:
        return False

    # Check if four points form a rectangle
    # The points are expected to be in the format:
    # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    dists = [square_dist(points[i], points[(i + 1) % 4]) for i in range(4)]
    dists.sort()

    # For a rectangle, the two smallest distances
    # should be equal and the two largest should be equal
    return dists[0] == dists[1] and dists[2] == dists[3]


def square_dist(p, q):
    # Calculate the square distance between two points
    return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2


def collect_system_info():
    os_info = platform.platform()
    cpu_info = platform.processor()
    gpu_info = get_gpu_info()
    cuda_info = get_cuda_version()
    python_info = platform.python_version()
    pyqt5_info = get_installed_package_version("PyQt5")
    onnx_info = get_installed_package_version("onnx")
    ort_info = get_installed_package_version("onnxruntime")
    ort_gpu_info = get_installed_package_version("onnxruntime-gpu")
    opencv_contrib_info = get_installed_package_version(
        "opencv-contrib-python-headless"
    )

    system_info = {
        "Operating System": os_info,
        "CPU": cpu_info,
        "GPU": gpu_info,
        "CUDA": cuda_info,
        "Python Version": python_info,
    }
    pkg_info = {
        "PyQt5 Version": pyqt5_info,
        "ONNX Version": onnx_info,
        "ONNX Runtime Version": ort_info,
        "ONNX Runtime GPU Version": ort_gpu_info,
        "OpenCV Contrib Python Headless Version": opencv_contrib_info,
    }

    return system_info, pkg_info


def get_installed_package_version(package_name):
    try:
        return get_package_version(package_name)
    except Exception:
        return None


def get_cuda_version():
    try:
        nvcc_output = subprocess.check_output(["nvcc", "--version"]).decode(
            "utf-8"
        )
        version_line = next(
            (line for line in nvcc_output.split("\n") if "release" in line),
            None,
        )
        if version_line:
            return version_line.split()[-1]
    except Exception:
        return None


def get_gpu_info():
    try:
        smi_output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            encoding="utf-8",
        )
        return ", ".join(smi_output.strip().split("\n"))
    except Exception:
        return None
