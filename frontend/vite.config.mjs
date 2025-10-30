import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: { 
    port: 5174,
    allowedHosts: [
      'localhost', // 保留本地访问
      'catechistic-unproficiently-billy.ngrok-free.dev' // 添加 ngrok 生成的域名
    ]},
});
