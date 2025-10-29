import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ====== Step 1: 构建图 ======
G = nx.Graph()
edges = [
    ('A', 'B'),
    ('A', 'C'),
    ('B', 'C'),
    ('C', 'D'),
    ('D', 'A')
]
G.add_edges_from(edges)

if nx.is_eulerian(G):
    path = list(nx.eulerian_circuit(G))
else:
    path = list(nx.eulerian_path(G))

print("欧拉路径：", path)

pos = nx.spring_layout(G, seed=42)

# ====== Step 2: 初始化绘图 ======
fig, ax = plt.subplots()
nx.draw(G, pos, with_labels=True, node_size=800, node_color="lightblue")

# ====== Step 3: 动画更新函数 ======
def update(frame):
    ax.clear()
    nx.draw(G, pos, with_labels=True, node_size=800, node_color="lightblue")
    nx.draw_networkx_edges(G, pos, edgelist=path[:frame+1], width=3, edge_color="red")
    if frame < len(path):
        u, v = path[frame]
        ax.set_title(f"Step {frame+1}: {u} → {v}")
    else:
        ax.set_title("✅ 完成！")

# ====== Step 4: 创建动画 ======
ani = animation.FuncAnimation(fig, update, frames=len(path), interval=1000, repeat=False)

# ====== Step 5: 导出 GIF ======
ani.save("euler_path.gif", writer="pillow", fps=1)
plt.close()
print("GIF 动画已保存为 euler_path.gif ✅")
