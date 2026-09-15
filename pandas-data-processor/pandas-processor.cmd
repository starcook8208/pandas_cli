@echo off
setlocal
set "PANDAS_PROCESSOR_PYTHON=%~dp0.venv\Scripts\python.exe"
if exist "%PANDAS_PROCESSOR_PYTHON%" goto run
set "PANDAS_PROCESSOR_PYTHON=%~dp0..\.venv\Scripts\python.exe"
if exist "%PANDAS_PROCESSOR_PYTHON%" goto run
echo {"status":"error","error":{"code":"DEPENDENCY_ERROR","file":null,"sheet":null,"column":null,"message":"Project Python environment not found. Follow README installation instructions."}}
exit /b 3
:run
"%PANDAS_PROCESSOR_PYTHON%" -I "%~dp0scripts\launch.py" %*
exit /b %errorlevel%
