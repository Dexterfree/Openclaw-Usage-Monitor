@echo off
REM OpenCLAW 快速开始脚本
REM 自动设置日志记录并启动监控

setlocal

echo ========================================
echo   OpenCLAW Token Usage Monitor
echo   快速开始
echo ========================================
echo.

REM 创建日志目录
if not exist "logs" mkdir logs
echo [OK] 日志目录已创建: .\logs

REM 生成示例数据
python generate_sample_data.py
echo.

echo ========================================
echo   监控器已就绪！
echo ========================================
echo.
echo 使用以下命令查看统计:
echo.
echo   1. 实时监控
echo      start_monitor realtime
echo.
echo   2. 每日报表
echo      start_monitor daily
echo.
echo   3. 详细细分
echo      start_monitor detailed
echo.
echo   4. 或者直接使用
echo      openclaw-monitor --view daily --log-path ./logs
echo.
pause

endlocal
