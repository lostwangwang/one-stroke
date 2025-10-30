# 阶段1：构建Vue项目
FROM node:18-alpine as builder
WORKDIR /app
# 复制package.json和package-lock.json
COPY package*.json ./
# 安装依赖
RUN npm install
# 复制项目代码
COPY . .
# 构建生产环境代码（输出到dist目录）
RUN npm run build

# 阶段2：部署到Nginx
FROM nginx:alpine
# 从构建阶段复制dist目录到Nginx的静态文件目录
COPY --from=builder /app/dist /usr/share/nginx/html
# 复制自定义Nginx配置（可选，解决路由刷新404问题）
COPY nginx.conf /etc/nginx/conf.d/default.conf
# 暴露80端口
EXPOSE 80
# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]