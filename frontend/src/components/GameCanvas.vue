<template>
  <div style="flex: 1; display: flex; flex-direction: column">
    <canvas
      ref="canvas"
      style="flex: 1; background: #f6f8fa; touch-action: none"
    ></canvas>

    <div style="padding: 8px; display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; border-top: 1px solid #e5e7eb;">
      <label style="display:flex; align-items:center; gap:6px">
        难度
        <select v-model="difficulty" @change="onChangeDifficulty" style="padding:6px; border-radius:6px; border:1px solid #cbd5e1">
          <option value="easy">简单</option>
          <option value="medium">中等</option>
          <option value="hard">困难</option>
        </select>
      </label>
      <span style="display:flex; align-items:center">关卡 {{ levelIndex }}</span>
      <button @click="prevLevel">上一关</button>
      <button @click="nextLevel">下一关</button>
      <button @click="askSolve">提示（显示答案）</button>
      <button @click="reset">重置</button>
      <button @click="loadDemo">加载示例</button>
    </div>

    <div v-if="message" style="padding:8px; text-align:center; color:#0b7a00; font-weight:600;">
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import { fetchDemo, fetchLevel, solveGraph } from "../api/fastapi";

const canvas = ref(null);
let ctx = null;
let nodes = [];
let edges = [];
let visitedEdges = [];
let currentNode = null;
let pathEndpoint = null;
let fullSolutionPath = [];
let hintInvalidated = false; // Simplified: No hintStepIndex needed for full solve

const difficulty = ref("easy");
const levelIndex = ref(1);
const message = ref("");

function edgeKey(a, b) {
  return a < b ? `${a}-${b}` : `${b}-${a}`;
}

function layoutNodesCircle(ids) {
  const el = canvas.value;
  if (!el || !el.width || !el.height || el.width <= 0 || el.height <= 0) {
    return [];
  }
  const cx = el.width / 2;
  const cy = el.height / 2;
  const r = Math.max(60, Math.min(el.width, el.height) / 2 - 50);
  const count = ids.length || 1;
  return ids.map((id, i) => {
    const ang = (i / count) * Math.PI * 2 - Math.PI / 2;
    const x = cx + r * Math.cos(ang);
    const y = cy + r * Math.sin(ang);
    return { id, x, y };
  });
}

function draw() {
  if (!ctx) return;
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height);

  ctx.lineWidth = 6;
  edges.forEach(([a, b]) => {
    const na = nodes.find((n) => n.id === a);
    const nb = nodes.find((n) => n.id === b);
    const key = edgeKey(a, b);
    if (!na || !nb) return;
    ctx.beginPath();
    ctx.moveTo(na.x, na.y);
    ctx.lineTo(nb.x, nb.y);
    ctx.strokeStyle = visitedEdges.find(v => v.key === key) ? "#0b84ff" : "#cbd5e1";
    ctx.stroke();
  });

  nodes.forEach((n) => {
    ctx.beginPath();
    ctx.arc(n.x, n.y, 18, 0, Math.PI * 2);
    ctx.fillStyle = "#fff";
    ctx.fill();
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 2;
    ctx.stroke();
  });

  visitedEdges.forEach((visited, index) => {
    const seqNum = index + 1;
    const { key, from, to } = visited;
    const na = nodes.find((n) => n.id === from);
    const nb = nodes.find((n) => n.id === to);
    if (!na || !nb) return;
    const midX = (na.x + nb.x) / 2;
    const midY = (na.y + nb.y) / 2;
    const offsetDistance = 15;
    let vecX = nb.x - na.x;
    let vecY = nb.y - na.y;
    const len = Math.hypot(vecX, vecY);
    let normX = 0; let normY = 0;
    if (len > 0) { normX = -vecY / len; normY = vecX / len; }
    const numX = midX + normX * offsetDistance;
    const numY = midY + normY * offsetDistance;

    ctx.fillStyle = "#0b84ff";
    ctx.font = "bold 15px Arial";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(seqNum.toString(), numX, numY);

    const nodeRadius = 18;
    const arrowLength = 12;
    const arrowAngle = Math.PI / 6;
    const angle = Math.atan2(nb.y - na.y, nb.x - na.x);
    const endX = nb.x - nodeRadius * Math.cos(angle);
    const endY = nb.y - nodeRadius * Math.sin(angle);
    ctx.beginPath();
    ctx.moveTo(endX, endY);
    ctx.lineTo( endX - arrowLength * Math.cos(angle - arrowAngle), endY - arrowLength * Math.sin(angle - arrowAngle));
    ctx.moveTo(endX, endY);
    ctx.lineTo( endX - arrowLength * Math.cos(angle + arrowAngle), endY - arrowLength * Math.sin(angle + arrowAngle));
    ctx.strokeStyle = "#0b84ff";
    ctx.lineWidth = 3;
    ctx.stroke();
  });
}

function reset() {
  visitedEdges.length = 0;
  currentNode = null;
  pathEndpoint = null;
  fullSolutionPath.length = 0;
  hintInvalidated = false;
  message.value = "";
  draw();
}

async function loadDemo() {
  try {
    const res = await fetchDemo();
    fullSolutionPath.length = 0;
    hintInvalidated = false;
    nodes = layoutNodesCircle(res.nodes); // Use Circle for demo
    edges = res.edges;
    reset();
  } catch (err) {
    message.value = "加载示例失败，请检查后端服务。";
  }
}

async function loadCurrentLevel() {
  try {
    const res = await fetchLevel(difficulty.value, levelIndex.value);
    fullSolutionPath.length = 0;
    hintInvalidated = false;
    nodes = layoutNodesCircle(res.nodes); // Use Circle for levels
    edges = res.edges;
    reset();
  } catch (err) {
    message.value = "加载关卡失败，请检查后端服务。";
  }
}

async function askSolve() {
  message.value = "";

  if (fullSolutionPath.length === 0) {
    try {
      const payload = { nodes: nodes.map(n => n.id), edges }; // Prepare payload
      console.log("向后端发送 /solve 请求:", payload); // Log request payload
      const res = await solveGraph(payload);
      console.log("从后端收到 /solve 响应:", res); // Log response

      if (!res.ok || !res.path || res.path.length < 1) { // Path can be length 1 if only 1 node
        message.value = res.error || "无法求解";
        return;
      }
      fullSolutionPath = res.path;
    } catch (err) {
      // --- V V V Added detailed error logging V V V ---
      console.error("求解器调用失败:", err); // Log the actual error object
      if (err.response) {
        console.error("后端响应数据:", err.response.data);
        console.error("后端响应状态:", err.response.status);
      } else if (err.request) {
        console.error("请求已发出但无响应:", err.request);
      } else {
        console.error("请求设置错误:", err.message);
      }
      // --- ^ ^ ^ Logging added ^ ^ ^ ---
      message.value = "提示功能连接失败，请检查后端。";
      return;
    }
  }

  visitedEdges.length = 0;

  // Check if fullSolutionPath is valid before iterating
  if (!fullSolutionPath || fullSolutionPath.length < 1) {
       message.value = "获取的路径无效";
       return;
  }

  // Handle single-node case (no edges to draw)
  if (fullSolutionPath.length == 1) {
       pathEndpoint = fullSolutionPath[0];
       hintInvalidated = true;
       draw(); // Draw just the nodes
       checkComplete(); // Should ideally show success if edges.length is 0
       return;
  }


  for (let i = 0; i < fullSolutionPath.length - 1; i++) {
    const startNode = fullSolutionPath[i];
    const endNode = fullSolutionPath[i+1];
    const key = edgeKey(startNode, endNode);
    visitedEdges.push({ key: key, from: startNode, to: endNode });
  }

  pathEndpoint = fullSolutionPath[fullSolutionPath.length - 1];
  hintInvalidated = true;

  draw();
  checkComplete();
}


function checkComplete() {
  if (edges && edges.length >= 0) { // Allow 0 edges for single node graphs
      let allEdgesVisited = true;
      const visitedCounts = visitedEdges.reduce((acc, v) => {
          acc[v.key] = (acc[v.key] || 0) + 1;
          return acc;
      }, {});

      const totalCounts = edges.reduce((acc, e) => {
           const k = edgeKey(e[0], e[1]);
           acc[k] = (acc[k] || 0) + 1;
           return acc;
      }, {});

      // Check if total edge count matches visited edge count
      if(visitedEdges.length !== edges.length){
           allEdgesVisited = false;
      } else {
           // Verify counts for each unique edge key
           for (const key in totalCounts) {
               if (visitedCounts[key] !== totalCounts[key]) {
                   allEdgesVisited = false;
                   break;
               }
           }
           if (Object.keys(visitedCounts).length !== Object.keys(totalCounts).length) {
               allEdgesVisited = false;
           }
      }


      if (allEdgesVisited) {
          message.value = "🎉 恭喜通关！";
      }
  }
}


function findNodeAt(x, y) {
  return nodes.find((n) => Math.hypot(n.x - x, n.y - y) < 50);
}

function onPointerDown(e) {
  e.preventDefault();
  const t = e.touches ? e.touches[0] : e;
  const rect = canvas.value.getBoundingClientRect();
  const x = t.clientX - rect.left;
  const y = t.clientY - rect.top;
  const n = findNodeAt(x, y);

  if (!n) return;
  message.value = "";

  if (visitedEdges.length === 0) {
      hintInvalidated = true;
  }

  if (visitedEdges.length === 0) {
    currentNode = n.id;
    pathEndpoint = n.id;
  } else if (n.id === pathEndpoint) {
    currentNode = n.id;
  }
}

function onPointerMove(e) {
  if (!currentNode) return;
  e.preventDefault();
  hintInvalidated = true;

  const t = e.touches ? e.touches[0] : e;
  const rect = canvas.value.getBoundingClientRect();
  const x = t.clientX - rect.left;
  const y = t.clientY - rect.top;
  const n = findNodeAt(x, y);

  if (n && n.id !== currentNode) {
    const possible = edges.some(
      ([a, b]) => (a === currentNode && b === n.id) || (a === n.id && b === currentNode)
    );

    if (possible) {
      const k = edgeKey(currentNode, n.id);

      const drawnCount = visitedEdges.filter(v => v.key === k).length;
      const totalCount = edges.filter(e => edgeKey(e[0], e[1]) === k).length;

      if (drawnCount < totalCount) {
        visitedEdges.push({ key: k, from: currentNode, to: n.id });
        currentNode = n.id;
        pathEndpoint = n.id;
        draw();
        checkComplete();
      }
    }
  }
}

function onPointerUp() {
  currentNode = null;
}

function prevLevel() {
  levelIndex.value = Math.max(1, levelIndex.value - 1);
  loadCurrentLevel();
}
function nextLevel() {
  levelIndex.value += 1;
  loadCurrentLevel();
}
function onChangeDifficulty() {
  levelIndex.value = 1;
  loadCurrentLevel();
}

let resizeHandler = null;

onMounted(() => {
  const el = canvas.value;
  ctx = el.getContext("2d");

  resizeHandler = () => {
    const w = window.innerWidth;
    const h = Math.max(200, window.innerHeight - 112);

    if (el.width !== w || el.height !== h) {
      el.width = w;
      el.height = h;

      if (nodes.length > 0) {
        nodes = layoutNodesCircle(nodes.map(n => n.id));
        draw();
      } else {
        draw();
      }
    } else {
      draw();
    }
  }

  window.addEventListener("resize", resizeHandler);
  resizeHandler();

  el.addEventListener("touchstart", onPointerDown, { passive: false });
  el.addEventListener("touchmove", onPointerMove, { passive: false });
  el.addEventListener("touchend", onPointerUp);
  el.addEventListener("mousedown", onPointerDown);
  el.addEventListener("mousemove", onPointerMove);
  el.addEventListener("mouseup", onPointerUp);
  el.addEventListener("mouseleave", onPointerUp);

  loadCurrentLevel();
});

onBeforeUnmount(() => {
  const el = canvas.value;
  if (el) {
    el.removeEventListener("touchstart", onPointerDown);
    el.removeEventListener("touchmove", onPointerMove);
    el.removeEventListener("touchend", onPointerUp);
    el.removeEventListener("mousedown", onPointerDown);
    el.removeEventListener("mousemove", onPointerMove);
    el.removeEventListener("mouseup", onPointerUp);
    el.removeEventListener("mouseleave", onPointerUp);
  }
  if (resizeHandler) {
    window.removeEventListener("resize", resizeHandler);
  }
});
</script>

<style scoped>
button {
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  background: #fff;
}
select {
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  background: #fff;
}
</style>