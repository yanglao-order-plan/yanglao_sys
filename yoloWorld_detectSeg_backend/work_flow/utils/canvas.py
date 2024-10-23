import imgviz
import math
import copy
import numpy as np
import cv2

from .shape import Shape  # 假设已调整为使用 OpenCV 的 Shape 类

LABEL_COLORMAP = imgviz.label_colormap()

class Canvas:
    """Canvas 类，用于管理形状并在图像上绘制。"""

    def __init__(self):
        self.shapes = []
        self.shapes_backups = []
        self.current = None
        self.selected_shapes = []
        self.scale = 1.0
        self.image = None  # 这是一个 NumPy 数组，表示加载的图像
        self.visible = {}
        self._fill_drawing = False
        self._hide_background = False
        self.show_groups = False
        self.show_texts = True
        self.show_labels = True
        self.show_scores = True
        self.show_degrees = False
        self.show_linking = True

        # 其他必要的属性

    def set_fill_drawing(self, value):
        """设置形状填充选项。"""
        self._fill_drawing = value

    def load_image(self, image):
        """加载图像（NumPy 数组）。"""
        self.image = image.copy()
        self.shapes = []
        self.update()

    def load_shapes(self, shapes, replace=True):
        """加载形状。"""
        if replace:
            self.shapes = list(shapes)
        else:
            self.shapes.extend(shapes)
        self.store_shapes()
        self.current = None
        self.update()

    def update(self, replace=False):
        """更新 Canvas（占位方法）。"""

        pass  # 在静态绘图的情况下，这里可以留空，或用于触发重新绘制。

    def store_shapes(self):
        """存储形状以便稍后恢复（撤销功能）。"""
        # 实现需要的逻辑
        pass

    def is_visible(self, shape):
        """检查形状是否可见。"""
        return self.visible.get(shape, True)

    def draw(self):
        """在图像上绘制形状并返回绘制结果。"""
        if self.image is None:
            return None

        # 创建图像的副本以进行绘制
        image = self.image.copy()

        # 绘制形状
        for shape in self.shapes:
            print(shape.label, shape.description)
            if self.is_visible(shape):
                shape.fill = self._fill_drawing
                shape.paint(image)

        # 绘制组
        if self.show_groups:
            grouped_shapes = {}
            for shape in self.shapes:
                if shape.group_id is not None:
                    grouped_shapes.setdefault(shape.group_id, []).append(shape)
            for group_id, shapes in grouped_shapes.items():
                # 计算组的边界框
                xs = []
                ys = []
                for shape in shapes:
                    bbox = shape.bounding_rect()
                    x, y, w, h = bbox
                    xs.extend([x, x + w])
                    ys.extend([y, y + h])
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                group_color = LABEL_COLORMAP[int(group_id) % len(LABEL_COLORMAP)]
                group_color = tuple(int(c) for c in group_color)
                # 绘制组的矩形框
                cv2.rectangle(
                    image,
                    (int(min_x), int(min_y)),
                    (int(max_x), int(max_y)),
                    group_color,
                    2,
                )
                # 可选地，在组的中心绘制组 ID
                center_x = int((min_x + max_x) / 2)
                center_y = int((min_y + max_y) / 2)
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                font_thickness = 1
                text = f"Group {group_id}"
                text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
                text_w, text_h = text_size
                text_x = center_x - text_w // 2
                text_y = center_y + text_h // 2
                cv2.putText(
                    image,
                    text,
                    (text_x, text_y),
                    font,
                    font_scale,
                    (255, 255, 255),
                    font_thickness,
                    cv2.LINE_AA,
                )

        # 绘制 KIE 链接
        if self.show_linking:
            gid2point = {}
            linking_pairs = []
            group_color = (255, 128, 0)  # 橙色
            for shape in self.shapes:
                if hasattr(shape, 'kie_linking') and shape.kie_linking:
                    linking_pairs.extend(shape.kie_linking)
                if shape.group_id is not None and shape.shape_type in [
                    "rectangle",
                    "polygon",
                    "rotation",
                ]:
                    bbox = shape.bounding_rect()
                    x, y, w, h = bbox
                    cx = x + w / 2
                    cy = y + h / 2
                    gid2point[shape.group_id] = (int(cx), int(cy))
            for key, value in linking_pairs:
                if key not in gid2point or value not in gid2point:
                    continue
                kp = gid2point[key]
                vp = gid2point[value]
                # 绘制从 kp 到 vp 的线
                cv2.line(image, kp, vp, group_color, 2)
                # 绘制箭头
                arrow_size = 10  # 箭头大小
                angle = math.atan2(vp[1] - kp[1], vp[0] - kp[0])  # 角度
                arrow_tip = vp
                arrow_left = (
                    int(vp[0] - arrow_size * math.cos(angle - math.pi / 6)),
                    int(vp[1] - arrow_size * math.sin(angle - math.pi / 6)),
                )
                arrow_right = (
                    int(vp[0] - arrow_size * math.cos(angle + math.pi / 6)),
                    int(vp[1] - arrow_size * math.sin(angle + math.pi / 6)),
                )
                cv2.line(image, arrow_tip, arrow_left, group_color, 2)
                cv2.line(image, arrow_tip, arrow_right, group_color, 2)

        # 绘制角度
        if self.show_degrees:
            for shape in self.shapes:
                if shape.shape_type == "rotation" and len(shape.points) == 4:
                    # 计算中心点
                    x1, y1 = shape.points[0]
                    x3, y3 = shape.points[2]
                    center_x = (x1 + x3) / 2
                    center_y = (y1 + y3) / 2
                    # 获取角度
                    degrees = int(math.degrees(shape.direction)) % 360
                    # 绘制文本
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.5
                    font_thickness = 1
                    text = f"{degrees}°"
                    text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
                    text_w, text_h = text_size
                    text_x = int(center_x - text_w / 2)
                    text_y = int(center_y + text_h / 2)
                    # 绘制背景矩形
                    cv2.rectangle(
                        image,
                        (text_x, text_y - text_h),
                        (text_x + text_w, text_y),
                        (0, 165, 255),  # 橙色背景
                        -1,
                    )
                    # 绘制文本
                    cv2.putText(
                        image,
                        text,
                        (text_x, text_y),
                        font,
                        font_scale,
                        (255, 255, 255),  # 白色文本
                        font_thickness,
                        cv2.LINE_AA,
                    )

        # 绘制描述文本
        if self.show_texts:
            for shape in self.shapes:
                if shape.description:
                    bbox = shape.bounding_rect()
                    x, y, w, h = bbox
                    text_x = int(x)
                    text_y = int(y) - 5  # 根据需要调整
                    text = shape.description
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.5
                    font_thickness = 1
                    text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
                    text_w, text_h = text_size
                    # 绘制背景矩形
                    cv2.rectangle(
                        image,
                        (text_x, text_y - text_h),
                        (text_x + text_w, text_y),
                        (0, 123, 255),  # 深蓝色背景
                        -1,
                    )
                    # 绘制文本
                    cv2.putText(
                        image,
                        text,
                        (text_x, text_y),
                        font,
                        font_scale,
                        (255, 255, 255),  # 白色文本
                        font_thickness,
                        cv2.LINE_AA,
                    )

        # 绘制标签
        if self.show_labels:
            for shape in self.shapes:
                if not shape.visible:
                    continue
                label_text = shape.label or ""
                if shape.group_id is not None:
                    label_text = f"id:{shape.group_id} {label_text}"
                if shape.score is not None and self.show_scores:
                    label_text += f" {float(shape.score):.2f}"
                if not label_text:
                    continue
                # 获取绘制标签的位置
                if shape.shape_type in ["rectangle", "polygon", "rotation"]:
                    bbox = shape.bounding_rect()
                    x, y, w, h = bbox
                    text_x = int(x)
                    text_y = int(y) - 5  # 根据需要调整
                elif shape.shape_type in ["circle", "line", "linestrip", "point"]:
                    point = shape.points[0]
                    text_x = int(point[0])
                    text_y = int(point[1]) - 5  # 根据需要调整
                else:
                    continue
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                font_thickness = 1
                text_size, _ = cv2.getTextSize(label_text, font, font_scale, font_thickness)
                text_w, text_h = text_size
                # 绘制背景矩形
                cv2.rectangle(
                    image,
                    (text_x, text_y - text_h),
                    (text_x + text_w, text_y),
                    shape.line_color,  # 使用形状的线条颜色作为背景
                    -1,
                )
                # 绘制文本
                cv2.putText(
                    image,
                    label_text,
                    (text_x, text_y),
                    font,
                    font_scale,
                    (255, 255, 255),  # 白色文本
                    font_thickness,
                    cv2.LINE_AA,
                )

        return image

    # 根据需要添加管理形状的方法

    def set_shape_visible(self, shape, value):
        """设置形状的可见性。"""
        self.visible[shape] = value
        self.update()

    def reset_state(self):
        """清除形状和图像。"""
        self.image = None
        self.shapes_backups = []
        self.update()

    def _update_shape_color(self, shape):
        """更新形状颜色，适用于 OpenCV 图像处理"""
        r, g, b = self._get_rgb_by_label(shape.label)

        # OpenCV 使用 BGR 顺序，填充和线条颜色使用整数元组
        shape.line_color = (b, g, r)  # 边界线的颜色
        shape.fill_color = (b, g, r, 128)  # 填充颜色，注意这里保持透明度信息

        # 可选颜色属性更新（不再使用 QtGui.QColor）
        shape.vertex_fill_color = (b, g, r)  # 顶点颜色
        shape.hvertex_fill_color = (255, 255, 255)  # 高亮顶点颜色
        shape.select_line_color = (255, 255, 255)  # 选择形状的边框颜色
        shape.select_fill_color = (b, g, r, 155)  # 选择形状的填充颜色（包含透明度）

    def _get_rgb_by_label(self, label, skip_label_info=False):
        """根据标签获取 RGB 颜色，用于 OpenCV 图像处理"""
        if label in self.label_info and not skip_label_info:
            return tuple(self.label_info[label]["color"])

        if self._config["shape_color"] == "auto":
            # 在唯一标签列表中查找或添加标签以获取对应颜色
            if not self.unique_label_list.find_items_by_label(label):
                item = self.unique_label_list.create_item_from_label(label)
                self.unique_label_list.addItem(item)
            item = self.unique_label_list.find_items_by_label(label)[0]
            label_id = self.unique_label_list.indexFromItem(item).row() + 1
            label_id += self._config["shift_auto_shape_color"]
            return LABEL_COLORMAP[label_id % len(LABEL_COLORMAP)]

        if (
                self._config["shape_color"] == "manual"
                and self._config["label_colors"]
                and label in self._config["label_colors"]
        ):
            return self._config["label_colors"][label]

        if self._config["default_shape_color"]:
            return self._config["default_shape_color"]

        return (0, 255, 0)  # 默认颜色：绿色