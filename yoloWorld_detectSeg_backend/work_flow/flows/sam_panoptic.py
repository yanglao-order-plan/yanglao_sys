import os
import random
import sys
import traceback
import logging

import numpy as np
import cv2
from torch.nn.functional import threshold_

from work_flow.utils.box import box_iou
from . import __preferred_device__, Model, Shape, AutoLabelingResult
from .setr_mla import SETR_MLA
from .unidet import UniDet
from ..__base__.clip import ChineseClipONNX
from ..utils.segment_anything import sam_model_registry, SamAutomaticMaskGenerator

sys.path.append('.')
sys.path.append('./UNIDET/detectron2')


def random_color():
    r = random.randint(120, 255)
    g = random.randint(120, 255)
    b = random.randint(120, 255)
    return [b, g, r]




class SAM_Panoptic(Model):
    """Segmentation model using SegmentAnything"""
    num_class = 104
    area_thr = 0
    ratio_thr = 0.5
    top_k = 80
    thresholds = [0.5, 0.6]
    category_txt = "E:\GitHub\yanglao_sys\yoloWorld_detectSeg_backend\work_flow\configs\SER_MLA/foodseg103_category_id.txt"
    class Meta:
        required_config_names = [
            "type",
            "name",
            "display_name",
            "model_path",
        ]
        widgets = [
            "edit_conf",
        ]
        output_modes = {
            "polygon": "Polygon",
            "rectangle": "Rectangle",
            "rotation": "Rotation",
        }
        default_output_mode = "polygon"

    def __init__(self, config_path, on_message) -> None:
        # Run the parent class's init method
        super().__init__(config_path, on_message)

        # Get encoder and decoder model paths
        model_abs_path = self.get_model_abs_path(
            self.config, "model_path"
        )
        if not model_abs_path or not os.path.isfile(
                model_abs_path
        ):
            raise FileNotFoundError(
                "Could not download or initialize encoder of Unidet."
            )

        with open(self.category_txt, 'r') as f:
            category_lines = f.readlines()
            self.category_list = [' '.join(line_data.split('\t')[1:]).strip() for line_data in category_lines]
            f.close()

        # sam enhance
        self.enhance_mask = self.config.get("enhance_mask", None)
        model_type = self.config.get("model_type", None)
        sam_model_abs_path = self.get_model_abs_path(
            self.config, "sam_model_path"
        )
        sam = sam_model_registry[model_type](checkpoint=sam_model_abs_path)
        self.sam = SamAutomaticMaskGenerator(sam, output_mode='binary_mask')

        # unidet background
        self.unidet = UniDet(self.config, on_message)

        # setr_mla semantic
        self.setr_mla = SETR_MLA(self.config, on_message)


    def post_process(self, category_info, shape):
        """
        Post process masks
        输入: 每个蒙版的范围、类别、颜色
        """
        # Find contours
        approx_contours, masks, cls_names, colors = [], [], [], []
        for info in category_info:
            mask = info[5]["segmentation"]
            cls_names.append(info[2])
            colors.append(info[5]['color'])
            masks.append(mask)
            mask *= 255 # binary mask
            mask = mask.astype(np.uint8)
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
            )
            max_contour = max(contours, key=cv2.contourArea)
            # Refine contours 对每个mask直接最大外接
            epsilon = 0.001 * cv2.arcLength(max_contour, True)
            approx = cv2.approxPolyDP(max_contour, epsilon, True)
            approx_contours.append(approx)

        # Remove too big contours ( >90% of image size)
        if len(approx_contours) > 1:
            image_size = shape[0] * shape[1]
            areas = [cv2.contourArea(contour) for contour in approx_contours]
            avg_area = np.mean(areas)
            filtered_approx_contours, filtered_classes, filtered_colors = [], [], []
            for contour, area, cls_name, color in zip(approx_contours, areas, cls_names, colors):
                if area < image_size * 0.9 or area > avg_area * 0.2:
                    filtered_approx_contours.append(contour)
                    filtered_classes.append(cls_name)
                    filtered_colors.append(color)

            approx_contours = filtered_approx_contours
            classes = filtered_classes
            colors = filtered_colors
        # Contours to shapes
        shapes = []
        if self.output_mode == "polygon":
            for i, (approx, cls_name, color) in enumerate(zip(approx_contours, cls_names, colors)):
                # Scale points
                points = approx.reshape(-1, 2)
                points[:, 0] = points[:, 0]
                points[:, 1] = points[:, 1]
                points = points.tolist()
                if len(points) < 3:
                    continue
                points.append(points[0])
                # Create shape
                shape = Shape(flags={})
                for point in points:
                    point[0] = int(point[0])
                    point[1] = int(point[1])
                    shape.add_point(point[0], point[1])
                shape.shape_type = "polygon"
                shape.closed = True
                shape.fill_color = color
                shape.line_color = color
                shape.line_width = 1
                shape.label = cls_name
                shape.selected = False
                shapes.append(shape)
        elif self.output_mode in ["rectangle", "rotation"]:
            for i, (approx, cls_name, color) in enumerate(zip(approx_contours, cls_names, colors)):
                x_min = 100000000
                y_min = 100000000
                x_max = 0
                y_max = 0
                # Scale points
                points = approx.reshape(-1, 2)
                points[:, 0] = points[:, 0]
                points[:, 1] = points[:, 1]
                points = points.tolist()
                if len(points) < 3:
                    continue
                # Create shape
                shape = Shape(flags={})
                for point in points:
                    x_min = min(x_min, point[0])
                    y_min = min(y_min, point[1])
                    x_max = max(x_max, point[0])
                    y_max = max(y_max, point[1])
                    point[0] = int(point[0])
                    point[1] = int(point[1])
                    shape.add_point(point[0], point[1])
                shape.shape_type = (
                    "rectangle" if self.output_mode == "rectangle" else "rotation"
                )
                shape.closed = True
                shape.fill_color = color
                shape.line_color = color
                shape.line_width = 1
                shape.label = cls_name
                shape.selected = False
                shapes.append(shape)

        return shapes

    # 语义增强
    def enhance_masks(self, seg, image):
        data = self.sam.generate(image)
        pred_mask_img = seg[:, :, -1]  # red channel
        enhanced_mask = seg[:, :, 2]  # full channel
        shape_size = pred_mask_img.shape[0] * pred_mask_img.shape[1]
        category_info = []
        for idx, meta in enumerate(data):  # 针对语义分割mask，利用sam mask的聚类结果统一局部像素
            sam_mask = meta["segmentation"]
            single_mask_labels = pred_mask_img[sam_mask]  # 像素计数
            unique_values, counts = np.unique(single_mask_labels, return_counts=True, axis=0)
            max_idx = np.argmax(counts)  # 语义像素id+sam像素轮廓
            cls_idx = unique_values[max_idx]
            count_ratio = counts[max_idx] / counts.sum()  # 增强比例（当前最多像素，其数量的百分比）
            cls_name = self.category_list[cls_idx]  # 已经增强语义了啊
            shape_per = counts.sum() / shape_size
            category_info.append((idx, cls_idx, cls_name, count_ratio, shape_per, meta))
        category_info = sorted(category_info, key=lambda x: float(x.split(',')[4]), reverse=True)
        category_info = category_info[:self.top_k]

        _category_info = category_info.copy()
        for info in category_info:  # 忽略无意义的class_id
            idx, label, count_ratio, area = info[0], int(info[1]), float(
                info[3]), float(info[4])
            if area < self.area_thr or count_ratio < self.ratio_thr:  # 过滤1: 区域阈值
                _category_info.remove(info)
                continue
            sam_mask = data[int(idx)]["segmentation"].astype(bool)  # enhance依据知识源划分（有监督分类）
            assert (sam_mask.sum() / (sam_mask.shape[0] * sam_mask.shape[1]) - area) < 1e-4
            enhanced_mask[sam_mask] = label  # 像素范畴增强（背景为白色）

        return enhanced_mask, _category_info

    # 实例增强
    def enhance_instance(self, category_info, shape):
        enhanced_mask = np.zeros((*shape, 3))
        boxes, info = [], []
        color_list = self.setr_mla.color_list.copy()
        color_list2 = color_list[::-1]
        color_list[0] = [238, 239, 20]
        _category_info = category_info.copy()
        for info in category_info:
            idx, label, count_ratio, area, meta = info[0], int(info[1]), float(
                info[3]), float(info[4]), info[5]
            sam_mask = meta["segmentation"].astype(bool)
            if label == 0:  # 过滤2-无效类别
                _category_info.remove(info)
                continue
            elif label < self.num_class:  # 控制mask颜色，区分实例
                color = random_color()  # 这里只记录颜色，没必要做纯色图像
            else:
                color = color_list[label]
            enhanced_mask[sam_mask] = color
            info[5]['color'] = color
            name = info[2]
            boxes.append(meta["bbox"])
            info.append((label, name))

        boxes_np = np.array(boxes)
        font = cv2.FONT_HERSHEY_SIMPLEX
        enhanced_mask = enhanced_mask.astype(np.uint8)
        for id, coord in enumerate(boxes_np):
            x0, y0, w, h = coord[:4]
            label = info[id][0]
            pt1 = (int(x0), int(y0))
            pt2 = (int(x0 + w), int(y0 + h))
            color = color_list[int(label)].tolist()
            if label > self.num_class - 1:
                color = color_list2[int(label)].tolist()
            cv2.rectangle(enhanced_mask, pt1, pt2, color, 2)
            x, y = pt1
            category_name = info[id][1]
            cv2.putText(enhanced_mask, category_name, (x + 3, y + 10), font, 0.35, color, 1)

        return enhanced_mask, _category_info

    # 全景增强
    def enhance_panoramic(self, category_info, det_info, shape):
        for threshold in self.thresholds:
            for info in category_info[threshold]:  #
                if info['category_name'] == 'background':
                    meta_data = info[5]
                    best_iou = 0.0
                    index = -1  # xywh -> xyxy
                    box = [float(meta_data['bbox_x0']), float(meta_data['bbox_y0']),
                           float(meta_data['bbox_x0']) + float(meta_data['bbox_w']),
                           float(meta_data['bbox_y0']) + float(meta_data['bbox_h'])]
                    for i, item in enumerate(det_info):  # 分析重合度
                        temp = box_iou(box, item['bounding_box'])
                        if temp >= best_iou:
                            index = i
                            best_iou = temp
                    if best_iou >= threshold: # 遍历时修改
                        info['category_name'] = det_info[index]['category_name']
                        info['category_id'] = str(int(det_info[index]['category_id']) + 104)
        # 全景增强后，直接获取实例分割结果
        return self.enhance_instance(category_info[self.thresholds[-1]], shape)


    def predict_shapes(self, image, filename=None) -> AutoLabelingResult:
        """
        Predict shapes from image
        """
        if image is None:
            return AutoLabelingResult([], replace=False)
        try:
            avatars = []
            seg = self.setr_mla.predict_raw(image)
            _, _, _, seg_avatars = self.setr_mla.color_mask(image, seg)
            enhance_semantic, category_info = self.enhance_masks(seg, image)
            mask_shape = enhance_semantic.shape[:2]
            enhance_instance, category_info = self.enhance_instance(category_info, mask_shape)
            det_data, enhance_det = self.unidet.predict_shapes(image, raw=True)
            enhance_panoptic, category_info = self.enhance_panoramic(category_info, det_data, mask_shape)
            avatars.extend(seg_avatars)
            avatars.extend([enhance_semantic, enhance_det, enhance_instance, enhance_panoptic])
            shapes = self.post_process(category_info, mask_shape)

        except Exception as e:  # noqa
            logging.warning("Could not inference model")
            logging.error(e)
            traceback.print_exc()
            return AutoLabelingResult([], replace=False)

        return AutoLabelingResult(shapes, replace=False, avatars=avatars)