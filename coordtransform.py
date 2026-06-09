# -*- coding: utf-8 -*-
"""
坐标系转换核心算法（纯 Python，无需联网 / 无需 API Key）
============================================================
支持四种坐标系互转：
  - WGS-84  : GPS / 国际标准（谷歌地球、GPS 设备、多数遥感底图）
  - GCJ-02  : 国测局「火星坐标系」（高德、腾讯、中国版谷歌）
  - BD-09   : 百度坐标系（百度地图，在 GCJ-02 上再加密一次）
  - CGCS2000: 2000 国家大地坐标系；在米级精度下与 WGS-84 视为一致，
              本工具按等同 WGS-84 处理（如需厘米级测绘请用专业基准转换）。

算法为业内公开的 GCJ-02 偏移公式 + BD-09 加密公式（coordtransform / eviltransform）。
转换思路：任意坐标 → 先归一到 WGS-84 → 再转到目标坐标系。
"""
import math

X_PI = math.pi * 3000.0 / 180.0
PI = math.pi
A = 6378245.0                      # 克拉索夫斯基椭球长半轴（GCJ-02 偏移算法基准）
EE = 0.00669342162296594323        # 椭球偏心率平方

SYSTEMS = ["WGS-84", "GCJ-02", "BD-09", "CGCS2000"]


def _out_of_china(lng, lat):
    """粗略判断是否在中国境外；境外不做偏移（GCJ-02 仅对境内加密）。"""
    return not (72.004 <= lng <= 137.8347 and 0.8293 <= lat <= 55.8271)


def _transform_lat(x, y):
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * PI) + 40.0 * math.sin(y / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * PI) + 320.0 * math.sin(y * PI / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * PI) + 40.0 * math.sin(x / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * PI) + 300.0 * math.sin(x / 30.0 * PI)) * 2.0 / 3.0
    return ret


def wgs84_to_gcj02(lng, lat):
    """WGS-84 → GCJ-02（加偏移）。"""
    if _out_of_china(lng, lat):
        return lng, lat
    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * PI)
    return lng + dlng, lat + dlat


def gcj02_to_wgs84(lng, lat):
    """GCJ-02 → WGS-84（数值迭代逼近逆变换，收敛到亚毫米级）。"""
    if _out_of_china(lng, lat):
        return lng, lat
    wlng, wlat = lng, lat
    for _ in range(30):
        glng, glat = wgs84_to_gcj02(wlng, wlat)
        dlng, dlat = glng - lng, glat - lat
        if abs(dlng) < 1e-9 and abs(dlat) < 1e-9:
            break
        wlng -= dlng
        wlat -= dlat
    return wlng, wlat


def gcj02_to_bd09(lng, lat):
    """GCJ-02 → BD-09（百度二次加密）。"""
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * X_PI)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * X_PI)
    return z * math.cos(theta) + 0.0065, z * math.sin(theta) + 0.006


def bd09_to_gcj02(lng, lat):
    """BD-09 → GCJ-02。"""
    x, y = lng - 0.0065, lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * X_PI)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * X_PI)
    return z * math.cos(theta), z * math.sin(theta)


def _to_wgs84(lng, lat, src):
    if src in ("WGS-84", "CGCS2000"):
        return lng, lat
    if src == "GCJ-02":
        return gcj02_to_wgs84(lng, lat)
    if src == "BD-09":
        return gcj02_to_wgs84(*bd09_to_gcj02(lng, lat))
    raise ValueError(f"未知坐标系: {src}")


def _from_wgs84(lng, lat, dst):
    if dst in ("WGS-84", "CGCS2000"):
        return lng, lat
    if dst == "GCJ-02":
        return wgs84_to_gcj02(lng, lat)
    if dst == "BD-09":
        return gcj02_to_bd09(*wgs84_to_gcj02(lng, lat))
    raise ValueError(f"未知坐标系: {dst}")


def convert(lng, lat, src, dst):
    """任意坐标系互转：src → dst。返回 (lng, lat)。"""
    lng, lat = float(lng), float(lat)
    if src == dst:
        return lng, lat
    w_lng, w_lat = _to_wgs84(lng, lat, src)
    return _from_wgs84(w_lng, w_lat, dst)


def haversine_m(lng1, lat1, lng2, lat2):
    """两点球面距离（米）。用于直观展示坐标系之间的偏移量。"""
    R = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


if __name__ == "__main__":
    # 自检：天安门 WGS-84 → GCJ-02，偏移应约几十~一百多米
    g = convert(116.397455, 39.909187, "WGS-84", "GCJ-02")
    print("WGS-84 → GCJ-02:", round(g[0], 6), round(g[1], 6))
    print("偏移(米):", round(haversine_m(116.397455, 39.909187, *g), 1))
