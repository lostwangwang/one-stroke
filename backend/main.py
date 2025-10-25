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

# 旧接口：返回一个简单 demo
@app.get('/generate')
def generate_demo():
    nodes = [1, 2, 3]
    edges = [(1, 2), (2, 3), (3, 1)]
    return {"nodes": nodes, "edges": edges}

# 新增：关卡库（静态示例，可扩展为算法生成）
LEVELS = {
    "easy": [
        {"nodes": [1, 2, 3], "edges": [(1, 2), (2, 3), (3, 1)]},
        {"nodes": [1, 2, 3, 4], "edges": [(1, 2), (2, 3), (3, 4), (4, 1)]},
        {"nodes": [1, 2, 3, 4, 5], "edges": [(1, 2), (2, 3), (3, 4), (4, 1), (2, 5), (3, 5)]},
    ],
    "medium": [
        {"nodes": [1, 2, 3, 4, 5, 6], "edges": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1), (1, 4)]},
        {"nodes": [1, 2, 3, 4, 5], "edges": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 1), (1, 3), (3, 5)]},
        {"nodes": [1, 2, 3, 4, 5, 6], "edges": [(1, 2), (2, 3), (3, 1), (3, 4), (4, 5), (5, 3), (2, 6), (5, 6)]},
    ],
    "hard": [
        # 8 点环 + 两条弦，产生 2 个奇点（欧拉路径）
        {"nodes": [1,2,3,4,5,6,7,8], "edges": [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,1),(2,5),(5,8)]},
        # 7 点环 + 两条共享端点的弦 => 2 奇点
        {"nodes": [1,2,3,4,5,6,7], "edges": [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,1),(1,4),(4,7)]},
        # 8 点环 + 对称弦（每点两次切换）=> 全偶（欧拉回路）
        {"nodes": [1,2,3,4,5,6,7,8], "edges": [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,1),(1,5),(2,6),(3,7),(4,8)]},
    ],
}

@app.get('/level')
def get_level(difficulty: str = "easy", index: int = 1):
    diff = difficulty.lower()
    if diff not in LEVELS:
        diff = "easy"
    levels = LEVELS[diff]
    # index 从 1 开始，循环取值
    i = (max(1, index) - 1) % len(levels)
    return levels[i]

@app.post('/solve')
def solve_graph(graph: GraphInput):
    path = find_euler_path(graph.nodes, graph.edges)
    if path is None:
        return {"ok": False, "error": "No Euler path"}
    return {"ok": True, "path": path}