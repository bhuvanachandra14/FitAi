# Stage 1: Build React Frontend
FROM node:20-alpine as frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Build Python Backend
FROM python:3.9-slim

WORKDIR /app

# Set environment variable to limit compilation to 1 core (Fixes OOM)
ENV CMAKE_BUILD_PARALLEL_LEVEL=1

# Install system dependencies
# Added --fix-missing and clean to handle repo errors
RUN apt-get update --fix-missing && apt-get install -y \
    cmake \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir --upgrade pip wheel setuptools cmake && \
    # Install dlib first explicitly to manage the build
    pip install --no-cache-dir dlib && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend assets from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set working directory to backend
WORKDIR /app/backend

# Expose port
EXPOSE 10000

# Start command
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:10000", "--timeout", "120"]
