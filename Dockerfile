FROM python:3.12-slim
WORKDIR /app
ENV PYTHONIOENCODING=utf-8
COPY . .
CMD ["python", "-m", "indicguard.benchmark"]
