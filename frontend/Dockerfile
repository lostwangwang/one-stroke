# 阶段 1：用 Nginx 作为基础镜像（轻量且适合托管静态文件）
FROM nginx:alpine

# 将打包后的 dist 文件夹复制到 Nginx 的默认静态文件目录
COPY dist/ /usr/share/nginx/html/

# （可选）替换 Nginx 配置文件，解决 Vue 路由 history 模式刷新 404 问题
# 在 frontend 目录下创建 nginx.conf（内容见下方），再复制到容器
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露 80 端口（Nginx 默认端口）
EXPOSE 80

# 启动 Nginx（前台运行，避免容器退出）
CMD ["nginx", "-g", "daemon off;"]