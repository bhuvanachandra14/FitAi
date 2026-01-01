#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Building Frontend..."
npm install --prefix frontend
npm run build --prefix frontend

echo "Installing Backend Dependencies..."
pip install --upgrade pip
pip install cmake
pip install -r backend/requirements.txt --no-cache-dir
