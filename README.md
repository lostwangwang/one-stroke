# OneStroke — Vue3 + FastAPI (mobile-ready)

一个可运行的最小可行版本（MVP），包含：

- 前端：Vue 3 + Vite + Canvas（移动触控友好）
- 后端：FastAPI（/generate, /solve 两个接口）

---

## 文件结构（本项目）

```
one-stroke/
├─ frontend/
│  ├─ package.json
│  ├─ vite.config.js
│  └─ src/
│     ├─ main.js
│     ├─ App.vue
│     ├─ components/
│     │  └─ GameCanvas.vue
│     ├─ utils/
│     │  └─ euler.js
│     └─ api/
│        └─ fastapi.js
└─ backend/
   ├─ requirements.txt
   ├─ main.py
   └─ algorithms/
      └─ euler.py
```

---

## 快速开始（在本地运行）

### 后端（FastAPI）

1. 进入 `backend` 目录，创建虚拟环境并安装依赖：

```bash
python -m venv .venv
source .venv/bin/activate   # windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. 启动服务：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端运行后，`/generate` 返回一个 demo 关卡，`/solve` 接受 `{ nodes: [...], edges: [[a,b], ...] }` 并返回欧拉路径。

---

### 前端（Vue3 + Vite）

1. 进入 `frontend` 目录，安装依赖并运行：

```bash
npm install
npm run dev
```

2. 打开手机浏览器或模拟器访问 Vite 输出的 URL（通常为 http://localhost:5173），项目已自适配移动端触控。

---

## 代码清单

下面是各文件的最小实现，你可以直接复制到对应位置并运行。

---

### backend/requirements.txt

```
fastapi
uvicorn[standard]
python-multipart
pydantic
```

---

### backend/algorithms/euler.py

```python
from collections import defaultdict

# 找欧拉路径（无向图）。nodes: list of ids, edges: list of (a,b)
def find_euler_path(nodes, edges):
    graph = defaultdict(list)
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)

    # find start
    odd = [n for n in graph if len(graph[n]) % 2 == 1]
    if len(odd) not in (0, 2):
        return None
    start = odd[0] if odd else (nodes[0] if nodes else None)
    if start is None:
        return []

    # Hierholzer
    stack = [start]
    path = []
    local = {k: list(v) for k, v in graph.items()}
    while stack:
        v = stack[-1]
        if local.get(v):
            u = local[v].pop()
            # remove reverse
            local[u].remove(v)
            stack.append(u)
        else:
            path.append(stack.pop())
    return path[::-1]
```

---

### backend/main.py

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Tuple, Optional
from fastapi.middleware.cors import CORSMiddleware
from algorithms.euler import find_euler_path

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class GraphInput(BaseModel):
    nodes: List[int]
    edges: List[Tuple[int, int]]

@app.get('/generate')
def generate_demo():
    # 简单三角形 demo
    nodes = [1,2,3]
    edges = [(1,2),(2,3),(3,1)]
    return {"nodes": nodes, "edges": edges}

@app.post('/solve')
def solve_graph(graph: GraphInput):
    path = find_euler_path(graph.nodes, graph.edges)
    if path is None:
        return {"ok": False, "error": "No Euler path"}
    return {"ok": True, "path": path}
```

---

### frontend/package.json

```json
{
  "name": "one-stroke-frontend",
  "version": "0.0.1",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.4.0",
    "vue": "^3.3.4"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.2.0",
    "vite": "^5.0.0"
  }
}
```

---

### frontend/vite.config.js

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: { port: 5173 }
})
```

---

### frontend/src/main.js

```js
import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
```

---

### frontend/src/App.vue

```vue
<template>
  <div id="app">
    <GameCanvas />
  </div>
</template>

<script setup>
import GameCanvas from './components/GameCanvas.vue'
</script>

<style>
html,body,#app{height:100%;margin:0}
#app{display:flex;flex-direction:column;height:100vh}
</style>
```

---

### frontend/src/api/fastapi.js

```js
import axios from 'axios'
const api = axios.create({ baseURL: 'http://localhost:8000' })
export const fetchDemo = () => api.get('/generate').then(r=>r.data)
export const solveGraph = (graph) => api.post('/solve', graph).then(r=>r.data)
```

---

### frontend/src/utils/euler.js

```js
// client-side simple validator and helper for edges
export function isEulerPossible(nodes, edges){
  const deg = new Map();
  edges.forEach(([a,b])=>{ deg.set(a,(deg.get(a)||0)+1); deg.set(b,(deg.get(b)||0)+1) })
  let odd=0; for(const v of deg.values()) if(v%2) odd++
  return odd===0 || odd===2
}
```

---

### frontend/src/components/GameCanvas.vue

```vue
<template>
  <div style="flex:1;display:flex;flex-direction:column">
    <canvas ref="canvas" style="flex:1;background:#f6f8fa;touch-action:none"></canvas>
    <div style="padding:8px;display:flex;gap:8px;justify-content:center">
      <button @click="loadDemo">加载示例</button>
      <button @click="askSolve">提示（后端求解）</button>
      <button @click="reset">重置</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { fetchDemo, solveGraph } from '../api/fastapi'

const canvas = ref(null)
let ctx = null
let nodes = []
let edges = []
let visitedEdges = new Set()
let currentNode = null
let scale = 1

function draw(){
  if(!ctx) return
  ctx.clearRect(0,0,canvas.value.width,canvas.value.height)
  // draw edges
  ctx.lineWidth = 6
  edges.forEach(([a,b])=>{
    const na = nodes.find(n=>n.id===a)
    const nb = nodes.find(n=>n.id===b)
    const key = edgeKey(a,b)
    ctx.beginPath()
    ctx.moveTo(na.x, na.y)
    ctx.lineTo(nb.x, nb.y)
    ctx.strokeStyle = visitedEdges.has(key) ? '#0b84ff' : '#cbd5e1'
    ctx.stroke()
  })
  // draw nodes
  nodes.forEach(n=>{
    ctx.beginPath(); ctx.arc(n.x,n.y,18,0,Math.PI*2); ctx.fillStyle='#fff'; ctx.fill();
    ctx.strokeStyle='#333'; ctx.lineWidth=2; ctx.stroke();
  })
}

function edgeKey(a,b){ return a<b?`${a}-${b}`:`${b}-${a}` }

function reset(){ visitedEdges.clear(); currentNode=null; draw() }

async function loadDemo(){
  const res = await fetchDemo()
  nodes = res.nodes.map((id,i)=>({ id, x: 60 + i*120, y: 120 + (i%2)*60 }))
  edges = res.edges
  reset()
}

async function askSolve(){
  const graph = { nodes: nodes.map(n=>n.id), edges }
  const res = await solveGraph(graph)
  if(!res.ok){ alert(res.error||'无法求解') ; return }
  // animate solution
  const path = res.path
  // transform path -> edges visited
  visitedEdges.clear()
  for(let i=0;i<path.length-1;i++) visitedEdges.add(edgeKey(path[i],path[i+1]))
  draw()
}

function findNodeAt(x,y){
  return nodes.find(n=>Math.hypot(n.x-x,n.y-y) < 24)
}

function onTouchStart(e){
  e.preventDefault()
  const t = e.touches ? e.touches[0] : e
  const rect = canvas.value.getBoundingClientRect()
  const x = (t.clientX - rect.left)
  const y = (t.clientY - rect.top)
  const n = findNodeAt(x,y)
  if(n) currentNode = n.id
}

function onTouchMove(e){
  if(!currentNode) return
  e.preventDefault()
  const t = e.touches ? e.touches[0] : e
  const rect = canvas.value.getBoundingClientRect()
  const x = (t.clientX - rect.left)
  const y = (t.clientY - rect.top)
  const n = findNodeAt(x,y)
  if(n && n.id !== currentNode){
    // check edge exists
    const possible = edges.some(([a,b]) => (a===currentNode && b===n.id) || (a===n.id && b===currentNode))
    if(possible){ visitedEdges.add(edgeKey(currentNode, n.id)); currentNode = n.id; draw(); }
  }
}

function onTouchEnd(e){ currentNode = null }

onMounted(()=>{
  const el = canvas.value
  ctx = el.getContext('2d')
  function resize(){ el.width = window.innerWidth; el.height = window.innerHeight - 64; draw() }
  window.addEventListener('resize', resize)
  resize()
  el.addEventListener('touchstart', onTouchStart)
  el.addEventListener('touchmove', onTouchMove)
  el.addEventListener('touchend', onTouchEnd)
  // load demo by default
  loadDemo()
})

onBeforeUnmount(()=>{
  const el = canvas.value
  if(el){ el.removeEventListener('touchstart', onTouchStart); el.removeEventListener('touchmove', onTouchMove); el.removeEventListener('touchend', onTouchEnd) }
})
</script>

<style scoped>
button{padding:8px 12px;border-radius:6px;border:1px solid #cbd5e1;background:#fff}
</style>
```

---

## 最后说明

- 这个仓库为最小可行版本（MVP），方便你快速跑通前后端联调、移动触控交互和后端求解逻辑。
- 后续我可以帮你：增加关卡生成器、更好的一键部署脚本、用户系统、动画回放、或把前端迁移为小程序（uni-app）。

如果你准备好了，我可以：
- ✅ 把上面代码拆成真实文件并打包为 zip（提供下载）
- ✅ 或者我现在直接把某个文件内容一步步发到你这儿（你可以复制粘贴运行）

你想要哪一种？

