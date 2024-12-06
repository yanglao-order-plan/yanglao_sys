from io import BytesIO

import cv2
import imagehash
import numpy as np
import requests
from PIL import Image

from work_flow.engines.types import AutoLabelingResult
from work_flow.utils.shape import Shape


class PixelAnalysis:
    def __init__(self, model_config, **kwargs):
        self.hash_threshold = 5
        self.saturation_threshold = 100
        pass

    def calculate_brightness_and_saturation(self, image):
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv_image)
        brightness = np.mean(v)
        saturation = np.mean(s)
        return brightness, saturation

    def calculate_image_sharpness(self, image):
        # 读取图像
        gray_image = cv2.cvtColor(image, cv2.IMREAD_GRAYSCALE)
        laplacian = cv2.Laplacian(gray_image, cv2.CV_64F)
        variance = np.var(laplacian)
        return variance

    def predict_shapes(self, image, minor=None, mode='repeat'):
        # 饱和度分析 尖锐度分析
        if image is None:
            raise ValueError("Image is None")
        if mode == 'hash':
            if minor is None:
                raise ValueError("Minor image is None")
            image_hash = imagehash.phash(Image.fromarray(image))
            minor_hash = imagehash.phash(Image.fromarray(minor))
            hash_distance = image_hash - minor_hash
            shape=Shape(score=hash_distance, visible=False)
            if hash_distance < self.hash_threshold:
                shape.label = True
                description = '相似图片'
            else:
                shape.label = False
                description = '非相似图片'
            return  AutoLabelingResult(shapes=[shape], description=description)

        elif mode == 'saturation':
            brightness, saturation = self.calculate_brightness_and_saturation(image)
            shape=Shape(score=saturation, visible=False)
            if saturation > self.saturation_threshold:
                shape.label = True
                description = '疑似网图'
            else:
                shape.label = False
                description = '非疑似网图'
            return AutoLabelingResult(shapes=[shape], description=description)

        return AutoLabelingResult(shapes=[])


# if urls is None:
#     raise ValueError("Minor urls is None")
# image_hash = imagehash.phash(Image.fromarray(image))
# hash_distances = []
# for url in urls:
#     try:
#         # 从 URL 下载图片
#         response = requests.get(url)
#         response.raise_for_status()  # 如果请求失败会抛出异常
#         # 将下载的内容转化为图片
#         img = Image.open(BytesIO(response.content))
#         minor_hash = imagehash.phash(Image.fromarray(img))
#         hash_distances.append(image_hash - minor_hash)
#     except Exception as e:
#         print(f"Error downloading or processing image from {url}: {e}")


