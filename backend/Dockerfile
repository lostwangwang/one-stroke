# 阶段 1：用 Python 官方镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 复制项目代码到容器
COPY . .

# 暴露 FastAPI 运行端口（默认 8000）
EXPOSE 8000

# 启动命令（用 uvicorn 运行，允许外部访问，worker 数根据服务器配置调整）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]