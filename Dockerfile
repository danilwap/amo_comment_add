# ---- Base image ----
FROM python:3.11-slim

# ---- System deps ----
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*





# ---- Workdir ----
WORKDIR /app

# ---- Copy dependencies ----
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy project ----
COPY . .
COPY .env .env

# ---- Expose port ----
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1


# ---- Gunicorn + Uvicorn старт ----
CMD ["gunicorn", "src.app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120"]
