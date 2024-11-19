import logging
import os
import os.path as osp
import base64
import io
import shutil
from typing import List

import cv2
import mmcv
import numpy as np
import PIL.ExifTags
import PIL.Image
import PIL.ImageOps
from PIL import Image


def batch_base64_encode_image(results_images):
    for im in results_images.imgs:
        buffered = io.BytesIO()
        im_base64 = Image.fromarray(im)
        im_base64.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def base64_encode_image(image) -> str:
    buffered = io.BytesIO()
    dim = image.ndim
    if dim == 2:  # 这种一般都是单个张量，未添加mat签名
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif dim == 3:
        cv2.cvtColor(image, cv2.COLOR_RGB2BGR, image)
    elif dim == 4:
        cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA, image)
    im_base64 = Image.fromarray(image)
    im_base64.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{img_str}"

def img_data_to_pil(img_data):
    f = io.BytesIO()
    f.write(img_data)
    img_pil = PIL.Image.open(f)
    return img_pil


def img_data_to_arr(img_data):
    img_pil = img_data_to_pil(img_data)
    img_arr = np.array(img_pil)
    return img_arr


def img_b64_to_arr(img_b64):
    img_data = base64.b64decode(img_b64)
    img_arr = img_data_to_arr(img_data)
    return img_arr


def img_pil_to_data(img_pil):
    f = io.BytesIO()
    img_pil.save(f, format="PNG")
    img_data = f.getvalue()
    return img_data


def numpy_to_pil(np_image: np.ndarray) -> Image.Image:
    """
    将 NumPy 数组转换为 PIL 图像对象，处理不同的颜色模式和通道顺序。

    Args:
        np_image (np.ndarray): 输入的 NumPy 图像数组。

    Returns:
        Image.Image: 转换后的 PIL 图像对象。

    Raises:
        ValueError: 如果图像格式不受支持。
    """
    if np_image is None:
        raise ValueError("输入的 NumPy 图像为 None。")

    # 检查图像的维度
    if len(np_image.shape) == 2:
        # 灰度图像
        return Image.fromarray(np_image, mode='L')
    elif len(np_image.shape) == 3:
        height, width, channels = np_image.shape
        if channels == 1:
            # 单通道灰度图像
            return Image.fromarray(np_image[:, :, 0], mode='L')
        elif channels == 3:
            # BGR 转 RGB
            rgb_image = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb_image, 'RGB')
        elif channels == 4:
            # BGRA 转 RGBA
            rgba_image = cv2.cvtColor(np_image, cv2.COLOR_BGRA2RGBA)
            return Image.fromarray(rgba_image, 'RGBA')
        else:
            raise ValueError(f"不支持的通道数: {channels}")
    else:
        raise ValueError(f"不支持的图像形状: {np_image.shape}")

def crop_polygon_object(image, polygon_points, background_color=(0, 0, 0)):
    """
    根据给定的多边形顶点裁剪图像，仅保留多边形内部的区域。
    新图像为裁剪对象的最小外接矩形，多边形外部区域用指定的背景颜色填充。

    Args:
        image (np.ndarray): 原始图像，BGR 或 RGB 格式。
        polygon_points (list or np.ndarray): 多边形顶点列表，例如 [(x1, y1), (x2, y2), ...]。
        background_color (tuple): 背景颜色，默认为黑色，格式为 (B, G, R)。

    Returns:
        np.ndarray: 裁剪后的图像，三通道。
    """
    # 确保多边形点为 numpy 数组并为整数类型
    if isinstance(polygon_points, list):
        polygon_points = np.array(polygon_points, dtype=np.int32)
    elif isinstance(polygon_points, np.ndarray):
        polygon_points = polygon_points.astype(np.int32)
    else:
        raise ValueError("polygon_points 应为列表或 numpy 数组")

    # 创建与图像尺寸相同的掩码
    mask = np.zeros(image.shape[:2], dtype=np.uint8)

    # 在掩码上绘制并填充多边形
    cv2.fillPoly(mask, [polygon_points], 255)

    # 计算多边形的最小外接矩形
    x, y, w, h = cv2.boundingRect(polygon_points)

    # 裁剪掩码和图像到最小外接矩形
    mask_cropped = mask[y:y+h, x:x+w]
    image_cropped = image[y:y+h, x:x+w]

    # 创建与裁剪后图像相同大小的背景图像
    background = np.full(image_cropped.shape, background_color, dtype=np.uint8)

    # 使用掩码将多边形区域从原图像复制到背景图像上
    mask_inv = cv2.bitwise_not(mask_cropped)
    fg = cv2.bitwise_and(image_cropped, image_cropped, mask=mask_cropped)
    bg = cv2.bitwise_and(background, background, mask=mask_inv)
    result = cv2.add(fg, bg)

    return result



def img_arr_to_b64(img_arr):
    img_pil = PIL.Image.fromarray(img_arr)
    f = io.BytesIO()
    img_pil.save(f, format="PNG")
    img_bin = f.getvalue()
    if hasattr(base64, "encodebytes"):
        img_b64 = base64.encodebytes(img_bin)
    else:
        img_b64 = base64.encodestring(img_bin)
    return img_b64


def img_data_to_png_data(img_data):
    with io.BytesIO() as f:
        f.write(img_data)
        img = PIL.Image.open(f)

        with io.BytesIO() as f:
            img.save(f, "PNG")
            f.seek(0)
            return f.read()


def process_image_exif(filename):
    """Process image EXIF orientation and save if necessary."""
    with PIL.Image.open(filename) as img:
        exif_data = None
        if hasattr(img, "_getexif"):
            exif_data = img._getexif()
        if exif_data is not None:
            for tag, value in exif_data.items():
                tag_name = PIL.ExifTags.TAGS.get(tag, tag)
                if tag_name != "Orientation":
                    continue
                if value == 3:
                    img = img.rotate(180, expand=True)
                    rotation = "180 degrees"
                elif value == 6:
                    img = img.rotate(270, expand=True)
                    rotation = "270 degrees"
                elif value == 8:
                    img = img.rotate(90, expand=True)
                    rotation = "90 degrees"
                else:
                    return  # No rotation needed
                backup_dir = osp.join(
                    osp.dirname(osp.dirname(filename)),
                    "x-anylabeling-exif-backup",
                )
                os.makedirs(backup_dir, exist_ok=True)
                backup_filename = osp.join(backup_dir, osp.basename(filename))
                shutil.copy2(filename, backup_filename)
                img.save(filename)
                logging.error(
                    f"Rotated {filename} by {rotation}, saving backup to {backup_filename}"
                )
                break


def apply_exif_orientation(image):
    try:
        exif = image._getexif()
    except AttributeError:
        exif = None

    if exif is None:
        return image

    exif = {
        PIL.ExifTags.TAGS[k]: v
        for k, v in exif.items()
        if k in PIL.ExifTags.TAGS
    }

    orientation = exif.get("Orientation", None)

    if orientation == 1:
        # do nothing
        return image
    if orientation == 2:
        # left-to-right mirror
        return PIL.ImageOps.mirror(image)
    if orientation == 3:
        # rotate 180
        return image.transpose(PIL.Image.ROTATE_180)
    if orientation == 4:
        # top-to-bottom mirror
        return PIL.ImageOps.flip(image)
    if orientation == 5:
        # top-to-left mirror
        return PIL.ImageOps.mirror(image.transpose(PIL.Image.ROTATE_270))
    if orientation == 6:
        # rotate 270
        return image.transpose(PIL.Image.ROTATE_270)
    if orientation == 7:
        # top-to-right mirror
        return PIL.ImageOps.mirror(image.transpose(PIL.Image.ROTATE_90))
    if orientation == 8:
        # rotate 90
        return image.transpose(PIL.Image.ROTATE_90)
    return image
