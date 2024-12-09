import logging
import re

import cv2
import traceback
import numpy as np
from . import Model, AutoLabelingResult
from .lama import Lama
from .ppocr_v4 import PPOCRv4


class PPOCRv4LAMA(Model):
    """Open-Set instance segmentation model using GroundingSAM"""
    PIXEL_TOLERANCE_Y = 20  # 允许检测框纵向偏差的像素点数
    PIXEL_TOLERANCE_X = 20  # 允许检测框横向偏差的像素点数
    SUBTITLE_AREA_DEVIATION_PIXEL = 20
    # 用于放大mask大小，防止自动检测的文本框过小，inpaint阶段出现文字边，有残留

    def __init__(self, model_config, on_message) -> None:
        # Run the parent class's init method
        print(model_config)
        super().__init__(model_config, on_message)

        # ----------- PPOCRV4 ---------- #
        self.sub_detector = PPOCRv4(model_config, on_message)
        # ----------- LAMA ---------- #
        self.lama_inpaint = Lama(model_config, on_message)
        # self.mask_enhance = self.config.get("mask_enhance", False)


    def create_mask(self, size, coords_list, mask_enhance=False):
        mask = np.zeros(size, dtype="uint8")
        if coords_list:
            for coords in coords_list:
                xmin, xmax, ymin, ymax = coords
                # 为了避免框过小，放大10个像素
                x1 = xmin - self.SUBTITLE_AREA_DEVIATION_PIXEL
                if x1 < 0:
                    x1 = 0
                y1 = ymin - self.SUBTITLE_AREA_DEVIATION_PIXEL
                if y1 < 0:
                    y1 = 0
                x2 = xmax + self.SUBTITLE_AREA_DEVIATION_PIXEL
                y2 = ymax + self.SUBTITLE_AREA_DEVIATION_PIXEL
                cv2.rectangle(mask, (x1, y1),
                              (x2, y2), (255, 255, 255), thickness=-1)
        # if mask_enhance:
        #     if size[1] <= 720:
        return mask

    @staticmethod
    def get_coordinates(dt_box):
        """
        从返回的检测框中获取坐标
        :param dt_box 检测框返回结果
        :return list 坐标点列表
        """
        coordinate_list = list()
        if isinstance(dt_box, list):
            for i in dt_box:
                i = list(i)
                (x1, y1) = int(i[0][0]), int(i[0][1])
                (x2, y2) = int(i[1][0]), int(i[1][1])
                (x3, y3) = int(i[2][0]), int(i[2][1])
                (x4, y4) = int(i[3][0]), int(i[3][1])
                xmin = max(x1, x4)
                xmax = min(x2, x3)
                ymin = max(y1, y2)
                ymax = min(y3, y4)
                coordinate_list.append((xmin, xmax, ymin, ymax))
        return coordinate_list

    def are_similar(self, region1, region2):
        """判断两个区域是否相似。"""
        xmin1, xmax1, ymin1, ymax1 = region1
        xmin2, xmax2, ymin2, ymax2 = region2

        return abs(xmin1 - xmin2) <= self.PIXEL_TOLERANCE_X and abs(xmax1 - xmax2) <= self.PIXEL_TOLERANCE_X and \
            abs(ymin1 - ymin2) <= self.PIXEL_TOLERANCE_Y and abs(ymax1 - ymax2) <= self.PIXEL_TOLERANCE_Y

    def unify_regions(self, raw_regions):
        """将连续相似的区域统一，保持列表结构。"""
        if len(raw_regions) > 0:
            keys = sorted(raw_regions.keys())  # 对键进行排序以确保它们是连续的
            unified_regions = {}

            # 初始化
            last_key = keys[0]
            unify_value_map = {last_key: raw_regions[last_key]}

            for key in keys[1:]:
                current_regions = raw_regions[key]

                # 新增一个列表来存放匹配过的标准区间
                new_unify_values = []

                for idx, region in enumerate(current_regions):
                    last_standard_region = unify_value_map[last_key][idx] if idx < len(unify_value_map[last_key]) else None

                    # 如果当前的区间与前一个键的对应区间相似，我们统一它们
                    if last_standard_region and self.are_similar(region, last_standard_region):
                        new_unify_values.append(last_standard_region)
                    else:
                        new_unify_values.append(region)

                # 更新unify_value_map为最新的区间值
                unify_value_map[key] = new_unify_values
                last_key = key

            # 将最终统一后的结果传递给unified_regions
            for key in keys:
                unified_regions[key] = unify_value_map[key]
            return unified_regions
        else:
            return raw_regions

    def find_subtitle_frame_no(self, dt_boxes):
        # ----------- finding subtitles ---------- #
        subtitle_frame_no_box_dict = {}
        logging.info('[Processing] start finding subtitles...')
        coordinate_list = self.get_coordinates(dt_boxes)
        if coordinate_list:
            temp_list = []
            for coordinate in coordinate_list:
                xmin, xmax, ymin, ymax = coordinate
                temp_list.append((xmin, xmax, ymin, ymax))
            if len(temp_list) > 0:
                subtitle_frame_no_box_dict[1] = temp_list

        subtitle_frame_no_box_dict = self.unify_regions(subtitle_frame_no_box_dict)
        logging.info('[Finished] Finished finding subtitles...')
        new_subtitle_frame_no_box_dict = dict()
        for key in subtitle_frame_no_box_dict.keys():
            if len(subtitle_frame_no_box_dict[key]) > 0:
                new_subtitle_frame_no_box_dict[key] = subtitle_frame_no_box_dict[key]
        return new_subtitle_frame_no_box_dict

    def format_letter(self, letters):
        return "\n".join(letters) # 形成表单

    def mask_enhance(self, size, mask):
        mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=1)
        mask = cv2.erode(mask, np.ones((5, 5), np.uint8), iterations=1)

    def pack_results(self, dt_boxes, rec_res, scores, image):
        results = self.sub_detector.pack_results(dt_boxes, rec_res, scores)
        for shape in results.shapes:
            shape.visible = False
        results.image = image
        results.description = self.format_letter([res[0] for res in rec_res])
        results.visible = False
        return results

    def predict_shapes(self, image, image_path=None, mask_enhance=False, formats=[]):
        """
        Predict shapes from image
        """
        if image is None:
            return []
        try:
            image = image.copy()
            dt_boxes, rec_res, scores = self.sub_detector.text_sys(image)
            letters = [res[0] for res in rec_res]
            for id, letter in enumerate(letters):
                for format in formats:
                    if re.match(format, letter): # 排除清除字符串
                        dt_boxes.pop(id)
            sub_list = self.find_subtitle_frame_no(dt_boxes)
            logging.info('[Processing] Start removing subtitles...')
            if len(sub_list):
                mask = self.create_mask(image.shape[0:2], sub_list[1], mask_enhance)
                results = self.lama_inpaint.predict_shapes(image, mask)
                image = results.image
            logging.info('[Finished] Finished removing subtitles...')
            return self.pack_results(dt_boxes, rec_res, scores, image)

        except Exception as e:  # noqa
            logging.warning("Could not inference model")
            logging.error(e)
            traceback.print_exc()
            return AutoLabelingResult([], replace=False)
