FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn pyyaml openai
COPY . .
EXPOSE 8010
CMD ["python3", "server.py"]
