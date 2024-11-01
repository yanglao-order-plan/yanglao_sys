import os
import os.path as osp
import base64
import io
import shutil

import cv2
import numpy as np
import PIL.ExifTags
import PIL.Image
import PIL.ImageOps
from PIL import Image

from PyQt5 import QtGui

from utils.backend_utils.colorprinter import print_red


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


def pil_to_qimage(img):
    """Convert PIL Image to QImage."""
    img = img.convert("RGBA")  # Ensure image is in RGBA format
    data = np.array(img)
    height, width, channel = data.shape
    bytes_per_line = 4 * width
    qimage = QtGui.QImage(
        data, width, height, bytes_per_line, QtGui.QImage.Format_RGBA8888
    )
    return qimage


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
                print_red(
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
