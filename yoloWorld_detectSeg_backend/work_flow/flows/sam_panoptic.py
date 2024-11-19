import os
import random
import sys
import traceback
import logging
from typing import List, Dict, Any

import mmcv
import numpy as np
import cv2

from work_flow.utils.box import box_iou, get_IoU
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
        approx_contours, masks, cls_names, colors, scores = [], [], [], [], []
        for info in category_info:
            mask = info[5]["segmentation"]
            cls_names.append(info[2])
            colors.append(info[5]['color'])
            scores.append(info[3])
            masks.append(mask)
            mask = mask.astype(np.uint8)  # 将布尔类型转换为 uint8 (0 和 1)
            mask *= 255  # 转换为 0 和 255
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
            filtered_approx_contours, filtered_classes, filtered_colors, filtered_scores = [], [], [], []
            for contour, area, cls_name, color, score in zip(approx_contours, areas, cls_names, colors, scores):
                if area < image_size * 0.9 or area > avg_area * 0.2:
                    filtered_approx_contours.append(contour)
                    filtered_classes.append(cls_name)
                    filtered_colors.append(color)
                    filtered_scores.append(score)

            approx_contours = filtered_approx_contours
            cls_names = filtered_classes
            colors = filtered_colors
            scores = filtered_scores
        # Contours to shapes
        shapes = []
        for i, (approx, cls_name, color, score) in enumerate(zip(approx_contours, cls_names, colors, scores)):
                # Scale points
            if self.output_mode == "polygon":
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
            elif self.output_mode in ["rectangle", "rotation"]:
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
            else:
                raise ValueError(f"Invalid output mode: {self.output_mode}")
            shape.closed = True
            shape.fill_color = color
            shape.line_color = color
            shape.line_width = 1
            shape.label = cls_name
            shape.score = float(score)
            shape.selected = False
            shapes.append(shape)

        return shapes

    @staticmethod
    def write_masks_to_folder(masks: List[Dict[str, Any]]) -> None:
        path = 'output'
        header = "id,area,bbox_x0,bbox_y0,bbox_w,bbox_h,point_input_x,point_input_y,predicted_iou,stability_score,crop_box_x0,crop_box_y0,crop_box_w,crop_box_h"  # noqa
        metadata = [header]
        os.makedirs(os.path.join(path, "sam_mask"), exist_ok=True)
        masks_array = []
        for i, mask_data in enumerate(masks):
            mask = mask_data["segmentation"]
            masks_array.append(mask.copy())
            filename = f"{i}.png"
            cv2.imwrite(os.path.join(path, "sam_mask", filename), mask * 255)
            mask_metadata = [
                str(i),
                str(mask_data["area"]),
                *[str(x) for x in mask_data["bbox"]],
                *[str(x) for x in mask_data["point_coords"][0]],
                str(mask_data["predicted_iou"]),
                str(mask_data["stability_score"]),
                *[str(x) for x in mask_data["crop_box"]],
            ]
            row = ",".join(mask_metadata)
            metadata.append(row)

        masks_array = np.stack(masks_array, axis=0)
        np.save(os.path.join(path, "sam_mask", "masks.npy"), masks_array)
        metadata_path = os.path.join(path, "sam_metadata.csv")
        with open(metadata_path, "w") as f:
            f.write("\n".join(metadata))
        return

    # 语义增强
    def enhance_masks(self, seg, image):
        self.sam.predictor.model.to(__preferred_device__)  # 必须通道转换
        data = self.sam.generate(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        # self.write_masks_to_folder(data)
        self.sam.predictor.model.to('cpu')

        enhanced_mask = seg.copy()  # full channel
        shape_size = enhanced_mask.shape[0] * enhanced_mask.shape[1]
        category_info = []
        for idx, meta in enumerate(data):  # 针对语义分割mask，利用sam mask的聚类结果统一局部像素
            sam_mask = meta["segmentation"]
            single_mask_labels = enhanced_mask[sam_mask]  # 像素计数
            unique_values, counts = np.unique(single_mask_labels, return_counts=True, axis=0)
            max_idx = np.argmax(counts)  # 语义像素id+sam像素轮廓
            cls_idx = unique_values[max_idx]
            count_ratio = counts[max_idx] / counts.sum()  # 增强比例（当前最多像素，其数量的百分比）
            cls_name = self.category_list[cls_idx]  # 已经增强语义了啊
            shape_per = counts.sum() / shape_size
            category_info.append([idx, cls_idx, cls_name, count_ratio, shape_per, meta])
            # 单独mask的类别置信度为[3] mask在整体的iou可信度为[4]
        category_info = sorted(category_info, key=lambda x: float(x[4]), reverse=True)
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
            if label == 0:  # 过滤2-背景过滤
                _category_info.remove(info)
                continue
            elif label < self.num_class:  # 控制mask颜色，区分实例
                color = random_color()  # 随机颜色
            else:
                color = color_list[label]
            enhanced_mask[sam_mask] = color
            info[5]['color'] = color
            boxes.append(meta["bbox"])

        font = cv2.FONT_HERSHEY_SIMPLEX
        enhanced_mask = enhanced_mask.astype(np.uint8)
        for info in _category_info:
            idx, label, category_name, count_ratio, area, meta = (info[0], int(info[1]), str(info[2]),
                                                                  float(info[3]), float(info[4]), info[5])
            x0, y0, w, h = meta["bbox"]
            pt1 = (int(x0), int(y0))
            pt2 = (int(x0 + w), int(y0 + h))
            color = color_list[int(label)].tolist()
            if label > self.num_class - 1:
                color = color_list2[int(label)].tolist()
            cv2.rectangle(enhanced_mask, pt1, pt2, color, 2)
            x, y = pt1
            cv2.putText(enhanced_mask, category_name, (x + 3, y + 10), font, 0.35, color, 1)

        return enhanced_mask, _category_info

    # 全景增强
    def enhance_panoramic(self, category_info, det_info, shape):
        # for threshold in self.thresholds:
        for info in category_info:  #
            if info[2] == 'background':
                meta_data = info[5]
                best_iou = 0.0
                index = -1  # xywh -> xyxy
                bbox_x0, bbox_y0, bbox_w, bbox_h = meta_data["bbox"]
                box = [float(bbox_x0), float(bbox_y0),
                       float(bbox_x0) + float(bbox_w),
                       float(bbox_y0) + float(bbox_h)]
                for i, item in enumerate(det_info):  # 分析重合度
                    temp = get_IoU(box, item['bounding_box'])
                    if temp >= best_iou:
                        index = i
                        best_iou = temp
                if best_iou >= self.thresholds[0]: # 遍历时修改
                    info[2] = det_info[index]['category_name']  # 绘图应该避免label==0
                    info[1] = str(int(det_info[index]['category_id']) + 104)
        # 全景增强后，直接获取实例分割结果
        return self.enhance_instance(category_info, shape)

    def color_mask(self, image, mask):
        values = set(mask.flatten().tolist())
        final_masks = []
        for v in values:  # 拆分标签
            final_masks.append((mask[:, :] == v, v))
        np.random.seed(42)
        if len(final_masks) == 0:
            return
        h, w = final_masks[0][0].shape[:2]
        result = np.zeros((h, w, 3), dtype=np.uint8)
        for m, label in final_masks:
            result[m, :] = self.setr_mla.color_list[label]
        vis = cv2.addWeighted(image, 0.5, result, 0.5, 0)
        # mmcv.imwrite(mask, 'output/enhance_mask.png')
        # mmcv.imwrite(vis, 'output/enhance_vis.png')
        return vis

    def predict_shapes(self, image, filename=None) -> AutoLabelingResult:
        """
        Predict shapes from image
        """
        if image is None:
            return AutoLabelingResult([], replace=False)
        try:
            avatars = []
            pred_mask = self.setr_mla.predict_raw(image)
            _, _, _, pred_vis = self.setr_mla.color_mask(image, pred_mask)
            enhance_mask, category_info = self.enhance_masks(pred_mask, image)
            enhance_vis = self.color_mask(image, enhance_mask)
            mask_shape = enhance_mask.shape[:2]
            instance_vis, _ = self.enhance_instance(category_info, mask_shape)
            det_data, detection_vis = self.unidet.predict_shapes(image, raw=True)
            # mmcv.imwrite(detection_vis, 'output/detection_vis.png')
            panoramic_vis, category_info = self.enhance_panoramic(category_info, det_data, mask_shape)
            # mmcv.imwrite(panoramic_vis, 'output/panoramic_vis.png')
            avatars.extend([pred_mask, pred_vis, enhance_mask, enhance_vis, detection_vis, instance_vis, panoramic_vis])
            shapes = self.post_process(category_info, mask_shape)

        except Exception as e:  # noqa
            logging.warning("Could not inference model")
            logging.error(e)
            traceback.print_exc()
            return AutoLabelingResult([], replace=False)

        return AutoLabelingResult(shapes, replace=False, avatars=avatars)