@echo off
title YouTube Automation - 4 Agent Pipeline
color 0A

echo.
echo ===============================================================
echo   YouTube Automation - 4 Agent Pipeline Launcher
echo ===============================================================
echo.

:: Find Python
set PYTHON_EXE=

:: Check common locations
if exist "C:\Users\hp\AppData\Local\Programs\Python\Python311\python.exe" (
    set PYTHON_EXE=C:\Users\hp\AppData\Local\Programs\Python\Python311\python.exe
    goto :found_python
)
if exist "C:\Users\hp\AppData\Local\Programs\Python\Python310\python.exe" (
    set PYTHON_EXE=C:\Users\hp\AppData\Local\Programs\Python\Python310\python.exe
    goto :found_python
)
if exist "C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe" (
    set PYTHON_EXE=C:\Users\hp\AppData\Local\Programs\Python\Python312\python.exe
    goto :found_python
)
if exist "C:\Python311\python.exe" (
    set PYTHON_EXE=C:\Python311\python.exe
    goto :found_python
)
if exist "C:\Python310\python.exe" (
    set PYTHON_EXE=C:\Python310\python.exe
    goto :found_python
)
if exist "C:\Users\hp\Anaconda3\python.exe" (
    set PYTHON_EXE=C:\Users\hp\Anaconda3\python.exe
    goto :found_python
)
if exist "C:\ProgramData\Anaconda3\python.exe" (
    set PYTHON_EXE=C:\ProgramData\Anaconda3\python.exe
    goto :found_python
)

:: Try python3 in PATH
python3 --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON_EXE=python3
    goto :found_python
)

:: Try python in PATH
python --version >nul 2>&1
if %errorlevel% == 0 (
    set PYTHON_EXE=python
    goto :found_python
)

echo [ERROR] Python not found! Please install Python from https://python.org
echo         Or right-click agent1_analyzer.py and select "Open with Python"
pause
exit /b 1

:found_python
echo [OK] Python found: %PYTHON_EXE%
%PYTHON_EXE% --version
echo.

:: Find Git
set GIT_EXE=
for /f "delims=" %%i in ('where git 2^>nul') do set GIT_EXE=%%i
if not defined GIT_EXE (
    if exist "C:\Program Files\Git\bin\git.exe" set GIT_EXE=C:\Program Files\Git\bin\git.exe
)
if defined GIT_EXE (
    echo [OK] Git found: %GIT_EXE%
) else (
    echo [WARN] Git not found - Agent 2 push will need manual setup
    echo        Download from: https://git-scm.com/download/win
)

echo.
echo ---------------------------------------------------------------
echo   Choose which agent to run:
echo ---------------------------------------------------------------
echo.
echo   [1] Agent 1 - Project Analyzer     (analysis_report.json)
echo   [2] Agent 2 - Code Fixer + GitHub Push
echo   [3] Agent 3 - Render Deployer + Health Check
echo   [4] Agent 4 - Live Tester
echo   [A] Run ALL agents in sequence (Master Orchestrator)
echo   [Q] Quit
echo.
set /p CHOICE="Enter your choice (1/2/3/4/A/Q): "

if /i "%CHOICE%"=="1" goto :run_agent1
if /i "%CHOICE%"=="2" goto :run_agent2
if /i "%CHOICE%"=="3" goto :run_agent3
if /i "%CHOICE%"=="4" goto :run_agent4
if /i "%CHOICE%"=="A" goto :run_all
if /i "%CHOICE%"=="Q" goto :quit

echo Invalid choice. Please run again.
pause
exit /b

:run_agent1
echo.
echo [RUNNING] Agent 1 - Project Analyzer...
echo.
"%PYTHON_EXE%" agent1_analyzer.py
echo.
echo Agent 1 completed! Check analysis_report.json for details.
pause
goto :eof

:run_agent2
echo.
echo [RUNNING] Agent 2 - Code Fixer + GitHub Pusher...
echo.
"%PYTHON_EXE%" agent2_github_pusher.py
echo.
pause
goto :eof

:run_agent3
echo.
set /p SERVICE_URL="Enter your Render URL (e.g. https://youtube-automation.onrender.com) or press Enter to skip: "
echo [RUNNING] Agent 3 - Render Deployer...
echo.
if defined SERVICE_URL (
    "%PYTHON_EXE%" agent3_deployer.py %SERVICE_URL%
) else (
    "%PYTHON_EXE%" agent3_deployer.py
)
echo.
pause
goto :eof

:run_agent4
echo.
set /p TEST_URL="Enter your live URL to test (e.g. https://youtube-automation.onrender.com): "
echo [RUNNING] Agent 4 - Live Tester...
echo.
"%PYTHON_EXE%" agent4_tester.py %TEST_URL%
echo.
echo Test report saved to test_report.json
pause
goto :eof

:run_all
echo.
echo [RUNNING] Master Orchestrator - All 4 Agents...
echo.
"%PYTHON_EXE%" run_all_agents.py
echo.
pause
goto :eof

:quit
echo Goodbye!
exit /b 0
