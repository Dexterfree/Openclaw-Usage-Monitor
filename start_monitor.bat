@echo off
REM OpenCLAW Token Usage Monitor - 启动脚本
REM 使用方法: start_monitor.bat [view] [log_path]

setlocal

REM 默认配置
set VIEW_MODE=%1
set LOG_PATH=%2

REM 如果没有提供视图模式，使用 realtime
if "%VIEW_MODE%"=="" set VIEW_MODE=realtime

REM 如果没有提供日志路径，使用当前目录下的 logs
if "%LOG_PATH%"=="" set LOG_PATH=.\logs

echo ========================================
echo   OpenCLAW Token Usage Monitor
echo ========================================
echo   View: %VIEW_MODE%
echo   Log Path: %LOG_PATH%
echo ========================================
echo.

REM 运行监控器
openclaw-monitor --view %VIEW_MODE% --log-path "%LOG_PATH%"

endlocal
