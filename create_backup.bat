@echo off
REM 💾 PRODUCTION BACKUP SCRIPT - WINDOWS

echo 💾 BACKUP KÉSZÍTÉSE...

REM Timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "TIMESTAMP=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"
set "BACKUP_NAME=erdliget_dashboard_backup_%TIMESTAMP%"

REM Git commit (ha git repo)
if exist ".git" (
    echo 📝 Git commit készítése...
    git add .
    git commit -m "Backup before production cleanup - %TIMESTAMP%"
    echo ✅ Git backup kész
)

REM Teljes mappa másolat
echo 📂 Fájlok másolása...
cd ..
xcopy real_agent_2 "%BACKUP_NAME%" /E /I /H
echo ✅ Backup létrehozva: %BACKUP_NAME%

echo.
echo 🎯 Most biztonságosan futtathatod a cleanup scriptet!
echo 📋 Parancs: cd real_agent_2 ^&^& python cleanup_for_production.py

pause
