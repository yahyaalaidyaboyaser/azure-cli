::
:: Microsoft Azure CLI - Windows Installer - Author file components script
:: Copyright (C) Microsoft Corporation. All Rights Reserved.
::
@IF EXIST "%~dp0\..\python.exe" (
  SET AZ_INSTALLER=MSI
  SET IS_SPYTHON=true
  "%~dp0\..\python.exe" "%~dp0\..\Lib\site-packages\azure\cli\__main__.pyc" %*
) ELSE (
  echo Failed to load python executable.
  exit /b 1
)
