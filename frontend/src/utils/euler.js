// client-side simple validator and helper for edges
export function isEulerPossible(nodes, edges) {
  const deg = new Map();
  edges.forEach(([a, b]) => {
    deg.set(a, (deg.get(a) || 0) + 1);
    deg.set(b, (deg.get(b) || 0) + 1);
  });
  let odd = 0;
  for (const v of deg.values()) if (v % 2) odd++;
  return odd === 0 || odd === 2;
}
