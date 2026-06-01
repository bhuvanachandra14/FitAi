#!/bin/bash

# Function to kill processes on exit
cleanup() {
    echo "Stopping servers..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit
}

trap cleanup SIGINT

echo "Starting Backend..."
cd backend
source venv/bin/activate
uvicorn main:app --reload > ../server.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "Starting Frontend..."
cd frontend
npm run dev -- --host &
FRONTEND_PID=$!
cd ..

echo "Both servers are running."
echo "Backend: http://127.0.0.1:8000/docs"
echo "Frontend: http://localhost:5173"

wait
