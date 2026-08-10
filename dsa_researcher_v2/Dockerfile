FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY tools/ ./tools/
COPY dsa_mcp/ ./dsa_mcp/

EXPOSE 8110

CMD ["python", "-m", "dsa_mcp.server", "--port", "8110"]
