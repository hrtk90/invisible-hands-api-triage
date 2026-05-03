@echo off
setlocal

python -m pip install -r requirements.txt
if errorlevel 1 goto failed

python -m pytest -q
if errorlevel 1 goto failed

python -m py_compile app.py
if errorlevel 1 goto failed

python -m py_compile src\__init__.py
if errorlevel 1 goto failed

python -m py_compile src\vam_api.py
if errorlevel 1 goto failed

python -m py_compile src\scoring.py
if errorlevel 1 goto failed

python -m py_compile src\archival_routes.py
if errorlevel 1 goto failed

python -m py_compile src\utils.py
if errorlevel 1 goto failed

echo.
echo Setup, tests, and compile checks completed successfully.
pause
exit /b 0

:failed
echo.
echo Setup or verification failed. Review the output above.
pause
exit /b 1
