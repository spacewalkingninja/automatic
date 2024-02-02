:: --------------------------------------------------------------------------------------------------------------
:: Do not make any changes to this file. Instead, create a shortcut to this file and add needed arguments there.
:: --------------------------------------------------------------------------------------------------------------

@echo off

:: USER PATH
:: %~dp0 = C:\Users\[username]Desota\Desota_Models\DeUrlCruncher\executables\windows
for %%a in ("%~dp0\..\..\..\..\..") do set "user_path=%%~fa"
for %%a in ("%~dp0\..\..\..\..\..\..") do set "test_path=%%~fa"
for %%a in ("%UserProfile%\..") do set "test1_path=%%~fa"

:: GET USER PATH
IF "%test1_path%" EQU "C:\Users" GOTO TEST1_PASSED
IF "%test1_path%" EQU "C:\users" GOTO TEST1_PASSED
IF "%test1_path%" EQU "c:\Users" GOTO TEST1_PASSED
IF "%test1_path%" EQU "c:\users" GOTO TEST1_PASSED

IF "%test_path%" EQU "C:\Users" GOTO TEST_PASSED
IF "%test_path%" EQU "C:\users" GOTO TEST_PASSED
IF "%test_path%" EQU "c:\Users" GOTO TEST_PASSED
IF "%test_path%" EQU "c:\users" GOTO TEST_PASSED

ECHO %fail%Error: Can't Resolve Request!%ansi_end%
ECHO %fail%[ DEV TIP ] Run Command Without Admin Rights!%ansi_end%
PAUSE
exit
:TEST1_PASSED
set user_path=%UserProfile%
:TEST_PASSED
:: Model VARS

set model_name=automatic
set model_path_basepath=Desota\Desota_Models\%model_name%
set python_main_basepath=%model_path_basepath%\main.py

set model_path=%user_path%\%model_path_basepath%
set python_main=%user_path%\%python_main_basepath%

:: - Miniconda (virtual environment) Vars
set conda_basepath=\Desota\Desota_Models\miniconda3\condabin\conda.bat
set model_env_basepath=%model_path_basepath%\env

:: Miniconda (virtual environment) Vars
set conda_path=%user_path%\%conda_basepath%
set model_env=%user_path%\%model_env_basepath%
set pip_reqs=%user_path%\%pip_reqs_basepath%

set pyenv=%model_env%\python

set SKIP_VENV=1
::call %conda_path% activate %model_env% >NUL 2>NUL

if not defined PYTHON (set PYTHON=%pyenv%)
if not defined VENV_DIR (set "VENV_DIR=%~dp0%venv")
set ERROR_REPORTING=FALSE
mkdir tmp 2>NUL

%PYTHON% -c "" >tmp/stdout.txt 2>tmp/stderr.txt
if %ERRORLEVEL% == 0 goto :check_pip
echo Cannot launch python
goto :show_stdout_stderr

:check_pip
%PYTHON% -mpip --help >tmp/stdout.txt 2>tmp/stderr.txt
if %ERRORLEVEL% == 0 goto :start_venv
if "%PIP_INSTALLER_LOCATION%" == "" goto :show_stdout_stderr
%PYTHON% "%PIP_INSTALLER_LOCATION%" >tmp/stdout.txt 2>tmp/stderr.txt
if %ERRORLEVEL% == 0 goto :start_venv
echo Cannot install pip
goto :show_stdout_stderr

:start_venv
if ["%VENV_DIR%"] == ["-"] goto :skip_venv
if ["%SKIP_VENV%"] == ["1"] goto :skip_venv

dir "%VENV_DIR%\Scripts\Python.exe" >tmp/stdout.txt 2>tmp/stderr.txt
if %ERRORLEVEL% == 0 goto :activate_venv

for /f "delims=" %%i in ('CALL %PYTHON% -c "import sys; print(sys.executable)"') do set PYTHON_FULLNAME="%%i"
echo Using python: %PYTHON_FULLNAME%
echo Creating VENV: %VENV_DIR%
%PYTHON_FULLNAME% -m venv "%VENV_DIR%" >tmp/stdout.txt 2>tmp/stderr.txt
if %ERRORLEVEL% == 0 goto :activate_venv
echo Failed creating VENV: "%VENV_DIR%"
goto :show_stdout_stderr

:activate_venv
set PYTHON="%VENV_DIR%\Scripts\Python.exe"
echo Using VENV: %VENV_DIR%

:skip_venv
if [%ACCELERATE%] == ["True"] goto :accelerate
goto :launch

:accelerate
set ACCELERATE="%VENV_DIR%\Scripts\accelerate.exe"
if EXIST %ACCELERATE% goto :accelerate_launch

:launch
%PYTHON% launch.py %*
pause
exit /b

:accelerate_launch
echo Using accelerate
%ACCELERATE% launch --num_cpu_threads_per_process=6 launch.py %*
pause
exit /b

:show_stdout_stderr

echo.
echo exit code: %errorlevel%

for /f %%i in ("tmp\stdout.txt") do set size=%%~zi
if %size% equ 0 goto :show_stderr
echo.
echo stdout:
type tmp\stdout.txt

:show_stderr
for /f %%i in ("tmp\stderr.txt") do set size=%%~zi
if %size% equ 0 goto :show_stderr
echo.
echo stderr:
type tmp\stderr.txt

:endofscript

echo.
echo Launch Failed
pause
