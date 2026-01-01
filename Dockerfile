# Stage 1: Build React Frontend
FROM node:20-alpine as frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Build Python Backend
FROM python:3.9
# Using full Python image (Debian based) which includes gcc, make, etc.

WORKDIR /app

# 1. Force Single-Core Build for dlib (Prevents OOM / Status 1 error)
ENV CMAKE_BUILD_PARALLEL_LEVEL=1

# 2. Update pip and install build tools via pip (Avoids apt-get errors)
# We use opencv-python-headless, so we don't need libgl1 via apt-get!
RUN pip install --no-cache-dir --upgrade pip wheel setuptools cmake

# 3. Install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

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
