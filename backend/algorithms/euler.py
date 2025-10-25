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