@echo off
echo 正在启动失物招领系统...
echo.

REM 检查是否安装了Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未检测到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate

REM 安装依赖
echo 检查并安装依赖...
pip install -r requirements.txt

REM 运行应用
echo.
echo ================================
echo 失物招领系统启动中...
echo 访问地址: http://localhost:5000
echo 管理后台: http://localhost:5000/admin
echo 默认管理员账号: admin / admin123
echo 按 Ctrl+C 停止服务器
echo ================================
echo.

python app.py

pause

