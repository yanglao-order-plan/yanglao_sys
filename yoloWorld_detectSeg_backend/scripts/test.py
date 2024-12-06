import base64
from PIL import Image
from io import BytesIO
import urllib.parse

def image_to_base64(image_path):
    """
    将本地图像文件转换为 Base64 编码的字符串
    :param image_path: 本地图像文件的路径
    :return: Base64 编码的字符串
    """
    # 打开图像
    with Image.open(image_path) as img:
        # 将图像转换为字节流
        buffered = BytesIO()
        img.save(buffered, format="JPEG")  # 可以根据需要调整格式，默认为 JPEG
        img_data = buffered.getvalue()

    # 将字节流转换为 Base64 编码
    base64_str = base64.b64encode(img_data).decode('utf-8')
    base64_byte = base64.b64decode(img_data)
    url = urllib.parse.quote(base64_byte)
    # 返回 Base64 编码的 URL
    return url

# 示例使用
image_path = "E:\Datasets\cook_order\Images/000b87e76aba4e9fbd4c7061dad5579e1690366289166.jpeg"  # 替换为你的图像路径
image_url = image_to_base64(image_path)

print(image_url)
