import cv2
import imagehash
import numpy as np
from PIL import Image

from work_flow.engines.types import AutoLabelingResult


class PixelAnalysis:
    def __init__(self, **kwargs):
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

    def predict_shape(self, image, **kwargs):
        # 饱和度分析 尖锐度分析
        brightness, saturation = self.calculate_brightness_and_saturation(image)
        variance = self.calculate_image_sharpness(image)
        description = f"Brightness: {brightness}, Saturation: {saturation}, Sharpness: {variance}"
        return AutoLabelingResult(description=description)

    def calculate_image_hash(self, image_path):
        """使用感知哈希（phash）计算图片的哈希值"""
        image = Image.open(image_path)
        return imagehash.phash(image)

    def calculate_image_hash_from_url(self, url):
        """从 URL 下载图片并计算其哈希值"""
        try:
            response = requests.get(url)
            response.raise_for_status()  # 检查请求是否成功
            with open("temp_image.jpg", 'wb') as f:  # 将图片临时保存为文件
                f.write(response.content)

            # 计算下载的图片哈希值
            image_hash = calculate_image_hash("temp_image.jpg")
            os.remove("temp_image.jpg")  # 删除临时文件
            return image_hash
        except Exception as e:
            print(f"Failed to download image from {url}: {e}")
            return None


    def get_database_hashes(self, conn):


        # 加入end_time过滤条件，确保只查询指定日期之后的记录
        query = f"""
        SELECT {attribute} 
        FROM {table} 
        WHERE handler = %s AND end_time > %s
        """

        cursor.execute(query, (handler, date_filter))
        hashes = []
        for (urls_string,) in cursor.fetchall():
            if urls_string:
                for url in urls_string.split(','):
                    # 从数据库中提取每张图片的哈希值
                    image_hash = calculate_image_hash_from_url(url)
                    if image_hash is not None:
                        hashes.append(image_hash)
        return hashes


    def compare_hashes(self, image_hash, db_hashes):
        """计算新图片的哈希值与数据库中哈希值的汉明距离"""
        return min(image_hash - db_hash for db_hash in db_hashes)


# 使用时
image_path = "D:/Mysql/handler/test2.jpeg"
image_hash = calculate_image_hash(image_path)

# 假设已经连接到数据库
conn = mysql.connector.connect(
    host='47.99.65.68',
    database='yanglao',
    user='dhgxjbgs',
    password='D23@#hGb',
    ssl_disabled=True  # 禁用 SSL/TLS
)

# 获取符合条件的数据库图片哈希值
db_hashes = get_database_hashes(conn)

similarity = compare_hashes(image_hash, db_hashes)
threshold = 5  # 设置相似度阈值

if similarity < threshold:
    print("The image is similar to an image in the database.")
else:
    print("The image is not similar to any image in the database.")

# 关闭数据库连接
conn.close()



