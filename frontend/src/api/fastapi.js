import axios from "axios";
const api = axios.create({ baseURL: "/api" });
export const fetchDemo = () => api.get("/generate").then((r) => r.data);
export const fetchLevel = (difficulty, index = 1) =>
  api.get(`/level`, { params: { difficulty, index } }).then((r) => r.data);
export const solveGraph = (graph) =>
  api.post("/solve", graph).then((r) => r.data);

// 新增：下一步提示
export const hintNext = (payload) =>
  api.post("/hint", payload).then((r) => r.data);
