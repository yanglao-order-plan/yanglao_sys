import os
import requests
import mysql.connector
from urllib.parse import urlparse
from mysql.connector import Error

jdbc_url = "mysql://47.99.65.68:3306/yanglao"
host = '47.99.65.68'
database = 'yanglao'
username = "dhgxjbgs"
password = "D23@#hGb"


def get_img_urls(specific_service_id, img_stages, start_data, end_data, start_order_id):
    # work_order_query = f"-- SELECT order_id FROM work_order WHERE service_id = {specific_service_id} and DATE(start_time) >= {start_data} and DATE(start_time) <= {end_data}"
    work_order_query = "SELECT order_id, start_time FROM work_order WHERE  service_id = {0} AND start_time >= \"{1}\" and start_time <= \"{2}\" AND order_id >= \"{3}\""
    service_log_query_template = "SELECT {0} FROM service_log WHERE order_id = {1}"

    conn = None
    try:
        conn = mysql.connector.connect(
            host=host,
            database=database,
            user=username,
            password=password,
            # ssl_disabled=False  # 禁用 SSL/TLS
        )

        if conn.is_connected():
            cursor = conn.cursor()

            # 查询 work_order 表，获取 order_id
            print(work_order_query.format(specific_service_id, start_data, end_data, start_order_id))
            cursor.execute(work_order_query.format(specific_service_id, start_data, end_data, start_order_id))
            order_ids_times = [(row[0], row[1]) for row in cursor.fetchall()]
            # return order_ids_times

            urls_all = dict()
            # 三层列表，用于存储所有订单的图片 URL
            for item in order_ids_times:
                urls_all[item] = []
                order_id = item[0]
                for attribute in img_stages:
                    service_log_query = service_log_query_template.format(attribute, order_id)
                    cursor.execute(service_log_query)
                    for (urls_string,) in cursor.fetchall():
                        if urls_string:
                            urls = urls_string.split(',')
                            urls_all[item] += urls
                            # download_images(order_id, attribute, urls, base_dir)
                        else:
                            print(f"No URLs found for order_id {order_id} and attribute {attribute}")
            return urls_all

    except Error as e:
        print(f"Error: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def download_images(order_id, attribute, urls, base_dir):
    order_dir = os.path.join(base_dir, str(order_id))
    attribute_dir = os.path.join(order_dir, attribute)
    os.makedirs(attribute_dir, exist_ok=True)

    for url in urls:
        try:
            response = requests.get(url, stream=True, verify=False)  # 禁用 SSL 证书验证
            response.raise_for_status()  # 如果响应状态码不是200，则抛出异常

            # 从 URL 中提取文件名
            file_name = get_file_name_from_url(url)
            file_path = os.path.join(attribute_dir, file_name)

            with open(file_path, 'wb') as out_file:
                out_file.write(response.content)

            print(f"Downloaded image from {url} to {file_path}")

        except requests.RequestException as e:
            print(f"Failed to download image from {url}: {e}")

def get_file_name_from_url(url):
    parsed_url = urlparse(url)
    return os.path.basename(parsed_url.path)

if __name__ == "__main__":
    specific_service_id = 406
    start_order_id = 447523
    img_stages = "img_url"
    base_dir = "E:\\test\\download"  # 设置保存图片的基础目录
    start_data = '2024-3-1'
    end_data = '2024-4-30'
    print(len(get_img_urls(specific_service_id, [img_stages], start_data, end_data, start_order_id)))
