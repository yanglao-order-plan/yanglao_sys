import copy
import cv2
import math
import uuid
import numpy as np
import PIL.Image
import PIL.ImageDraw
from utils.backend_utils.colorprinter import print_red
from work_flow.utils import point_in_polygon, point_near_line

# Default colors in BGR format (since OpenCV uses BGR)
DEFAULT_LINE_COLOR = (0, 255, 0)        # Green
DEFAULT_FILL_COLOR = (100, 100, 100)    # Gray





def polygons_to_mask(img_shape, polygons, shape_type=None):
    print_red(
        "The 'polygons_to_mask' function is deprecated, "
        "use 'shape_to_mask' instead."
    )
    return shape_to_mask(img_shape, points=polygons, shape_type=shape_type)


def shape_to_mask(
    img_shape, points, shape_type=None, line_width=10, point_size=5
):
    mask = np.zeros(img_shape[:2], dtype=np.uint8)
    mask = PIL.Image.fromarray(mask)
    draw = PIL.ImageDraw.Draw(mask)
    xy = [tuple(point) for point in points]
    if shape_type == "circle":
        assert len(xy) == 2, "Shape of shape_type=circle must have 2 points"
        (cx, cy), (px, py) = xy
        d = math.sqrt((cx - px) ** 2 + (cy - py) ** 2)
        draw.ellipse([cx - d, cy - d, cx + d, cy + d], outline=1, fill=1)
    elif shape_type == "rectangle":
        assert len(xy) == 2, "Shape of shape_type=rectangle must have 2 points"
        draw.rectangle(xy, outline=1, fill=1)
    elif shape_type == "rotation":
        assert len(xy) == 4, "Shape of shape_type=rotation must have 4 points"
        draw.polygon(xy=xy, outline=1, fill=1)
    elif shape_type == "line":
        assert len(xy) == 2, "Shape of shape_type=line must have 2 points"
        draw.line(xy=xy, fill=1, width=line_width)
    elif shape_type == "linestrip":
        draw.line(xy=xy, fill=1, width=line_width)
    elif shape_type == "point":
        assert len(xy) == 1, "Shape of shape_type=point must have 1 points"
        cx, cy = xy[0]
        r = point_size
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=1, fill=1)
    else:
        assert len(xy) > 2, "Polygon must have points more than 2"
        draw.polygon(xy=xy, outline=1, fill=1)
    mask = np.array(mask, dtype=bool)
    return mask


def shapes_to_label(img_shape, shapes, label_name_to_value):
    cls = np.zeros(img_shape[:2], dtype=np.int32)
    ins = np.zeros_like(cls)
    instances = []
    for shape in shapes:
        points = shape["points"]
        label = shape["label"]
        group_id = shape.get("group_id")
        if group_id is None:
            group_id = uuid.uuid1()
        shape_type = shape.get("shape_type", None)

        cls_name = label
        instance = (cls_name, group_id)

        if instance not in instances:
            instances.append(instance)
        ins_id = instances.index(instance) + 1
        cls_id = label_name_to_value[cls_name]

        mask = shape_to_mask(img_shape[:2], points, shape_type)
        cls[mask] = cls_id
        ins[mask] = ins_id

    return cls, ins


def masks_to_bboxes(masks):
    if masks.ndim != 3:
        raise ValueError(f"masks.ndim must be 3, but it is {masks.ndim}")
    if masks.dtype != bool:
        raise ValueError(
            f"masks.dtype must be bool type, but it is {masks.dtype}"
        )
    bboxes = []
    for mask in masks:
        where = np.argwhere(mask)
        (y1, x1), (y2, x2) = where.min(0), where.max(0) + 1
        bboxes.append((y1, x1, y2, x2))
    bboxes = np.asarray(bboxes, dtype=np.float32)
    return bboxes


def rectangle_from_diagonal(diagonal_vertices):
    """
    Generate rectangle vertices from diagonal vertices.

    Parameters:
    - diagonal_vertices (list of lists):
        List containing two points representing the diagonal vertices.

    Returns:
    - list of lists:
        List containing four points representing the rectangle's four corners.
        [tl -> tr -> br -> bl]
    """
    x1, y1 = diagonal_vertices[0]
    x2, y2 = diagonal_vertices[1]

    # Creating the four-point representation
    rectangle_vertices = [
        [x1, y1],  # Top-left
        [x2, y1],  # Top-right
        [x2, y2],  # Bottom-right
        [x1, y2],  # Bottom-left
    ]

    return rectangle_vertices



class Shape:
    """Shape data type with OpenCV drawing logic (without selection and highlight)"""

    KEYS = [
        "label",
        "score",
        "points",
        "group_id",
        "difficult",
        "shape_type",
        "flags",
        "description",
        "attributes",
    ]

    # The following class variables influence the drawing of all shape objects.
    _line_color = DEFAULT_LINE_COLOR
    _fill_color = DEFAULT_FILL_COLOR
    point_size = 4
    scale = 1.0
    line_width = 2

    def __init__(
        self,
        label=None,
        score=None,
        line_color=None,
        shape_type=None,
        flags=None,
        group_id=None,
        description=None,
        difficult=False,
        direction=0,
        attributes=None,
        kie_linking=None,
    ):
        self.label = label
        self.score = score
        self.group_id = group_id
        self.description = description
        self.difficult = difficult
        self.kie_linking = kie_linking if kie_linking is not None else []
        self.points = []
        self.fill = False
        self.shape_type = shape_type or "polygon"
        self.flags = flags or {}
        self.other_data = {}
        self.attributes = attributes or {}
        self.cache_label = None
        self.visible = True

        # Rotation setting
        self.direction = direction
        self.center = None
        self.show_degrees = True

        self._closed = False

        if line_color is not None:
            # Override the class line_color attribute
            self._line_color = line_color

    @property
    def shape_type(self):
        """Get shape type (polygon, rectangle, rotation, point, line, ...)"""
        return self._shape_type

    @shape_type.setter
    def shape_type(self, value):
        """Set shape type"""
        if value is None:
            value = "polygon"
        if value not in self.get_supported_shape():
            raise ValueError(f"Unexpected shape_type: {value}")
        self._shape_type = value

    @property
    def line_color(self):
        return self._line_color

    @line_color.setter
    def line_color(self, value):
        # 使用 wrap_color 方法来处理颜色
        self._line_color = self.wrap_color(value)

    @property
    def fill_color(self):
        return self._fill_color

    @fill_color.setter
    def fill_color(self, value):
        # 使用 wrap_color 方法来处理颜色
        self._fill_color = self.wrap_color(value)


    @staticmethod
    def get_supported_shape():
        return [
            "polygon",
            "rectangle",
            "rotation",
            "point",
            "line",
            "circle",
            "linestrip",
        ]

    def close(self):
        """Close the shape"""
        if self.shape_type == "rotation" and len(self.points) == 4:
            cx = (self.points[0][0] + self.points[2][0]) / 2
            cy = (self.points[0][1] + self.points[2][1]) / 2
            self.center = (cx, cy)
        self._closed = True

    def reach_max_points(self):
        """Check if the shape has reached its maximum number of points"""
        return len(self.points) >= 4

    def add_point(self, x, y):
        """Add a point to the shape"""
        point = (x, y)
        if self.shape_type == "rectangle":
            if not self.reach_max_points():
                self.points.append(point)
        else:
            if self.points and point == self.points[0]:
                self.close()
            else:
                self.points.append(point)

    def can_add_point(self):
        """Check if the shape can add more points"""
        return self.shape_type in ["polygon", "linestrip"]

    def pop_point(self):
        """Remove and return the last point of the shape"""
        if self.points:
            return self.points.pop()
        return None

    def insert_point(self, i, point):
        """Insert a point at a specific index"""
        self.points.insert(i, point)

    def remove_point(self, i):
        """Remove a point at a specific index"""
        self.points.pop(i)

    def is_closed(self):
        """Check if the shape is closed"""
        return self._closed

    def set_open(self):
        """Set the shape to be open"""
        self._closed = False

    @property
    def normalize_points(self):
        return [(float(p[0]), float(p[1])) for p in self.points]

    def to_dict(self):
        """Serialize the shape to a dictionary"""
        dict_data = {
            "label": self.label,
            "score": self.score,
            "points": self.normalize_points,
            "group_id": self.group_id,
            "description": self.description,
            "difficult": self.difficult,
            "shape_type": self.shape_type,
            "flags": self.flags,
            "attributes": self.attributes,
            "kie_linking": self.kie_linking,
        }
        if self.shape_type == "rotation":
            dict_data["direction"] = self.direction
        dict_data = {**self.other_data, **dict_data}
        return dict_data

    def load_from_dict(self, data: dict, close=True):
        """Load the shape from a dictionary"""
        self.label = data["label"]
        self.score = data.get("score")
        self.points = data["points"]
        self.group_id = data.get("group_id")
        self.description = data.get("description", "")
        self.difficult = data.get("difficult", False)
        self.shape_type = data.get("shape_type", "polygon")
        self.flags = data.get("flags", {})
        self.attributes = data.get("attributes", {})
        self.kie_linking = data.get("kie_linking", [])
        if self.shape_type == "rotation":
            self.direction = data.get("direction", 0)
        self.other_data = {k: v for k, v in data.items() if k not in self.KEYS}
        if close:
            self.close()
        return self

    def get_rect_from_line(self, pt1, pt2):
        """Get rectangle parameters from a diagonal line"""
        x1, y1 = pt1
        x2, y2 = pt2
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        return (int(left), int(top), int(width), int(height))

    def get_circle_params_from_line(self, line):
        """Compute parameters to define a circle from a line"""
        if len(line) != 2:
            return None
        x1, y1 = line[0]
        x2, y2 = line[1]
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        radius = math.hypot(x2 - x1, y2 - y1) / 2
        return (int(center_x), int(center_y), int(radius))

    def make_path(self):
        """Create a path from shape using standard variables"""
        if self.shape_type in ["polygon", "rectangle", "linestrip", "line"]:
            path = [tuple(p) for p in self.points]
        elif self.shape_type == "circle":
            if len(self.points) == 2:
                center_x, center_y, radius = self.get_circle_params_from_line(self.points)
                path = {"center": (center_x, center_y), "radius": radius}
            else:
                path = None  # Unable to define circle
        elif self.shape_type == "point":
            path = tuple(self.points[0])
        else:
            path = None  # Other shape types
        return path

    def contains_point(self, point, epsilon=1e-6):
        """Check if the shape contains a point"""
        path = self.make_path()
        if self.shape_type in ["polygon", "rectangle", "linestrip"]:
            return point_in_polygon(point, path)
        elif self.shape_type == "circle":
            if path is None:
                return False
            center = path["center"]
            radius = path["radius"]
            dx = point[0] - center[0]
            dy = point[1] - center[1]
            distance_squared = dx * dx + dy * dy
            return distance_squared <= radius * radius + epsilon
        elif self.shape_type == "line":
            if path is None:
                return False
            return point_near_line(point, path, epsilon=epsilon)
        elif self.shape_type == "point":
            shape_point = self.points[0]
            dx = point[0] - shape_point[0]
            dy = point[1] - shape_point[1]
            distance_squared = dx * dx + dy * dy
            return distance_squared <= epsilon ** 2
        else:
            return False

    def bounding_rect(self):
        """Return the bounding rectangle of the shape"""
        path = self.make_path()
        if self.shape_type == "circle":
            if path is None:
                return None
            center_x, center_y = path["center"]
            radius = path["radius"]
            left = center_x - radius
            right = center_x + radius
            top = center_y - radius
            bottom = center_y + radius
        elif self.shape_type in ["polygon", "rectangle", "linestrip", "line"]:
            if not path:
                return None
            xs = [p[0] for p in path]
            ys = [p[1] for p in path]
            left = min(xs)
            right = max(xs)
            top = min(ys)
            bottom = max(ys)
        elif self.shape_type == "point":
            x, y = path
            left = right = x
            top = bottom = y
        else:
            return None
        width = right - left
        height = bottom - top
        return (int(left), int(top), int(width), int(height))

    def move_by(self, offset):
        """Move all points by an offset"""
        dx, dy = offset
        self.points = [(p[0] + dx, p[1] + dy) for p in self.points]

    def move_vertex_by(self, i, offset):
        """Move a specific vertex by an offset"""
        dx, dy = offset
        x, y = self.points[i]
        self.points[i] = (x + dx, y + dy)

    def copy(self):
        """Create a deep copy of the shape"""
        return copy.deepcopy(self)

    def __len__(self):
        """Return the number of points in the shape"""
        return len(self.points)

    def __getitem__(self, key):
        """Get a point at a specific index"""
        return self.points[key]

    def __setitem__(self, key, value):
        """Set a point at a specific index"""
        self.points[key] = value

    def paint(self, image):
        """Paint shape onto the image using OpenCV"""
        if not self.visible or not self.points:
            return
        # Determine the color
        line_color = self.line_color
        fill_color = self.fill_color
        line_thickness = max(1, int(round(self.line_width)))

        # Convert points to integer tuples
        pts = [(int(p[0]), int(p[1])) for p in self.points]

        if self.shape_type == "rectangle":
            if len(pts) == 2:
                top_left = pts[0]
                bottom_right = pts[1]
                if self.fill:
                    cv2.rectangle(image, top_left, bottom_right, fill_color, -1)
                cv2.rectangle(image, top_left, bottom_right, line_color, line_thickness)
            elif len(pts) == 4:
                if self.fill:
                    cv2.fillPoly(image, [np.array(pts, dtype=np.int32)], fill_color)
                cv2.polylines(image, [np.array(pts, dtype=np.int32)], isClosed=True, color=line_color, thickness=line_thickness)
        elif self.shape_type == "rotation":
            if len(pts) == 4:
                if self.fill:
                    cv2.fillPoly(image, [np.array(pts, dtype=np.int32)], fill_color)
                cv2.polylines(image, [np.array(pts, dtype=np.int32)], isClosed=True, color=line_color, thickness=line_thickness)
        elif self.shape_type == "circle":
            if len(pts) == 2:
                center_x, center_y, radius = self.get_circle_params_from_line(pts)
                if self.fill:
                    cv2.circle(image, (center_x, center_y), radius, fill_color, -1)
                cv2.circle(image, (center_x, center_y), radius, line_color, line_thickness)
        elif self.shape_type == "linestrip":
            cv2.polylines(image, [np.array(pts, dtype=np.int32)], isClosed=False, color=line_color, thickness=line_thickness)
            if self.fill:
                cv2.fillPoly(image, [np.array(pts, dtype=np.int32)], fill_color)
        elif self.shape_type == "point":
            if pts:
                point_radius = max(1, int(round(self.point_size / 2)))
                cv2.circle(image, pts[0], point_radius, line_color, -1)
        else:  # Polygon or other shapes
            if self.fill:
                cv2.fillPoly(image, [np.array(pts, dtype=np.int32)], fill_color)
            cv2.polylines(image, [np.array(pts, dtype=np.int32)], isClosed=self.is_closed(), color=line_color, thickness=line_thickness)

    @staticmethod
    def wrap_color(color):
        """确保颜色是一个 RGBA 四元组"""
        if isinstance(color, str) and color.startswith('#'):
            # 将十六进制颜色字符串转换为 (R, G, B, A)
            color = color.lstrip('#')
            r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
            return (r, g, b, 255)  # 设为不透明
        elif isinstance(color, (tuple, list)) and len(color) == 4:
            return tuple(color)
        elif isinstance(color, (tuple, list)) and len(color) == 3:
            return tuple(color) + (255,)  # 默认为不透明
        else:
            raise ValueError("Unsupported color format. Please use a hex string or a tuple/list of RGB/RGBA values.")