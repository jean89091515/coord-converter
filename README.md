# 🧭 坐标系转换工具（WGS-84 ⇄ GCJ-02 ⇄ BD-09 ⇄ CGCS2000）

立方数据学社 · Vibe Coding 工作营 · 第 6 讲「实用工具开发」配套。

一个**纯离线、零 API Key** 的坐标系互转 Web 工具：单点转换、批量 CSV/Excel 转换、
地图叠加直观展示坐标系之间的偏移。算法为业内公开的 GCJ-02 偏移 / BD-09 加密公式。

## 功能
- **单点转换**：输入经纬度，任选源/目标坐标系，一键换算，并显示偏移米数。
- **地图验偏移**：底图上同时画"转换前/转换后"两点 + 偏移向量。
- **批量转换**：上传含经纬度的 CSV/Excel，整列换算并下载结果（`sample_points.csv` 为示例）。

## 本地运行
```bash
pip install -r requirements.txt
streamlit run app.py
```
浏览器打开 http://localhost:8501

## 部署到 Streamlit Community Cloud（免费、生成公网链接）
1. 把本文件夹推到一个 **GitHub 仓库**（可单独建一个干净仓库）：
   ```bash
   cd coord-converter
   git init && git add . && git commit -m "坐标系转换工具"
   gh repo create coord-converter --public --source=. --push   # 或在 GitHub 网页建仓后 push
   ```
2. 打开 **https://share.streamlit.io** → 用 GitHub 登录 → **New app**。
3. 选择该仓库 / 分支 `main` / 主文件 `app.py` → **Deploy**。
4. 约 1 分钟后得到形如 `https://<你的应用名>.streamlit.app` 的公网链接，可直接发群 / 嵌 PPT。

> Streamlit Cloud 会自动按 `requirements.txt` 装依赖；本工具不依赖任何地图密钥，开箱即用。

## 文件说明
| 文件 | 作用 |
|---|---|
| `app.py` | Streamlit 界面 |
| `coordtransform.py` | 坐标转换核心算法（可单独 `python coordtransform.py` 自检） |
| `requirements.txt` | 依赖清单（Streamlit Cloud 据此安装） |
| `.streamlit/config.toml` | 主题配色 |
| `sample_points.csv` | 批量转换示例数据（上海地标） |
