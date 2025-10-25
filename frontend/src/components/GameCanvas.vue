<template>
  <div style="flex: 1; display: flex; flex-direction: column">
    <canvas
      ref="canvas"
      style="flex: 1; background: #f6f8fa; touch-action: none"
    ></canvas>
    <div style="padding: 8px; display: flex; gap: 8px; justify-content: center">
      <button @click="loadDemo">加载示例</button>
      <button @click="askSolve">提示（后端求解）</button>
      <button @click="reset">重置</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";
import { fetchDemo, solveGraph } from "../api/fastapi";

const canvas = ref(null);
let ctx = null;
let nodes = [];
let edges = [];
let visitedEdges = new Set();
let currentNode = null;
let scale = 1;

function draw() {
  if (!ctx) return;
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height);
  // draw edges
  ctx.lineWidth = 6;
  edges.forEach(([a, b]) => {
    const na = nodes.find((n) => n.id === a);
    const nb = nodes.find((n) => n.id === b);
    const key = edgeKey(a, b);
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

function edgeKey(a, b) {
  return a < b ? `${a}-${b}` : `${b}-${a}`;
}

function reset() {
  visitedEdges.clear();
  currentNode = null;
  draw();
}

async function loadDemo() {
  const res = await fetchDemo();
  nodes = res.nodes.map((id, i) => ({
    id,
    x: 60 + i * 120,
    y: 120 + (i % 2) * 60,
  }));
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
  // animate solution
  const path = res.path;
  // transform path -> edges visited
  visitedEdges.clear();
  for (let i = 0; i < path.length - 1; i++)
    visitedEdges.add(edgeKey(path[i], path[i + 1]));
  draw();
}

function findNodeAt(x, y) {
  return nodes.find((n) => Math.hypot(n.x - x, n.y - y) < 24);
}

function onTouchStart(e) {
  e.preventDefault();
  const t = e.touches ? e.touches[0] : e;
  const rect = canvas.value.getBoundingClientRect();
  const x = t.clientX - rect.left;
  const y = t.clientY - rect.top;
  const n = findNodeAt(x, y);
  if (n) currentNode = n.id;
}

function onTouchMove(e) {
  if (!currentNode) return;
  e.preventDefault();
  const t = e.touches ? e.touches[0] : e;
  const rect = canvas.value.getBoundingClientRect();
  const x = t.clientX - rect.left;
  const y = t.clientY - rect.top;
  const n = findNodeAt(x, y);
  if (n && n.id !== currentNode) {
    // check edge exists
    const possible = edges.some(
      ([a, b]) =>
        (a === currentNode && b === n.id) || (a === n.id && b === currentNode)
    );
    if (possible) {
      visitedEdges.add(edgeKey(currentNode, n.id));
      currentNode = n.id;
      draw();
    }
  }
}

function onTouchEnd(e) {
  currentNode = null;
}

onMounted(() => {
  const el = canvas.value;
  ctx = el.getContext("2d");
  function resize() {
    el.width = window.innerWidth;
    el.height = window.innerHeight - 64;
    draw();
  }
  window.addEventListener("resize", resize);
  resize();
  el.addEventListener("touchstart", onTouchStart);
  el.addEventListener("touchmove", onTouchMove);
  el.addEventListener("touchend", onTouchEnd);
  // load demo by default
  loadDemo();
});

onBeforeUnmount(() => {
  const el = canvas.value;
  if (el) {
    el.removeEventListener("touchstart", onTouchStart);
    el.removeEventListener("touchmove", onTouchMove);
    el.removeEventListener("touchend", onTouchEnd);
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
</style>
