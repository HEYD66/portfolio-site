@echo off
REM 设置控制台编码为UTF-8
chcp 65001 >nul

REM 应用配置
set APP_PORT=10008
set VENV_ACTIVATE=venv\Scripts\activate.bat
set PID_FILE=app.pid
set LOG_FILE=app.log
set WIN_REQ_FILE=%TEMP%\portfolio_requirements_windows.txt

REM 显示中文菜单
:menu
echo =
:menu_loop
echo 个人作品展示网站 启动脚本
set choice=0
set /p choice=请选择操作：1.前台启动 2.后台启动 3.查看状态 4.停止 5.退出 输入(1-5): 

if "%choice%"=="1" goto start_foreground
if "%choice%"=="2" goto start_background
if "%choice%"=="3" goto check_status
if "%choice%"=="4" goto stop_background
if "%choice%"=="5" goto exit_script

REM 无效选项处理
echo 无效选项，请重新输入。
goto menu_loop

REM 检查Python环境
:check_python
REM 检查Python是否安装
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到Python。请先安装Python 3.7或更高版本。
    pause
    exit /b 1
)

REM 检查pip是否可用
python -m pip --version >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: pip不可用。请尝试更新Python或手动安装pip。
    pause
    exit /b 1
)

REM 检查虚拟环境是否存在
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo 错误: 创建虚拟环境失败。
        pause
        exit /b 1
    )
)

REM 激活虚拟环境并安装依赖
call %VENV_ACTIVATE%
python -m pip install --upgrade pip >nul 2>nul

REM gunicorn用于Linux生产部署，Windows本地启动不需要，过滤后再安装
findstr /V /I /B /C:"gunicorn" requirements.txt > "%WIN_REQ_FILE%"
pip install -r "%WIN_REQ_FILE%" >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 安装依赖失败。
    pause
    exit /b 1
)
del "%WIN_REQ_FILE%" >nul 2>nul

REM 退出虚拟环境
deactivate

exit /b 0

REM 前台启动应用
:start_foreground
echo 正在前台启动应用...
echo 应用将在 http://127.0.0.1:%APP_PORT% 运行
echo 按 Ctrl+C 停止应用

REM 检查环境
call :check_python
if %errorlevel% neq 0 goto menu

REM 启动Flask应用
call %VENV_ACTIVATE%
python app.py --port %APP_PORT%

REM 恢复命令提示符
if %errorlevel% neq 0 (
    echo 应用启动失败。
    pause
    exit /b 1
)

echo 应用已停止
pause
goto menu

REM 后台启动应用
:start_background
echo 正在后台启动应用...

REM 检查环境
call :check_python
if %errorlevel% neq 0 goto menu

REM 检查是否已有后台进程
if exist %PID_FILE% (
    set /p existing_pid=<"%PID_FILE%"
    tasklist /fi "PID eq %existing_pid%" | findstr "python.exe" >nul 2>nul
    if %errorlevel% equ 0 (
        echo 错误: 应用已在后台运行，PID: %existing_pid%
        pause
        goto menu
    ) else (
        del %PID_FILE% >nul 2>nul
    )
)

REM 启动应用到后台
call %VENV_ACTIVATE%
start /b "Portfolio" python app.py --port %APP_PORT% > %LOG_FILE% 2>&1

REM 等待应用启动
ping -n 2 127.0.0.1 >nul

REM 获取进程ID并保存到PID文件
for /f %%i in ('powershell -NoProfile -Command "$p = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*app.py --port %APP_PORT%*' } | Sort-Object ProcessId -Descending | Select-Object -First 1; if ($p) { $p.ProcessId }"') do (
    echo %%i > %PID_FILE%
)

echo 应用已在后台启动
if exist %PID_FILE% (
    set /p pid=<"%PID_FILE%"
    echo PID: %pid%
    echo 日志文件: %LOG_FILE%
)
echo 访问地址: http://127.0.0.1:%APP_PORT%
pause
goto menu

REM 查看应用状态
:check_status
echo 检查应用状态...

if not exist %PID_FILE% (
    echo 应用未在后台运行。
) else (
    set /p pid=<"%PID_FILE%"
    tasklist /fi "PID eq %pid%" | findstr "python.exe" >nul 2>nul
    if %errorlevel% equ 0 (
        echo 应用正在后台运行：
        echo PID: %pid%
        echo 访问地址: http://127.0.0.1:%APP_PORT%
    ) else (
        echo 应用已停止，清理PID文件。
        del %PID_FILE% >nul 2>nul
        del %LOG_FILE% >nul 2>nul
    )
)
pause
goto menu

REM 停止应用
:stop_background
echo 正在停止应用...

if not exist %PID_FILE% (
    echo 应用未在后台运行。
) else (
    set /p pid=<"%PID_FILE%"
    tasklist /fi "PID eq %pid%" | findstr "python.exe" >nul 2>nul
    if %errorlevel% equ 0 (
        taskkill /f /pid %pid% >nul 2>nul
        echo 应用已成功停止，PID: %pid%
    ) else (
        echo 应用已停止，清理PID文件。
    )
    del %PID_FILE% >nul 2>nul
    del %LOG_FILE% >nul 2>nul
)
pause
goto menu

REM 退出脚本
:exit_script
echo 感谢使用！
pause
exit /b 0
