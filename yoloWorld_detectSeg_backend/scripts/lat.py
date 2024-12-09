from geopy.geocoders import Nominatim
import requests


# 获取地址的经纬度范围
def get_address_bounds(address):
    geolocator = Nominatim(user_agent="geoapiExercises")

    location = geolocator.geocode(address)
    if location:
        latitude = location.latitude
        longitude = location.longitude

        # 返回一个包含经纬度的元组
        # 这里我们可以假设返回的是一个简单的点，不涉及精确的矩形范围
        return latitude, longitude
    else:
        print(f"无法找到地址: {address}")
        return None


# 判断给定经纬度是否在范围内
def is_point_in_area(bounds, latitude, longitude):
    min_lat, max_lat, min_lon, max_lon = bounds

    # 检查给定的经纬度是否在边界框内
    return min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon


# 示例地址（这个地址应该来自API查询获取范围信息）
address = "北京市, 中国"
bounds = get_address_bounds(address)

# 判定地址的经纬度
target_latitude = 39.9042  # 例如：北京市的纬度
target_longitude = 116.4074  # 例如：北京市的经度

# 判断是否在范围内
if bounds:
    print(is_point_in_area(bounds, target_latitude, target_longitude))
