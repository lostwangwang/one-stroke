from collections import defaultdict
from typing import List, Tuple, Optional, Dict, Set

# --- 原始的 "找完整路径" 算法 (保留) ---
def find_euler_path(nodes, edges):
    graph = defaultdict(list)
    if not edges: return []
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)

    odd = [n for n in nodes if n in graph and len(graph[n]) % 2 == 1]
    fallback_start = None
    if nodes:
        for n in nodes:
            if n in graph and graph[n]: 
                fallback_start = n
                break
    start = odd[0] if odd else (fallback_start if fallback_start else None)
    if start is None: return [] 

    stack = [start]
    path = []
    local_graph = {k: list(v) for k, v in graph.items()}
    while stack:
        v = stack[-1]
        if v in local_graph and local_graph[v]:
            u = local_graph[v].pop()
            try:
                if v in local_graph[u]: # Check if u still exists in graph
                    local_graph[u].remove(v)
            except (KeyError, ValueError):
                pass 
            stack.append(u)
        else:
            path.append(stack.pop())
    return path[::-1]

# --- V V V --- 恢复的 "智能提示" 算法 (检查桥) --- V V V ---

def _dfs_count(graph: Dict[int, List[int]], start_node: int, visited_nodes: Set[int]) -> int:
    """
    辅助函数：使用 DFS 计算连通分量的大小
    """
    count = 1
    visited_nodes.add(start_node)
    # 确保 start_node 在图中存在
    if start_node in graph:
        for neighbor in graph[start_node]:
            if neighbor not in visited_nodes:
                count += _dfs_count(graph, neighbor, visited_nodes)
    return count

def find_next_step(nodes: List[int], 
                   edges: List[Tuple[int, int]], 
                   visitedEdges: List[str], 
                   pathEndpoint: Optional[int]) -> Tuple[Optional[Tuple[int, int]], Optional[str]]:
    
    # 1. 建立完整的图
    full_graph = defaultdict(list)
    all_edges_set: Set[Tuple[int, int]] = set()
    for a, b in edges:
        full_graph[a].append(b)
        full_graph[b].append(a)
        all_edges_set.add(tuple(sorted((a, b))))

    # 2. 建立已访问边的集合
    visited_set: Set[Tuple[int, int]] = set()
    # 【修复】需要记录每条边被访问了多少次 (处理重复边)
    visited_count = defaultdict(int) 
    for key in visitedEdges:
        try:
            a, b = map(int, key.split('-'))
            edge_tuple = tuple(sorted((a, b)))
            visited_set.add(edge_tuple) # 仍然用 set 快速检查是否存在
            visited_count[edge_tuple] += 1 # 计数
        except ValueError:
            pass

    # 3. 确定起点
    start_node = pathEndpoint
    if start_node is None: 
        odd_nodes = [n for n in nodes if n in full_graph and len(full_graph[n]) % 2 == 1]
        # 检查图是否可解（理论上关卡生成已保证）
        if len(odd_nodes) not in (0, 2):
            return None, "此图无解 (奇数点错误)"
        
        fallback_start = None
        if nodes:
            for n in nodes:
                 if n in full_graph and full_graph[n]: 
                      fallback_start = n
                      break
                      
        start_node = odd_nodes[0] if odd_nodes else (fallback_start if fallback_start else None)
        if start_node is None:
            return None, "空关卡或无有效起点"

    # 4. 找到所有 "未完全访问" 的下一步
    valid_moves = []
    # 【修复】需要知道图中每条边总共出现了多少次
    total_edge_count = defaultdict(int)
    for a,b in edges:
        total_edge_count[tuple(sorted((a,b)))] += 1
        
    if start_node in full_graph:
        for neighbor in full_graph[start_node]:
            edge_tuple = tuple(sorted((start_node, neighbor)))
            # 如果这条边还没被访问过，或者访问次数小于总次数
            if visited_count[edge_tuple] < total_edge_count[edge_tuple]:
                valid_moves.append(neighbor)

    # 5. 检查是否卡住或通关
    if not valid_moves:
        # 【修复】检查是否所有边都被访问了 *正确的次数*
        all_visited_correctly = True
        for edge_tuple, count in total_edge_count.items():
            if visited_count[edge_tuple] != count:
                all_visited_correctly = False
                break
                
        if all_visited_correctly:
            return None, "🎉 恭喜通关！"
        else:
            return None, "你似乎走进了死胡同，请重置"

    # 6. 检查“桥”
    # 6a. 建立只包含 "剩余边" 的图 (考虑重复边)
    remaining_graph = defaultdict(list)
    remaining_edge_counts = defaultdict(int) # 需要追踪剩余数量
    for a, b in edges:
         edge_tuple = tuple(sorted((a,b)))
         remaining_count = total_edge_count[edge_tuple] - visited_count[edge_tuple]
         if remaining_count > 0 and edge_tuple not in remaining_edge_counts: # 只添加一次邻接关系
              remaining_graph[a].append(b)
              remaining_graph[b].append(a)
              remaining_edge_counts[edge_tuple] = remaining_count # 记录剩余次数

    # 6b. 遍历可走的下一步，找非桥
    non_bridge_moves = []
    bridge_moves = []

    # 统计当前连通分量的大小 (只考虑有剩余边的节点)
    nodes_in_remaining_graph = set(remaining_graph.keys())
    if not nodes_in_remaining_graph: # 没有剩余边了
         if all_visited_correctly: return None, "🎉 恭喜通关！"
         else: return None, "内部错误：无剩余边但未通关"
         
    # 找到一个有效的起始节点进行DFS
    dfs_start_node = start_node if start_node in nodes_in_remaining_graph else next(iter(nodes_in_remaining_graph))
    
    visited_nodes_before = set()
    initial_component_size = _dfs_count(remaining_graph, dfs_start_node, visited_nodes_before)


    for next_node in valid_moves:
        edge_tuple = tuple(sorted((start_node, next_node)))
        
        # 6c. 如果这是唯一出路，必须走
        # 【修复】检查 start_node 在 remaining_graph 中的有效邻居数量
        valid_remaining_neighbors = 0
        if start_node in remaining_graph:
             for neighbor in remaining_graph[start_node]:
                  check_tuple = tuple(sorted((start_node, neighbor)))
                  if remaining_edge_counts[check_tuple] > 0:
                       valid_remaining_neighbors += 1

        if valid_remaining_neighbors == 1:
            return (start_node, next_node), None

        # 6d. 模拟移除这条边
        remaining_graph[start_node].remove(next_node)
        remaining_graph[next_node].remove(start_node)
        remaining_edge_counts[edge_tuple] -= 1 # 减少计数
        # 如果这条边彻底没了，更新邻接表
        should_re_add_adjacency = True
        if remaining_edge_counts[edge_tuple] == 0:
            # 检查是否还有其他边连接这两个节点（理论上不会，因为我们只处理非重复邻接）
             pass # 邻接关系已移除
        else:
             # 如果还有重复边，需要把邻接关系加回去，否则DFS会出错
             remaining_graph[start_node].append(next_node)
             remaining_graph[next_node].append(start_node)
             should_re_add_adjacency = False


        # 6e. 检查连通性
        visited_nodes_after = set()
        # 需要找到一个新的有效起始点，因为start_node可能因移除边而孤立
        new_dfs_start = start_node if start_node in remaining_graph and remaining_graph[start_node] else next_node if next_node in remaining_graph and remaining_graph[next_node] else None
        
        component_size_after = 0
        if new_dfs_start:
             component_size_after = _dfs_count(remaining_graph, new_dfs_start, visited_nodes_after)
        
        # is_bridge = component_size_after < initial_component_size # 简单检查
        # 更严格的检查：next_node 是否仍在 start_node 的连通分量里？
        is_bridge = (new_dfs_start is None) or (next_node not in visited_nodes_after and start_node in visited_nodes_after)

        # 6f. 恢复图
        if should_re_add_adjacency: # 只有当邻接关系被彻底移除时才加回
            remaining_graph[start_node].append(next_node)
            remaining_graph[next_node].append(start_node)
        remaining_edge_counts[edge_tuple] += 1 # 恢复计数
        
        if not is_bridge:
            non_bridge_moves.append(next_node)
        else:
            bridge_moves.append(next_node)

    # 7. 优先走非桥
    if non_bridge_moves:
        return (start_node, non_bridge_moves[0]), None
    elif bridge_moves: # 否则走桥
        return (start_node, bridge_moves[0]), None
    else: # 理论上不应该到这里
         return None, "内部错误：无法确定下一步"

# --- ^ ^ ^ --- "智能提示" 算法结束 --- ^ ^ ^ ---