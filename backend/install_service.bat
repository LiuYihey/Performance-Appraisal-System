@echo off
REM 安装后端为 Windows 服务
REM 需要安装 NSSM (Non-Sucking Service Manager)

set NSSM_PATH=C:\nssm\nssm.exe
set PYTHON_PATH=C:\Program Files\AutoClaw\resources\python\python.exe
set BACKEND_PATH=C:\perf-system\backend
set SERVICE_NAME=PerfSystemBackend

REM 安装服务
%NSSM_PATH% install %SERVICE_NAME% "%PYTHON_PATH%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
%NSSM_PATH% set %SERVICE_NAME% AppDirectory %BACKEND_PATH%
%NSSM_PATH% set %SERVICE_NAME% DisplayName "绩效管理系统后端"
%NSSM_PATH% set %SERVICE_NAME% Description "绩效管理系统 FastAPI 后端服务"
%NSSM_PATH% set %SERVICE_NAME% Start SERVICE_AUTO_START
%NSSM_PATH% set %SERVICE_NAME% AppStdout %BACKEND_PATH%\service.log
%NSSM_PATH% set %SERVICE_NAME% AppStderr %BACKEND_PATH%\service_error.log

echo 服务安装完成！
echo 启动服务: net start %SERVICE_NAME%
echo 停止服务: net stop %SERVICE_NAME%
echo 卸载服务: %NSSM_PATH% remove %SERVICE_NAME% confirm
