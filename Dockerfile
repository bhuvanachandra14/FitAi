# Stage 1: Build React Frontend
FROM node:20-alpine as frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Build Python Backend
FROM python:3.9-slim-bullseye

WORKDIR /app

# Ensure single-core build for dlib (Memory safety)
ENV CMAKE_BUILD_PARALLEL_LEVEL=1

# Install system dependencies
# 1. rm -rf lists to fix "Exit 100" (Corrupt cache)
# 2. Install build-essential and blas for dlib compilation
RUN rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend assets
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

WORKDIR /app/backend

# Expose port
EXPOSE 10000

# Start command
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:10000", "--timeout", "120"]
