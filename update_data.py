#!/usr/bin/env python3
"""
🔄 ADATFRISSÍTŐ SCRIPT - PRODUCTION
==================================
Ez a script frissíti az ingatlan adatokat a production környezetben.

Használat:
    python update_data.py

Lépések:
1. Scraping - új alap CSV létrehozása
2. Text enhancement - enhanced CSV létrehozása
3. Backup - régi fájlok archiválása
"""

import os
import shutil
import asyncio
from datetime import datetime

def backup_existing_csv():
    """Meglévő CSV fájlok backup-ja"""
    print("💾 MEGLÉVŐ CSV FÁJLOK BACKUP...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"data_backup_{timestamp}"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Enhanced CSV backup
    enhanced_file = "ingatlan_reszletes_enhanced_text_features.csv"
    if os.path.exists(enhanced_file):
        shutil.copy2(enhanced_file, os.path.join(backup_dir, f"backup_{enhanced_file}"))
        print(f"✅ Enhanced CSV backed up to {backup_dir}/")
    
    # Alap CSV backup (ha van)
    for file in os.listdir("."):
        if file.startswith("ingatlan_reszletes_") and file.endswith(".csv") and "enhanced" not in file:
            shutil.copy2(file, os.path.join(backup_dir, f"backup_{file}"))
            print(f"✅ {file} backed up to {backup_dir}/")
    
    return backup_dir

def run_scraping():
    """Alap CSV scraping futtatása"""
    print("\n🕷️ SCRAPING INDÍTÁSA...")
    print("⚠️ FIGYELEM: Ez akár 10-30 percet is igénybe vehet!")
    
    try:
        # Scraping futtatása
        import subprocess
        result = subprocess.run(
            ["python", "ingatlan_list_details_scraper.py"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Scraping sikeres!")
            return True
        else:
            print(f"❌ Scraping hiba: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Scraping futtatási hiba: {e}")
        return False

def run_text_enhancement():
    """Text enhancement futtatása"""
    print("\n📝 TEXT ENHANCEMENT INDÍTÁSA...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["python", "enhance_csv_with_text.py"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Text enhancement sikeres!")
            return True
        else:
            print(f"❌ Text enhancement hiba: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Text enhancement futtatási hiba: {e}")
        return False

def validate_new_data():
    """Új adatok validálása"""
    print("\n✅ ÚJ ADATOK VALIDÁLÁSA...")
    
    enhanced_file = "ingatlan_reszletes_enhanced_text_features.csv"
    
    if not os.path.exists(enhanced_file):
        print("❌ Enhanced CSV nem található!")
        return False
    
    try:
        import pandas as pd
        df = pd.read_csv(enhanced_file, encoding='utf-8-sig')
        
        print(f"📊 Új adatok: {len(df)} rekord")
        print(f"📋 Oszlopok száma: {len(df.columns)}")
        
        # Text feature-k ellenőrzése
        text_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['luxus', 'komfort', 'parkol', 'pont', 'van_'])]
        print(f"🎯 Text feature-k: {len(text_cols)} db")
        
        if len(df) > 0 and len(text_cols) >= 6:
            print("✅ Új adatok validálva!")
            return True
        else:
            print("❌ Adatok nem megfelelőek!")
            return False
            
    except Exception as e:
        print(f"❌ Validálási hiba: {e}")
        return False

def main():
    """Főprogram"""
    print("🔄 INGATLAN ADATFRISSÍTÉS - PRODUCTION")
    print("="*50)
    
    # Megerősítés kérése
    answer = input("\n⚠️ Ez frissíteni fogja az összes adatot!\nFolytatod? (yes/no): ").lower()
    
    if answer != 'yes':
        print("❌ Adatfrissítés megszakítva.")
        return
    
    # 1. Backup
    backup_dir = backup_existing_csv()
    
    # 2. Scraping
    if not run_scraping():
        print("❌ Scraping sikertelen, megszakítás.")
        return
    
    # 3. Text enhancement
    if not run_text_enhancement():
        print("❌ Text enhancement sikertelen, megszakítás.")
        return
    
    # 4. Validálás
    if not validate_new_data():
        print("❌ Új adatok nem validak, visszaállítás szükséges!")
        return
    
    print("\n" + "="*50)
    print("🎉 ADATFRISSÍTÉS SIKERES!")
    print(f"💾 Backup helye: {backup_dir}/")
    print("🚀 A dashboard most az új adatokkal fog működni!")
    print("\n📋 Következő lépés: streamlit alkalmazás újraindítása")

if __name__ == "__main__":
    main()
