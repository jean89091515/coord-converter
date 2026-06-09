# -*- coding: utf-8 -*-
"""
坐标系转换工具 · Streamlit 应用
立方数据学社 · Vibe Coding 工作营
"""
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from coordtransform import SYSTEMS, convert, haversine_m

st.set_page_config(page_title="坐标系转换工具", page_icon="🧭", layout="wide")

# ---------------- 样式 ----------------
st.markdown(
    """
<style>
#MainMenu{visibility:hidden;}
header[data-testid="stHeader"]{height:0;visibility:hidden;}
footer{visibility:hidden;}
[data-testid="stToolbar"]{display:none;}
.block-container{padding-top:1.4rem;padding-bottom:1.2rem;max-width:1200px;}
.hdr{background:linear-gradient(90deg,#2b7fd4,#1d63b0);color:#fff;border-radius:12px;
     padding:14px 22px;margin-bottom:16px;display:flex;justify-content:space-between;
     align-items:center;box-shadow:0 6px 18px rgba(43,127,212,.28);}
.hdr .t{font-size:21px;font-weight:800;letter-spacing:.5px;}
.hdr .t small{font-weight:500;opacity:.92;margin-left:10px;font-size:14px;letter-spacing:1px;}
.hdr .b{font-size:12.5px;opacity:.92;text-align:right;line-height:1.5;}
.res{background:#eafbf1;border:1px solid #b7e6c8;border-left:6px solid #2ecc71;
     border-radius:10px;padding:12px 18px;margin-top:4px;}
.res .lab{color:#1c7a43;font-size:12.5px;font-weight:700;margin-bottom:2px;}
.res .v{font-size:25px;font-weight:800;color:#0e5e30;letter-spacing:.5px;
        font-variant-numeric:tabular-nums;}
div.stButton>button[kind="primary"]{background:linear-gradient(90deg,#2b7fd4,#2ecc71);
     border:none;font-weight:700;color:#fff;}
.sub{font-size:16px;font-weight:800;color:#1d3a5a;margin:2px 0 6px;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hdr"><div class="t">🧭 坐标系转换工具'
    '<small>WGS-84 ⇄ GCJ-02 ⇄ BD-09 ⇄ CGCS2000</small></div>'
    '<div class="b">立方数据学社 · Vibe Coding 工作营<br>v1.0 · 离线算法，无需 API Key</div></div>',
    unsafe_allow_html=True,
)

SYS_LABELS = {
    "WGS-84": "WGS-84（GPS / 国际）",
    "GCJ-02": "GCJ-02（高德 / 火星坐标）",
    "BD-09": "BD-09（百度）",
    "CGCS2000": "CGCS2000（2000 国家大地）",
}
LANDMARKS = {
    "东方明珠 (上海)": (121.499718, 31.239703),
    "外滩 (上海)": (121.490177, 31.236771),
    "上海虹桥站": (121.319000, 31.197600),
    "上海迪士尼": (121.669900, 31.143100),
    "陆家嘴 (上海)": (121.504700, 31.245400),
    "天安门 (北京)": (116.397455, 39.909187),
    "广州塔": (113.324520, 23.106414),
}

# ---------------- 状态初始化 ----------------
st.session_state.setdefault("lng_in", 121.499718)
st.session_state.setdefault("lat_in", 31.239703)
st.session_state.setdefault("src", "WGS-84")
st.session_state.setdefault("dst", "GCJ-02")


def _apply_preset():
    name = st.session_state.get("preset")
    if name in LANDMARKS:
        st.session_state.lng_in, st.session_state.lat_in = LANDMARKS[name]


def _swap():
    st.session_state.src, st.session_state.dst = st.session_state.dst, st.session_state.src


# ---------------- 主体两栏 ----------------
left, right = st.columns([1, 1.25], gap="large")

with left:
    st.markdown('<div class="sub">📍 单点转换</div>', unsafe_allow_html=True)

    st.selectbox("示例点位（选择后自动填入坐标）", ["— 自定义 —", *LANDMARKS.keys()],
                 key="preset", on_change=_apply_preset)

    c1, c2 = st.columns(2)
    lng = c1.number_input("经度 Longitude", key="lng_in", format="%.6f", step=0.0001)
    lat = c2.number_input("纬度 Latitude", key="lat_in", format="%.6f", step=0.0001)

    st.selectbox("源坐标系", SYSTEMS, key="src", format_func=lambda s: SYS_LABELS[s])
    st.button("⇅ 互换源 / 目标", on_click=_swap, use_container_width=True)
    st.selectbox("目标坐标系", SYSTEMS, key="dst", format_func=lambda s: SYS_LABELS[s])

    src, dst = st.session_state.src, st.session_state.dst
    out_lng, out_lat = convert(lng, lat, src, dst)
    offset = haversine_m(lng, lat, out_lng, out_lat)

    st.button("一键转换 →", type="primary", use_container_width=True)
    st.markdown(
        f'<div class="res"><div class="lab">✓ 转换结果（{dst}）</div>'
        f'<div class="v">{out_lng:.6f},&nbsp;&nbsp;{out_lat:.6f}</div></div>',
        unsafe_allow_html=True,
    )
    if src == dst:
        st.caption("源与目标相同，坐标未变。")
    else:
        st.caption(f"与输入坐标的位置偏移约 **{offset:,.1f} 米** —— 这就是不转换"
                   f"直接叠图会偏掉的距离。")

with right:
    st.markdown('<div class="sub">🗺️ 转换前后点位对比（叠加底图，直观验证偏移）</div>',
                unsafe_allow_html=True)
    mid = [(lat + out_lat) / 2, (lng + out_lng) / 2]
    fmap = folium.Map(location=mid, zoom_start=15 if offset < 600 else 13,
                      tiles="CartoDB positron", control_scale=True)
    folium.PolyLine([[lat, lng], [out_lat, out_lng]], color="#7886a0",
                    weight=3, opacity=0.9, dash_array="6,6").add_to(fmap)
    folium.CircleMarker([lat, lng], radius=9, color="#ffffff", weight=2, fill=True,
                        fill_color="#2ecc71", fill_opacity=1.0,
                        tooltip=f"转换前 {src}",
                        popup=f"{src}：{lng:.6f}, {lat:.6f}").add_to(fmap)
    folium.CircleMarker([out_lat, out_lng], radius=9, color="#ffffff", weight=2, fill=True,
                        fill_color="#e74c3c", fill_opacity=1.0,
                        tooltip=f"转换后 {dst}",
                        popup=f"{dst}：{out_lng:.6f}, {out_lat:.6f}").add_to(fmap)
    st_folium(fmap, height=430, returned_objects=[], use_container_width=True)
    st.caption("🟢 转换前　🔴 转换后　·　虚线为两坐标系间的偏移向量（可缩放 / 悬停查看）")

# ---------------- 批量转换 ----------------
st.divider()
st.markdown('<div class="sub">📦 批量转换（上传 CSV / Excel，整列换算并下载）</div>',
            unsafe_allow_html=True)
bc1, bc2 = st.columns([1, 1.25], gap="large")

with bc1:
    up = st.file_uploader("上传含经纬度两列的文件", type=["csv", "xlsx", "xls"])
    st.caption(f"批量转换使用上方选定的：**{src} → {dst}**。"
               "未上传时下方展示示例点位换算。")

with bc2:
    def _guess(cols, names):
        for i, c in enumerate(cols):
            if str(c).strip().lower() in names:
                return i
        return 0

    if up is not None:
        df = pd.read_csv(up) if up.name.lower().endswith(".csv") else pd.read_excel(up)
        g1, g2 = st.columns(2)
        lng_col = g1.selectbox("经度列", df.columns,
                               index=_guess(df.columns, {"lng", "lon", "longitude", "经度", "x"}))
        lat_col = g2.selectbox("纬度列", df.columns,
                               index=_guess(df.columns, {"lat", "latitude", "纬度", "y"}))
        conv = [convert(r[lng_col], r[lat_col], src, dst) for _, r in df.iterrows()]
        res = df.copy()
        res[f"经度_{dst}"] = [round(c[0], 6) for c in conv]
        res[f"纬度_{dst}"] = [round(c[1], 6) for c in conv]
        st.dataframe(res, use_container_width=True, height=240)
        st.download_button("⬇️ 下载转换结果（CSV）",
                           res.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"converted_{src}_to_{dst}.csv", mime="text/csv",
                           type="primary")
    else:
        rows = []
        for name, (a, b) in LANDMARKS.items():
            o = convert(a, b, src, dst)
            rows.append({"点位": name, f"经度({src})": a, f"纬度({src})": b,
                         f"经度({dst})": round(o[0], 6), f"纬度({dst})": round(o[1], 6),
                         "偏移(米)": round(haversine_m(a, b, *o), 1)})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=240)

# ---------------- 说明 ----------------
with st.expander("ℹ️ 三种坐标系是什么？为什么必须转换？（课堂讲解）"):
    st.markdown(
        """
| 坐标系 | 谁在用 | 说明 |
|---|---|---|
| **WGS-84** | GPS、谷歌地球、多数遥感/科研底图 | 国际通用真实坐标 |
| **GCJ-02** | 高德、腾讯、中国版谷歌 | 国家保密要求，对 WGS-84 做非线性**加偏**（俗称"火星坐标"） |
| **BD-09** | 百度地图 | 在 GCJ-02 基础上**再加密一层** |
| **CGCS2000** | 国家测绘基准 | 米级精度下≈WGS-84，本工具按等同处理 |

**核心坑**：从高德爬到的 POI 是 GCJ-02，若直接画在 WGS-84 底图（如 ECharts/Leaflet 的 OSM）上，
会整体**偏移几百米到一公里**——上面地图里那段灰线就是这个偏移。做空间分析前**必须先统一坐标系**。

**本工具**：纯公开算法离线换算，不调任何地图 API，因此可白嫖部署到 Streamlit Cloud。
对接第 6 讲「实用工具开发」，与第 4 讲「空间数据处理」的 POI 清洗环节衔接。
"""
    )
