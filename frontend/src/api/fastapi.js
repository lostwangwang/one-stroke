import axios from "axios";
const api = axios.create({ baseURL: "http://localhost:8000" });
export const fetchDemo = () => api.get("/generate").then((r) => r.data);
export const fetchLevel = (difficulty = "easy", index = 1) =>
  api.get(`/level`, { params: { difficulty, index } }).then((r) => r.data);
export const solveGraph = (graph) =>
  api.post("/solve", graph).then((r) => r.data);
