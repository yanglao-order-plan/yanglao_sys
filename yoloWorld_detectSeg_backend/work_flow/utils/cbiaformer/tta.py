import cv2
import numpy as np
from torchvision import transforms
from PIL import ImageFilter, ImageEnhance,Image
from torchvision.transforms import InterpolationMode


class histogramTransform:
    def __init__(self):
        pass

    def __call__(self, image):
        img = np.array(image)
        img_yuv = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img_yuv[:, :, 0] = clahe.apply(img_yuv[:, :, 0])
        img_output = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2RGB)
        return Image.fromarray(img_output)

class brightTransform:
    def __init__(self):
        pass

    def __call__(self, image):
        image = image.filter(ImageFilter.GaussianBlur(0.3))
        b = ImageEnhance.Brightness(image)
        return b.enhance(1.5)

class contrastTransform:
    def __init__(self):
        pass

    def __call__(self, image):
        enh_con = ImageEnhance.Contrast(image)
        image = enh_con.enhance(2)

        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2)
        return image

tta_transforms = [
    transforms.Compose([
        transforms.Resize((224, 224), InterpolationMode.BICUBIC),
        brightTransform(),
        transforms.ToTensor(),
        transforms.Normalize([0.600703, 0.506933, 0.386077], [0.074954, 0.082138, 0.094773])
    ]),
    transforms.Compose([
        transforms.Resize((224, 224), InterpolationMode.BICUBIC),
        transforms.RandomHorizontalFlip(p=1.0),
        transforms.ToTensor(),
        transforms.Normalize([0.600703, 0.506933, 0.386077], [0.074954, 0.082138, 0.094773])
    ]),
    transforms.Compose([
        transforms.Resize((224, 224), InterpolationMode.BICUBIC),
        contrastTransform(),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize([0.600703, 0.506933, 0.386077], [0.074954, 0.082138, 0.094773])
    ]),
    transforms.Compose([
        transforms.Resize((224, 224), InterpolationMode.BICUBIC),
        histogramTransform(),
        transforms.ToTensor(),
        transforms.Normalize([0.600703, 0.506933, 0.386077], [0.074954, 0.082138, 0.094773])
    ]),
    transforms.Compose([
        transforms.Resize((224, 224), InterpolationMode.BICUBIC),
        transforms.ToTensor(),
        transforms.Normalize([0.600703, 0.506933, 0.386077], [0.074954, 0.082138, 0.094773])
    ])
]