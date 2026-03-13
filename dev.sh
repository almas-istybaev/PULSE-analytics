#!/bin/bash
# Запуск Pulse в режиме разработки
# Использование: ./dev.sh

set -e

echo "🚀 Запуск Pulse Development Servers..."

# Backend
echo "⚡ Запуск FastAPI backend на http://localhost:8000"
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Frontend
echo "⚡ Запуск Vite frontend на http://localhost:5173"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Pulse запущен!"
echo "   Frontend:  http://localhost:5173"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/api/docs"
echo ""
echo "Нажмите Ctrl+C для остановки..."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Остановлен.'" INT TERM
wait
