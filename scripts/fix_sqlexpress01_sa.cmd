@echo off
setlocal EnableExtensions

set "INSTANCE=SQLEXPRESS01"
set "SERVICE=MSSQL$SQLEXPRESS01"

if "%~1"=="" (
    echo Usage: %~nx0 ^<NewSaPassword^>
    echo Example: %~nx0 MyStrongPass123!
    exit /b 1
)

set "SA_PASSWORD=%~1"

rem Single quotes break the SQL literal in this simple script.
if not "%SA_PASSWORD:'=%"=="%SA_PASSWORD%" (
    echo Error: password cannot contain a single quote character.
    exit /b 1
)

rem Admin rights are required for restarting SQL Server services.
net session >nul 2>&1
if errorlevel 1 (
    echo Error: run this script in an Administrator Command Prompt.
    exit /b 1
)

where sqlcmd >nul 2>&1
if errorlevel 1 (
    echo Error: sqlcmd not found in PATH.
    echo Install it first: winget install --id Microsoft.Sqlcmd --exact --silent --accept-package-agreements --accept-source-agreements
    exit /b 1
)

echo [1/5] Verifying admin connection to %INSTANCE%...
sqlcmd -S lpc:localhost\%INSTANCE% -E -b -Q "SELECT @@SERVERNAME;" >nul
if errorlevel 1 (
    echo Error: Windows admin login to instance %INSTANCE% failed.
    echo Sign in as a real local admin and retry.
    exit /b 1
)

echo [2/5] Enabling mixed authentication mode...
sqlcmd -S lpc:localhost\%INSTANCE% -E -b -Q "EXEC xp_instance_regwrite N'HKEY_LOCAL_MACHINE', N'Software\Microsoft\MSSQLServer\MSSQLServer', N'LoginMode', REG_DWORD, 2;"
if errorlevel 1 (
    echo Error: failed to set LoginMode=2.
    exit /b 1
)

echo [3/5] Enabling and resetting sa login...
sqlcmd -S lpc:localhost\%INSTANCE% -E -b -Q "ALTER LOGIN sa ENABLE; ALTER LOGIN sa WITH PASSWORD = '%SA_PASSWORD%', CHECK_POLICY = OFF, CHECK_EXPIRATION = OFF;"
if errorlevel 1 (
    echo Error: failed to reset sa login.
    exit /b 1
)

echo [4/5] Restarting SQL Server service %SERVICE%...
net stop "%SERVICE%" >nul
if errorlevel 1 (
    echo Error: failed to stop %SERVICE%.
    exit /b 1
)

net start "%SERVICE%" >nul
if errorlevel 1 (
    echo Error: failed to start %SERVICE%.
    exit /b 1
)

echo [5/5] Verifying sa login...
sqlcmd -S lpc:localhost\%INSTANCE% -U sa -P "%SA_PASSWORD%" -C -b -Q "SELECT @@VERSION AS VersionInfo;"
if errorlevel 1 (
    echo Error: sa verification failed.
    exit /b 1
)

echo.
echo Success: sa login is configured and verified on %INSTANCE%.
exit /b 0

cd "C:\Data Visualization\DE\Data-Engineer-Online-Store-Sales-Analytics"
scripts\fix_sqlexpress01_sa.cmd Krishn@16108
