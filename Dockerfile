# ===== 构建阶段：安装依赖 =====
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
# 使用国内 pip 镜像加速构建
RUN pip install --no-cache-dir --prefix=/install \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r requirements.txt

# ===== 运行阶段：精简镜像 =====
FROM python:3.11-slim AS runtime
WORKDIR /app

# 拷贝依赖
COPY --from=builder /install /usr/local

# 拷贝应用代码
COPY app ./app
COPY README.md GOAL.md PLAN.md ./

ENV PYTHONUNBUFFERED=1
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=5 --start-period=20s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
