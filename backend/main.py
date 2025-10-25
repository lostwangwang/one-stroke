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