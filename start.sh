#!/bin/bash
# 启动Python后端服务器
python chat.py &
PYTHON_PID=$!

# 启动React开发服务器
npm start &
REACT_PID=$!

# 等待用户按Ctrl+C
wait

# 清理进程
kill $PYTHON_PID
kill $REACT_PID