#!/bin/bash

echo "正在启动失物招领系统..."
echo ""

# 检查是否安装了Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未检测到Python，请先安装Python 3.7+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "检查并安装依赖..."
pip install -r requirements.txt

# 运行应用
echo ""
echo "================================"
echo "失物招领系统启动中..."
echo "访问地址: http://localhost:5000"
echo "管理后台: http://localhost:5000/admin"
echo "默认管理员账号: admin / admin123"
echo "按 Ctrl+C 停止服务器"
echo "================================"
echo ""

python app.py

