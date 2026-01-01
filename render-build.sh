#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Building Frontend..."
npm install --prefix frontend
npm run build --prefix frontend

echo "Installing Backend Dependencies..."
export CMAKE_BUILD_PARALLEL_LEVEL=1
pip install --upgrade pip
pip install wheel setuptools
pip install cmake
pip install -r backend/requirements.txt --no-cache-dir
