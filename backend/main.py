import random
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Tuple, Optional
from fastapi.middleware.cors import CORSMiddleware

# --- Use find_euler_path for the /solve endpoint ---
from algorithms.euler import find_euler_path

# 新增导入
from algorithms.euler import find_next_step
from collections import defaultdict
from generate_graph import generate_eulerian_graph_data

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


# --- Use simple GraphInput for /solve ---
class GraphInput(BaseModel):
    nodes: List[int]
    edges: List[Tuple[int, int]]


# 新增：提示请求体
class HintInput(BaseModel):
    nodes: List[int]
    edges: List[Tuple[int, int]]
    visitedEdges: List[str]  # 形如 ["1-2","2-3"]
    pathEndpoint: Optional[int] = None  # 当前端点，或空


@app.get("/generate")
def generate_demo():
    # Keep the simple triangle demo (Circuit)
    nodes = [1, 2, 3]
    edges = [(1, 2), (2, 3), (3, 1)]
    return {"nodes": nodes, "edges": edges}


# --- V V V --- Strictly Verified Fixed Levels (10 per difficulty, solvable, no parallel edges) --- V V V ---
# LEVELS = {
#     "easy": [
#         # 1. Triangle (Circuit)
#         {"nodes": [1, 2, 3], "edges": [(1, 2), (2, 3), (3, 1)]},
#         # 2. Square (Circuit)
#         {"nodes": [1, 2, 3, 4], "edges": [(1, 2), (2, 3), (3, 4), (4, 1)]},
#         # 3. Pentagon (Circuit)
#         {"nodes": [1, 2, 3, 4, 5], "edges": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 1)]},
#         # 4. Square + 1 Diagonal (Path: 1, 3 are odd)
#         {"nodes": [1, 2, 3, 4], "edges": [(1, 2), (2, 3), (3, 4), (4, 1), (1, 3)]},
#         # 5. "House" or Pentagon + Chord (Path: 1, 3 are odd)
#         {"nodes": [1, 2, 3, 4, 5], "edges": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 1), (1, 3)]},
#         # 6. Envelope (Square + 2 Diagonals) (Circuit)
#         {"nodes": [1, 2, 3, 4], "edges": [(1, 2), (2, 3), (3, 4), (4, 1), (1, 3), (2, 4)]},
#         # 7. Hexagon (Circuit)
#         {"nodes": [1, 2, 3, 4, 5, 6], "edges": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1)]},
#         # 8. Prism Graph (Triangle Base) (Circuit)
#         {"nodes": [1, 2, 3, 4, 5, 6], "edges": [(1,2),(2,3),(3,1),(4,5),(5,6),(6,4),(1,4),(2,5),(3,6)]},
#         # 9. Octagon (Circuit)
#         {"nodes": [1, 2, 3, 4, 5, 6, 7, 8], "edges": [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,1)]},
#         # 10. Simple Path Graph (Path: 1, 5 are odd)
#         {"nodes": [1, 2, 3, 4, 5], "edges": [(1, 2), (2, 3), (3, 4), (4, 5)]},
#     ],
#     "medium": [
#         # 1. K4 (Complete graph on 4 vertices) (Circuit)
#         {"nodes": [1, 2, 3, 4], "edges": [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]},
#         # 2. Hexagon + 1 Long Diagonal (Circuit)
#         {"nodes": [1, 2, 3, 4, 5, 6], "edges": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1), (1, 4)]},
#         # 3. Pentagon + Star inside (Circuit)
#         {"nodes": [1, 2, 3, 4, 5], "edges": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 1), (1, 3), (3, 5), (5, 2), (2, 4), (4, 1)]},
#         # 4. Hexagon + 2 Non-intersecting Short Diagonals (Path: 1, 4 are odd)
#         {"nodes": [1, 2, 3, 4, 5, 6], "edges": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1), (1, 3), (4, 6)]},
#         # 5. Cube Graph (Circuit)
#         {"nodes": [1, 2, 3, 4, 5, 6, 7, 8], "edges": [(1,2),(2,3),(3,4),(4,1),(5,6),(6,7),(7,8),(8,5),(1,5),(2,6),(3,7),(4,8)]},
#         # 6. Hexagon + 2 Intersecting Long Diagonals (Circuit)
#         {"nodes": [1, 2, 3, 4, 5, 6], "edges": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1), (1, 4), (2, 5)]},
#         # 7. Heptagon (7-gon) + 1 Chord (Path: 1, 4 are odd)
#         {"nodes": [1, 2, 3, 4, 5, 6, 7], "edges": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 1), (1, 4)]},
#         # 8. K5 minus one edge (Path: 4, 5 are odd)
#         {"nodes": [1, 2, 3, 4, 5], "edges": [(1,2),(1,3),(1,4),(1,5),(2,3),(2,4),(2,5),(3,4),(3,5)]}, # Removed (4,5)
#         # 9. Octagon + 2 Non-intersecting Diagonals (Circuit)
#         {"nodes": [1, 2, 3, 4, 5, 6, 7, 8], "edges": [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,1),(1,3),(5,7)]},
#         # 10. Double Square Connected (Circuit)
#         {"nodes": [1, 2, 3, 4, 5, 6, 7], "edges": [(1,2),(2,3),(3,4),(4,1),(1,5),(5,6),(6,7),(7,1)]}, # Node 1 is shared center
#     ],
#     "hard": [
#         # 1. K5 (Complete Graph on 5 vertices) (Circuit)
#         {"nodes": [1, 2, 3, 4, 5], "edges": [(1,2),(1,3),(1,4),(1,5),(2,3),(2,4),(2,5),(3,4),(3,5),(4,5)]},
#         # 2. Octagon + 4 "Short" Diagonals (Circuit)
#         {"nodes": [1, 2, 3, 4, 5, 6, 7, 8], "edges": [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,1),(1,3),(3,5),(5,7),(7,1)]},
#         # 3. Petersen Graph minus one vertex (Path: 1, 4, 7 are neighbors of removed 10)
#         {"nodes": [1,2,3,4,5,6,7,8,9], "edges": [(1,2),(2,3),(3,4),(4,5),(5,1),(1,6),(2,7),(3,8),(4,9),(5,6),(6,8),(7,9),(8,5),(9,7)]}, # Removed 10 and edges (4,10)(5,10)(9,10) -> Path
#         # 4. Heptagon (7-gon) + Star inside (Circuit)
#         {"nodes": [1, 2, 3, 4, 5, 6, 7], "edges": [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,1),(1,3),(3,5),(5,7),(7,2),(2,4),(4,6),(6,1)]},
#         # 5. Nonagon (9-gon) (Circuit)
#         {"nodes": [1,2,3,4,5,6,7,8,9], "edges": [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(9,1)]},
#         # 6. K6 minus a path of length 3 (Circuit)
#         {"nodes": [1,2,3,4,5,6], "edges": [(1,3),(1,4),(1,5),(1,6),(2,4),(2,5),(2,6),(3,4),(3,5),(3,6),(4,5),(4,6),(5,6)]}, # Removed (1,2), (2,3)
#         # 7. Decagon (10-gon) (Circuit)
#         {"nodes": [1,2,3,4,5,6,7,8,9,10], "edges": [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(9,10),(10,1)]},
#         # 8. Octagon + 4 Crossing Diagonals (Circuit)
#         {"nodes": [1, 2, 3, 4, 5, 6, 7, 8], "edges": [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,1),(1,5),(2,6),(3,7),(4,8)]},
#         # 9. K7 minus a cycle of length 3 (Circuit)
#         {"nodes": [1,2,3,4,5,6,7], "edges": [(1,4),(1,5),(1,6),(1,7),(2,4),(2,5),(2,6),(2,7),(3,4),(3,5),(3,6),(3,7),(4,5),(4,6),(4,7),(5,6),(5,7),(6,7)]}, # Removed (1,2),(2,3),(3,1)
#         # 10. Wheel Graph W7 (Center + 7-gon) (Circuit)
#         {"nodes": [1,2,3,4,5,6,7,8], "edges": [(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,1),(8,1),(8,2),(8,3),(8,4),(8,5),(8,6),(8,7)]}, # Node 8 is center
#     ],
# }
# --- ^ ^ ^ --- Verified Fixed Levels End --- ^ ^ ^ ---


@app.get("/level")
def get_level(difficulty: str = "easy", index: int = 1):
    print(f"Generating level for difficulty: {difficulty}, index: {index}")
    # 定义各难度的节点数范围
    difficulty_ranges = {
        "easy": (4, 6),      # 4-6个节点
        "medium": (5, 7),    # 5-7个节点  
        "hard": (6, 9)       # 6-9个节点
    }
    # 获取当前难度的范围，默认easy
    min_nodes, max_nodes = difficulty_ranges.get(difficulty, (4, 6))
    # 在范围内随机选择节点数（确保每次相同index生成相同的图）
    random.seed(index)  # 用index作为种子，保证相同index生成相同关卡
    num_nodes = random.randint(min_nodes, max_nodes)
    if difficulty == "easy":
        graph = generate_eulerian_graph_data(num_nodes=num_nodes, edge_prob=0.3, type="circuit")
    elif difficulty == "medium":
        graph = generate_eulerian_graph_data(num_nodes=num_nodes, edge_prob=0.5, type="circuit")
    else:  # hard
        graph = generate_eulerian_graph_data(num_nodes=num_nodes, edge_prob=0.7, type="path")
    return graph


@app.post("/solve")
def solve_graph(graph: GraphInput):
    # Use find_euler_path to get the full path
    path = find_euler_path(graph.nodes, graph.edges)

    if path is None:
        # Verify if the graph data itself is flawed (should not happen with fixed levels)
        d = defaultdict(int)
        valid_nodes_in_edges = set()
        for u, v in graph.edges:
            if u in graph.nodes and v in graph.nodes:
                d[u] += 1
                d[v] += 1
                valid_nodes_in_edges.add(u)
                valid_nodes_in_edges.add(v)
        odd_nodes = [
            n for n in graph.nodes if n in valid_nodes_in_edges and d[n] % 2 == 1
        ]
        print(
            f"CRITICAL: find_euler_path failed on fixed level! Odd nodes: {len(odd_nodes)}"
        )
        return {"ok": False, "error": f"关卡设计错误 (奇数点: {len(odd_nodes)})"}

    # Return the full path
    return {"ok": True, "path": path}


@app.post("/hint")
def hint_next_step(payload: HintInput):
    move, err = find_next_step(
        payload.nodes, payload.edges, payload.visitedEdges, payload.pathEndpoint
    )
    if err:
        return {"ok": False, "message": err}
    if not move:
        return {"ok": False, "message": "无法给出下一步"}
    return {"ok": True, "move": move}  # [from, to]
