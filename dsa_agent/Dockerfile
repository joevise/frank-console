FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/dsa_agent/

# 设置 PYTHONPATH 确保能找到 dsa_agent 包
ENV PYTHONPATH=/app

EXPOSE 8120

CMD ["python", "-m", "dsa_agent.api.server"]
