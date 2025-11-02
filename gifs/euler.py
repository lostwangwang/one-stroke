import networkx as nx
import matplotlib.pyplot as plt
import imageio
import os

# ====== 1. 定义图 ======
G = nx.Graph()
edges = [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3)]
G.add_edges_from(edges)

# ====== 2. 节点位置和帧准备 ======
pos = nx.spring_layout(G, seed=42)
os.makedirs("frames", exist_ok=True)
frames = []


# ====== 3. 绘制函数 ======
def draw_graph(path_edges, current_edge=None, filename="frame.png"):
    plt.figure(figsize=(5, 5))

    # 所有节点默认浅蓝
    nx.draw_networkx_nodes(G, pos, node_color="lightblue", node_size=800)
    nx.draw_networkx_labels(G, pos)

    # 所有边默认灰色
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(), edge_color="lightgray", width=2)

    # 已走过的边蓝色
    if path_edges:
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color="blue", width=4)

    # 当前尝试的边橙色
    if current_edge:
        nx.draw_networkx_edges(
            G, pos, edgelist=[current_edge], edge_color="orange", width=4
        )

    # 已走过的节点高亮
    used_nodes = set()
    for u, v in path_edges:
        used_nodes.add(u)
        used_nodes.add(v)
    nx.draw_networkx_nodes(
        G, pos, nodelist=list(used_nodes), node_color="green", node_size=800
    )

    # 标注路径顺序
    for idx, (u, v) in enumerate(path_edges):
        x = (pos[u][0] + pos[v][0]) / 2
        y = (pos[u][1] + pos[v][1]) / 2
        plt.text(
            x,
            y + 0.05,
            str(idx + 1),
            fontsize=12,
            fontweight="bold",
            color="red",
            ha="center",
        )

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    frames.append(filename)


# ====== 4. 暴力搜索欧拉路径 ======
def find_euler_path(path_edges):
    if len(path_edges) == len(G.edges()):
        draw_graph(path_edges)
        return True

    used_edges = set(path_edges)
    for u, v in G.edges():
        if (u, v) not in used_edges and (v, u) not in used_edges:
            draw_graph(path_edges, current_edge=(u, v))
            if find_euler_path(path_edges + [(u, v)]):
                return True
    return False


# ====== 5. 执行搜索 ======
find_euler_path([])

# ====== 6. 生成 GIF ======
images = []
for f in frames:
    images.append(imageio.v2.imread(f))

# duration: 每帧停留 2 秒，loop=0 无限循环
imageio.mimsave("euler_path_brute_force.gif", images, duration=2, loop=0)

print("GIF 已生成: euler_path_brute_force.gif")
