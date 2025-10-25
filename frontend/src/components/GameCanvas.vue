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
      <button @click="askSolve">提示（后端求解）</button>
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
let visitedEdges = new Set();
let currentNode = null;

const difficulty = ref("easy");
const levelIndex = ref(1);
const message = ref("");

function edgeKey(a, b) {
  return a < b ? `${a}-${b}` : `${b}-${a}`;
}

function layoutNodesCircle(ids) {
  const el = canvas.value;
  const cx = el.width / 2;
  const cy = el.height / 2;
  const r = Math.max(60, Math.min(el.width, el.height) / 2 - 80);
  const count = ids.length || 1;
  return ids.map((id, i) => {
    const ang = (i / count) * Math.PI * 2;
    const x = cx + r * Math.cos(ang);
    const y = cy + r * Math.sin(ang);
    return { id, x, y };
  });
}

function draw() {
  if (!ctx) return;
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height);
  // draw edges
  ctx.lineWidth = 6;
  edges.forEach(([a, b]) => {
    const na = nodes.find((n) => n.id === a);
    const nb = nodes.find((n) => n.id === b);
    const key = edgeKey(a, b);
    if (!na || !nb) return;
    ctx.beginPath();
    ctx.moveTo(na.x, na.y);
    ctx.lineTo(nb.x, nb.y);
    ctx.strokeStyle = visitedEdges.has(key) ? "#0b84ff" : "#cbd5e1";
    ctx.stroke();
  });
  // draw nodes
  nodes.forEach((n) => {
    ctx.beginPath();
    ctx.arc(n.x, n.y, 18, 0, Math.PI * 2);
    ctx.fillStyle = "#fff";
    ctx.fill();
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 2;
    ctx.stroke();
  });
}

function reset() {
  visitedEdges.clear();
  currentNode = null;
  message.value = "";
  draw();
}

async function loadDemo() {
  const res = await fetchDemo();
  nodes = layoutNodesCircle(res.nodes);
  edges = res.edges;
  reset();
}

async function loadCurrentLevel() {
  const res = await fetchLevel(difficulty.value, levelIndex.value);
  nodes = layoutNodesCircle(res.nodes);
  edges = res.edges;
  reset();
}

async function askSolve() {
  const graph = { nodes: nodes.map((n) => n.id), edges };
  const res = await solveGraph(graph);
  if (!res.ok) {
    alert(res.error || "无法求解");
    return;
  }
  const path = res.path;
  visitedEdges.clear();
  for (let i = 0; i < path.length - 1; i++) {
    visitedEdges.add(edgeKey(path[i], path[i + 1]));
  }
  draw();
  checkComplete();
}

function checkComplete() {
  if (edges.length && visitedEdges.size === edges.length) {
    message.value = "🎉 恭喜通关！";
  }
}

function findNodeAt(x, y) {
  return nodes.find((n) => Math.hypot(n.x - x, n.y - y) < 24);
}

function onPointerDown(e) {
  e.preventDefault();
  const t = e.touches ? e.touches[0] : e;
  const rect = canvas.value.getBoundingClientRect();
  const x = t.clientX - rect.left;
  const y = t.clientY - rect.top;
  const n = findNodeAt(x, y);
  if (n) currentNode = n.id;
}

function onPointerMove(e) {
  if (!currentNode) return;
  e.preventDefault();
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
      if (!visitedEdges.has(k)) {
        visitedEdges.add(k);
      }
      currentNode = n.id;
      draw();
      checkComplete();
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

onMounted(() => {
  const el = canvas.value;
  ctx = el.getContext("2d");
  function resize() {
    el.width = window.innerWidth;
    el.height = window.innerHeight - 112; // 留出控制条与提示的高度
    draw();
  }
  window.addEventListener("resize", resize);
  resize();
  // 支持触控与鼠标
  el.addEventListener("touchstart", onPointerDown);
  el.addEventListener("touchmove", onPointerMove);
  el.addEventListener("touchend", onPointerUp);
  el.addEventListener("mousedown", onPointerDown);
  el.addEventListener("mousemove", onPointerMove);
  el.addEventListener("mouseup", onPointerUp);
  // 默认加载第一关
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
