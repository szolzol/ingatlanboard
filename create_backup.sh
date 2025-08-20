#!/bin/bash
# 💾 PRODUCTION BACKUP SCRIPT

echo "💾 BACKUP KÉSZÍTÉSE..."

# Timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="erdliget_dashboard_backup_${TIMESTAMP}"

# Git commit (ha git repo)
if [ -d ".git" ]; then
    echo "📝 Git commit készítése..."
    git add .
    git commit -m "Backup before production cleanup - ${TIMESTAMP}"
    echo "✅ Git backup kész"
fi

# Teljes mappa másolat
echo "📂 Fájlok másolása..."
cd ..
cp -r real_agent_2 "${BACKUP_NAME}"
echo "✅ Backup létrehozva: ${BACKUP_NAME}"

echo "🎯 Most biztonságosan futtathatod a cleanup scriptet!"
echo "📋 Parancs: cd real_agent_2 && python cleanup_for_production.py"
