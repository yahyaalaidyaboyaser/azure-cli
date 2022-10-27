@echo off
SetLocal EnableDelayedExpansion

REM Double colon :: should not be used in parentheses blocks, so we use REM.
REM See https://stackoverflow.com/a/12407934/2199657

echo build a msi installer using local cli sources and python executables. You need to have curl.exe, unzip.exe and msbuild.exe available under PATH
echo.

set "PATH=%PATH%;%ProgramFiles%\Git\bin;%ProgramFiles%\Git\usr\bin;C:\Program Files (x86)\Git\bin;C:\Program Files (x86)\Microsoft Visual Studio\2019\Enterprise\MSBuild\Current\Bin"

if "%CLI_VERSION%"=="" (
    echo Please set the CLI_VERSION environment variable, e.g. 2.0.13
    goto ERROR
)
if %BLOB_SAS%=="" (
    echo Please set the BLOB_SAS environment variable
    goto ERROR
)
set PYTHON_VERSION=3.10.5
set SPYTHON_VERSION=3.10.22251.3

set WIX_DOWNLOAD_URL="https://azurecliprod.blob.core.windows.net/msi/wix310-binaries-mirror.zip"
@REM windows-http only support amd64
set PYTHON_DOWNLOAD_URL="https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip"
set NUGET_DOWNLOAD_URL="https://dist.nuget.org/win-x86-commandline/v6.2.1/nuget.exe"
set BASE_MISC_URL=https://azurecliedge.blob.core.windows.net/saw
set WINDOWS_HTTP_FILENAME=windows_http-0.22.203.1-cp310-cp310-win_amd64.whl
set SPYTHON_FILENAME=Microsoft.Internal.SPython.win32.%SPYTHON_VERSION%.nupkg

REM https://pip.pypa.io/en/stable/installation/#get-pip-py
set GET_PIP_DOWNLOAD_URL="https://bootstrap.pypa.io/get-pip.py"

REM Set up the output directory and temp. directories
echo Cleaning previous build artifacts...
set OUTPUT_DIR=%~dp0..\out
if exist %OUTPUT_DIR% rmdir /s /q %OUTPUT_DIR%
mkdir %OUTPUT_DIR%

set ARTIFACTS_DIR=%~dp0..\artifacts
mkdir %ARTIFACTS_DIR%
set TEMP_SCRATCH_FOLDER=%ARTIFACTS_DIR%\cli_scratch
set BUILDING_DIR=%ARTIFACTS_DIR%\cli
set WIX_DIR=%ARTIFACTS_DIR%\wix
set PYTHON_DIR=%ARTIFACTS_DIR%\Python
set SPYTHON_DIR=%ARTIFACTS_DIR%\SPython
set SPYTHON_EXE=%SPYTHON_DIR%\Microsoft.Internal.SPython.win32.%SPYTHON_VERSION%\tools\python.exe
set SPYTHON_LIB=%SPYTHON_DIR%\Microsoft.Internal.SPython.win32.%SPYTHON_VERSION%\tools\Lib
set NUGET_DIR=%ARTIFACTS_DIR%\Nuget
set MISC_DIR=%ARTIFACTS_DIR%\misc

set REPO_ROOT=%~dp0..\..\..

REM reset nuget dir
if not exist %NUGET_DIR% (
    mkdir %NUGET_DIR%
    pushd %NUGET_DIR%
    curl --output nuget.exe %NUGET_DOWNLOAD_URL%
    popd
)

REM download wheel
if not exist %MISC_DIR% (
    mkdir %MISC_DIR%
    pushd %MISC_DIR%
    curl --output %WINDOWS_HTTP_FILENAME% %BASE_MISC_URL%/%WINDOWS_HTTP_FILENAME%?%BLOB_SAS%
    curl --output %SPYTHON_FILENAME% %BASE_MISC_URL%/%SPYTHON_FILENAME%?%BLOB_SAS%
    popd
)

REM reset spython dir
if exist %SPYTHON_DIR% rmdir /s /q %SPYTHON_DIR%
if not exist %SPYTHON_DIR% (
    mkdir %SPYTHON_DIR%
    cd %SPYTHON_DIR%
    %NUGET_DIR%\nuget.exe install Microsoft.Internal.SPython.win32 -version %SPYTHON_VERSION% -Source %MISC_DIR%
)

REM reset working folders
if exist %BUILDING_DIR% rmdir /s /q %BUILDING_DIR%
REM rmdir always returns 0, so check folder's existence
if exist %BUILDING_DIR% (
    echo Failed to delete %BUILDING_DIR%.
    goto ERROR
)
mkdir %BUILDING_DIR%

if exist %TEMP_SCRATCH_FOLDER% rmdir /s /q %TEMP_SCRATCH_FOLDER%
if exist %TEMP_SCRATCH_FOLDER% (
    echo Failed to delete %TEMP_SCRATCH_FOLDER%.
    goto ERROR
)
mkdir %TEMP_SCRATCH_FOLDER%

if exist %REPO_ROOT%\privates (
    copy %REPO_ROOT%\privates\*.whl %TEMP_SCRATCH_FOLDER%
)

REM ensure wix is available
if exist %WIX_DIR% (
    echo Using existing Wix at %WIX_DIR%
)
if not exist %WIX_DIR% (
    mkdir %WIX_DIR%
    pushd %WIX_DIR%
    echo Downloading Wix.
    curl --output wix-archive.zip %WIX_DOWNLOAD_URL%
    unzip wix-archive.zip
    if %errorlevel% neq 0 goto ERROR
    del wix-archive.zip
    echo Wix downloaded and extracted successfully.
    popd
)

REM ensure Python is available
if exist %PYTHON_DIR% (
    echo Using existing Python at %PYTHON_DIR%
)
if not exist %PYTHON_DIR% (
    echo Setting up Python and pip
    mkdir %PYTHON_DIR%
    pushd %PYTHON_DIR%

    echo Downloading Python
    curl --output python-archive.zip %PYTHON_DOWNLOAD_URL%
    unzip python-archive.zip
    if %errorlevel% neq 0 goto ERROR
    del python-archive.zip
    echo Python downloaded and extracted successfully

    REM Delete _pth file so that Lib\site-packages is included in sys.path
    REM https://github.com/pypa/pip/issues/4207#issuecomment-297396913
    REM https://docs.python.org/3.10/using/windows.html#finding-modules
    del python*._pth

    echo Installing pip
    curl --output get-pip.py %GET_PIP_DOWNLOAD_URL%
    %PYTHON_DIR%\python.exe get-pip.py
    del get-pip.py
    echo Pip set up successful

    dir .
    popd
)
set PYTHON_EXE=%PYTHON_DIR%\python.exe

set CLI_SRC=%REPO_ROOT%\src
%PYTHON_EXE% -m pip install pycparser==2.18 --no-warn-script-location --force-reinstall --target %SPYTHON_LIB%
for %%a in (%CLI_SRC%\azure-cli %CLI_SRC%\azure-cli-core %CLI_SRC%\azure-cli-telemetry) do (
    pushd %%a
    %PYTHON_EXE% -m pip install --no-warn-script-location --no-cache-dir --no-deps -U .
    popd
)

copy %CLI_SRC%\azure-cli\requirements.py3.windows.txt %CLI_SRC%\azure-cli\requirements.py3.windows-spython.txt
pushd %CLI_SRC%\azure-cli\
    powershell -Command "(Get-Content requirements.py3.windows-spython.txt) -replace '^azure-cli-core==.*', '' | Out-File -encoding utf8 requirements.py3.windows-spython.txt"
    powershell -Command "(Get-Content requirements.py3.windows-spython.txt) -replace '^azure-cli-telemetry==.*', '' | Out-File -encoding utf8 requirements.py3.windows-spython.txt"
    powershell -Command "(Get-Content requirements.py3.windows-spython.txt) -replace '^azure-cli==.*', '' | Out-File -encoding utf8 requirements.py3.windows-spython.txt"
    echo setuptools==63.4.2 >> requirements.py3.windows-spython.txt
    echo multidict==6.0.2 >> requirements.py3.windows-spython.txt
popd

%PYTHON_EXE% -m pip install --no-warn-script-location --requirement %CLI_SRC%\azure-cli\requirements.py3.windows-spython.txt --target %SPYTHON_LIB%
rm %CLI_SRC%\azure-cli\requirements.py3.windows-spython.txt
%PYTHON_EXE% -m pip install "%MISC_DIR%\%WINDOWS_HTTP_FILENAME%" --no-warn-script-location --force-reinstall --target %SPYTHON_LIB%

@REM Install portalocker free version msal_extensions
%PYTHON_EXE% -m pip install https://github.com/AzureAD/microsoft-authentication-extensions-for-python/archive/optional-portalocker.zip --no-warn-script-location --ignore-installed --target %SPYTHON_LIB%

REM Remove forbidden packages in SPython. (remove requests after calling remove_unused_api_versions.py)
pushd %SPYTHON_LIB%
for /d %%G in (cffi*) do rmdir /s /q "%%G"
for /d %%G in (PyJWT*) do rmdir /s /q "%%G"
for /d %%G in (cryptography*) do rmdir /s /q "%%G"
for /d %%G in (portalocker*) do rmdir /s /q "%%G"
@REM PyWin32 related
for /d %%G in (pywin32*) do rmdir /s /q "%%G"
for /d %%G in (win32*) do rmdir /s /q "%%G"
rmdir /s /q pythonwin
rmdir /s /q adodbapi
rmdir /s /q isapi
popd

@REM --target is not compatible with namespace packages, as azure-cli, azure-cli-core, azure-cli=telemetry want to
@REM install into same folder. So I have to copy azure folder from standard python
mkdir %SPYTHON_LIB%\azure\cli
robocopy %PYTHON_DIR%\Lib\site-packages\azure\cli %SPYTHON_LIB%\azure\cli /s /NFL /NDL

robocopy %SPYTHON_DIR%\Microsoft.Internal.SPython.win32.%SPYTHON_VERSION%\tools %BUILDING_DIR% /s /NFL /NDL

REM Replace requests to winrequests
echo Replace requests to winrequests
pushd %BUILDING_DIR%\Lib\msrest
for %%a in ("pipeline\__init__.py" "universal_http\__init__.py" "universal_http\requests.py" "authentication.py" "pipeline\requests.py" "universal_http\async_requests.py" "pipeline\async_requests.py") do (
    powershell -Command "(Get-Content %%a) -replace '^import requests_oauthlib as oauth', '' | Out-File -encoding utf8 %%a"
    powershell -Command "(Get-Content %%a) -replace '^from requests', 'from azure.cli.core.vendored_sdks.winrequests' | Out-File -encoding utf8 %%a"
    powershell -Command "(Get-Content %%a) -replace '^import requests', 'import azure.cli.core.vendored_sdks.winrequests as requests' | Out-File -encoding utf8 %%a"
    powershell -Command "(Get-Content %%a) -replace '^from urllib3 import Retry', '' | Out-File -encoding utf8 %%a"
)
@REM Rebuild __pycache__
%BUILDING_DIR%\python.exe -m compileall .
popd
pushd %BUILDING_DIR%\Lib\msrestazure
for %%a in ("azure_exceptions.py") do (
    powershell -Command "(Get-Content %%a) -replace '^from requests', 'from azure.cli.core.vendored_sdks.winrequests' | Out-File -encoding utf8 %%a"
)
%BUILDING_DIR%\python.exe -m compileall .
popd
pushd %BUILDING_DIR%\Lib\azure\multiapi\storagev2\blob
for /R %%a in (*_download.py) do (
    powershell -Command "(Get-Content %%a) -replace '^import requests', 'import azure.cli.core.vendored_sdks.winrequests as requests' | Out-File -encoding utf8 %%a"
)
%BUILDING_DIR%\python.exe -m compileall .
popd

REM Remove cryptography
echo Remove cryptography
pushd %BUILDING_DIR%\Lib\azure\multiapi\storagev2
for /R %%a in (*encryption.py) do (
    powershell -Command "(Get-Content %%a) -replace '^from cryptography.*', '' | Out-File -encoding utf8 %%a"
)
%BUILDING_DIR%\python.exe -m compileall .
popd

%BUILDING_DIR%\python.exe -m azure.cli --version

if %errorlevel% neq 0 goto ERROR

pushd %BUILDING_DIR%
%BUILDING_DIR%\python.exe %~dp0\patch_models_v2.py
%BUILDING_DIR%\python.exe %~dp0\remove_unused_api_versions.py
popd

pushd %BUILDING_DIR%\Lib
for /d %%G in (requests*) do rmdir /s /q "%%G"
for /d %%G in (urllib3*) do rmdir /s /q "%%G"
popd

echo Creating the wbin (Windows binaries) folder that will be added to the path...
mkdir %BUILDING_DIR%\wbin
copy %REPO_ROOT%\build_scripts\windows\scripts\az_spython.cmd %BUILDING_DIR%\wbin\az.cmd
if %errorlevel% neq 0 goto ERROR
copy %REPO_ROOT%\build_scripts\windows\resources\CLI_LICENSE.rtf %BUILDING_DIR%
copy %REPO_ROOT%\build_scripts\windows\resources\ThirdPartyNotices.txt %BUILDING_DIR%
copy %REPO_ROOT%\NOTICE.txt %BUILDING_DIR%

REM Remove .py and only deploy .pyc files
pushd %BUILDING_DIR%\Lib
for /f %%f in ('dir /b /s *.pyc') do (
    set PARENT_DIR=%%~df%%~pf..
    echo !PARENT_DIR! | findstr /C:\Lib\site-packages\pip\ 1>nul
    if !errorlevel! neq  0 (
        REM Only take the file name without 'pyc' extension: e.g., (same below) __init__.cpython-310
        set FILENAME=%%~nf
        REM Truncate the '.cpython-310' postfix which is 12 chars long: __init__
        REM https://stackoverflow.com/a/636391/2199657
        set BASE_FILENAME=!FILENAME:~0,-12!
        REM __init__.pyc
        set pyc=!BASE_FILENAME!.pyc
        REM Delete ..\__init__.py
        del !PARENT_DIR!\!BASE_FILENAME!.py
        REM Copy to ..\__init__.pyc
        copy %%~f !PARENT_DIR!\!pyc! >nul
        REM Delete __init__.pyc
        del %%~f
    ) ELSE (
        echo --SKIP !PARENT_DIR! under pip
    )
)
popd

REM Remove __pycache__
echo remove pycache
for /d /r %BUILDING_DIR%\Lib\pip %%d in (__pycache__) do (
    if exist %%d rmdir /s /q "%%d"
)

REM Remove aio
echo remove aio
for /d /r %BUILDING_DIR%\Lib\site-packages\azure\mgmt %%d in (aio) do (
    if exist %%d rmdir /s /q "%%d"
)

REM Remove dist-info
echo remove dist-info
pushd %BUILDING_DIR%\Lib
for /d %%d in ("azure*.dist-info") do (
    if exist %%d rmdir /s /q "%%d"
)
popd

if %errorlevel% neq 0 goto ERROR

echo Building MSI...
msbuild /t:rebuild /p:Configuration=Release %REPO_ROOT%\build_scripts\windows\azure-cli.wixproj

if %errorlevel% neq 0 goto ERROR

start %OUTPUT_DIR%

goto END

:ERROR
echo Error occurred, please check the output for details.
exit /b 1

:END
exit /b 0
popd
