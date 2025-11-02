# OneStroke — Vue3 + FastAPI (mobile-ready)

一笔画（欧拉路径/回路）小游戏。前端基于 Vue 3 + Canvas，后端基于 FastAPI，内置关卡生成、完整求解和“智能下一步提示”。支持本地开发与 Docker 一键部署。

- 前端：Vue 3 + Vite + Canvas（移动触控友好）
- 后端：FastAPI（/generate, /level, /solve, /hint 接口）
- 关卡：随机生成，保证欧拉可解（回路或路径）
- 提示：桥（bridge）规避策略，尽量避免走到死胡同
- 可选：接入视觉大模型做文字讲解（OPENAI_API_KEY）

---

## 目录结构（带链接）

- 根目录
  - [.gitignore](.gitignore)
  - [docker-compose.yml](docker-compose.yml)
  - [README.md](README.md)
- 后端 [backend/](backend)
  - [Dockerfile](backend/Dockerfile)
  - [requirements.txt](backend/requirements.txt)
  - [main.py](backend/main.py)（FastAPI 入口）
  - [generate_graph.py](backend/generate_graph.py)（随机生成欧拉图）
  - 算法
    - [algorithms/euler.py](backend/algorithms/euler.py)
      - 核心求解：[`algorithms.euler.find_euler_path`](backend/algorithms/euler.py)
      - 智能提示：[`algorithms.euler.find_next_step`](backend/algorithms/euler.py)
  - 服务
    - [services/llm_client.py](backend/services/llm_client.py)（可选 LLM 讲解：[`services.llm_client.explain_with_llm`](backend/services/llm_client.py)）
- 前端 [frontend/](frontend)
  - [Dockerfile](frontend/Dockerfile)
  - [nginx.conf](frontend/nginx.conf)
  - [index.html](frontend/index.html)
  - [package.json](frontend/package.json)
  - [vite.config.mjs](frontend/vite.config.mjs)
  - 源码 [src/](frontend/src)
    - [main.js](frontend/src/main.js)
    - [App.vue](frontend/src/App.vue)
    - 组件
      - [components/GameCanvas.vue](frontend/src/components/GameCanvas.vue)（画布交互、提示、撤销、关卡切换）
    - 工具
      - [utils/euler.js](frontend/src/utils/euler.js)
    - API
      - [api/fastapi.js](frontend/src/api/fastapi.js)
- 示例与可视化
  - [gifs/euler.py](gifs/euler.py)（暴力搜索并生成 GIF）
  - [gifs/gifs.py](gifs/gifs.py)（基于 networkx 动画）

---

## 快速开始

### 方式一：本地开发（前后端分开跑）

1) 后端

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # 或 conda
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2) 前端

当前前端将 API 指向相对路径“/api”（见 [frontend/src/api/fastapi.js](frontend/src/api/fastapi.js)），适配 Docker 下的 Nginx 反代。若本地直连后端，请临时将 baseURL 调整为 http://localhost:8000，或为 Vite 添加代理。

临时直连（简单做法）：
- 将 [frontend/src/api/fastapi.js](frontend/src/api/fastapi.js) 中
  - `const api = axios.create({ baseURL: "/api" });`
  - 暂改为 `const api = axios.create({ baseURL: "http://localhost:8000" });`

启动前端：

```bash
cd frontend
npm install
npm run dev
# 打开 http://localhost:5174
```

注意：vite.config.mjs 已指定 dev 端口 5174。

### 方式二：Docker 一键启动（推荐）

```bash
docker compose up -d --build
# 前端: http://localhost/
# 后端: http://localhost:8000/ (供调试)
```

说明：
- 前端容器使用 Nginx，已在 [frontend/nginx.conf](frontend/nginx.conf) 配置 `/api -> backend:8000` 反向代理
- 前端 axios 使用相对路径 `/api`，与反代对齐，无需修改

---

## 后端 API 说明

Base URL（本地直连）：http://localhost:8000  
Base URL（Docker 前端转发）：/api

- GET /generate  
  返回一个简单 demo 关卡（示例三角形）。
  - 逻辑在 [backend/main.py](backend/main.py) -> `generate_demo`

- GET /level?difficulty=easy|medium|hard&index=1  
  返回指定难度、关卡编号的随机可解图。指数种子固定（index）保证同一编号可复现。
  - 生成器：[`generate_eulerian_graph_data`](backend/generate_graph.py)
  - 难度控制节点范围与稠密度，easy/medium 返回回路图，hard 返回路径图

- POST /solve  
  请求：`{ "nodes": number[], "edges": [ [u,v], ... ] }`  
  响应：`{ "ok": true, "path": number[] }` 或 `{ "ok": false, "error": string }`  
  - 求解器：[`algorithms.euler.find_euler_path`](backend/algorithms/euler.py)
  - 算法：Hierholzer，返回顶点序列，前端据此染色

- POST /hint  
  请求：`{ "nodes": number[], "edges": [ [u,v]... ], "visitedEdges": string[], "pathEndpoint": number | null }`  
  响应：`{ "ok": true, "move": [from, to] }` 或 `{ "ok": false, "message": string }`  
  - 智能提示：[`algorithms.euler.find_next_step`](backend/algorithms/euler.py)
  - 思路：统计“剩余边”，模拟移除每个候选边，优先选择“非桥”；若只有唯一出边则必须走；全部用尽则判断是否通关

可选：LLM 讲解  
- 若设置环境变量 `OPENAI_API_KEY`，可通过 [`services.llm_client.explain_with_llm`](backend/services/llm_client.py) 生成自然语言说明（当前未在接口中对外暴露，预留扩展位）。

---

## 实现原理（算法与交互）

- 欧拉路径/回路判定  
  必要条件：奇度顶点个数 $|V_{odd}| \in \{0,2\}$。  
  - 0 个奇度点 → 存在欧拉回路  
  - 2 个奇度点 → 存在欧拉路径  
  - 见前端校验辅助 [utils/euler.js](frontend/src/utils/euler.js) 与后端生成器

- 完整求解（/solve）  
  [`algorithms.euler.find_euler_path`](backend/algorithms/euler.py) 使用 Hierholzer 算法：
  1) 从合法起点出发（若有 2 奇点取其一，否则任意非孤立点）  
  2) 沿未用边前进入栈，无法继续时出栈记录  
  3) 反转得完整顶点序列（即解）

- 智能提示（/hint）  
  [`algorithms.euler.find_next_step`](backend/algorithms/euler.py) 关键点：
  - 剩余边图重建并计数（支持重复边）
  - 若当前端点只有唯一可走边，必须走
  - 否则尝试“删边做 DFS 连通性对比”，优先推荐“非桥”避免割裂剩余连通性
  - 若无边可走：校验是否所有边均被正确次数访问，是则通关，否则提示“死胡同”

- 关卡生成  
  [`generate_eulerian_graph_data`](backend/generate_graph.py)：
  1) 生成 G(n,p) 随机图，强制连通  
  2) 成对修复奇度点为偶数（回路）  
  3) 若需要“路径图”，随机删一条边制造 2 个奇点  
  4) 再核验连通与奇度条件，不满足则重试

- 前端交互（[components/GameCanvas.vue](frontend/src/components/GameCanvas.vue)）  
  - 触控/鼠标拖拽连边，按访问顺序染色并绘制箭头与序号
  - 底部工具：难度切换、关卡切换、撤销一步、提示（调用 /solve）、重置
  - 本地状态：`visitedEdges`、`pathEndpoint`、`currentNode` 等
  - 与后端交互：`/level` 拉取关卡，`/solve` 获取完整解，后续可扩展 `/hint`

---

## 前后端对接与网络

- 本地开发直连后端：将 [frontend/src/api/fastapi.js](frontend/src/api/fastapi.js) 的 baseURL 改为 `http://localhost:8000`
- Docker 部署：保持 baseURL 为 `/api`，由 [frontend/nginx.conf](frontend/nginx.conf) 反向代理到后端容器 `backend:8000`

---

## 运行示例动画（可选）

- 生成探索 GIF（需安装 `networkx`, `matplotlib`, `imageio`）：
  - [gifs/euler.py](gifs/euler.py)：暴力搜索每一步并合成 `euler_path_brute_force.gif`
  - [gifs/gifs.py](gifs/gifs.py)：使用 `FuncAnimation` 按欧拉路径逐帧绘制

```bash
cd gifs
python euler.py
python gifs.py
```

---

## 依赖与环境

- Python（后端）：见 [backend/requirements.txt](backend/requirements.txt)
- Node（前端）：见 [frontend/package.json](frontend/package.json)
- Vite Dev Server 端口：5174（见 [frontend/vite.config.mjs](frontend/vite.config.mjs)）
- Docker：前端 80，后端 8000；compose 已建立 `app-network`，通过服务名互通

---

## 常见问题

- 本地启动前端后接口 404  
  - 使用 Docker（一键反代），或按上文修改 baseURL 为后端直连
- 关卡不可解？  
  - 生成器已强制满足欧拉条件与连通，如遇异常，重试或检查日志
- LLM 提示无效  
  - 确保配置了环境变量 `OPENAI_API_KEY`；当前未作为公开接口暴露，仅作内部演示

---