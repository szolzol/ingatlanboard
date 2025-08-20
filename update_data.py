#!/usr/bin/env python3
"""
🔄 ADATFRISSÍTŐ SCRIPT - PRODUCTION (Integrált verzió)
=====================================================
Ez a script frissíti az ingatlan adatokat a production környezetben
az integrált scraper segítségével.

🌟 INTEGRÁCIÓ UTÁN:
- Egy lépéses folyamat
- Automatikus Enhanced CSV generálás
- Beépített szöveganalízis (18 text feature)

Használat:
    python update_data.py

Lépések:
1. 🌟 Integrált scraping - Enhanced CSV egyből
2. Backup - régi fájlok archiválása
3. Validálás és jelentés
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

def run_integrated_scraping():
    """🌟 Integrált Enhanced scraping futtatása"""
    print("\n🌟 INTEGRÁLT ENHANCED SCRAPING INDÍTÁSA...")
    print("✨ Szöveganalízis beépítve - Enhanced CSV egyből!")
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
            print("✅ Integrált Enhanced scraping sikeres!")
            print("🌟 Enhanced CSV automatikusan generálva!")
            return True
        else:
            print(f"❌ Scraping hiba: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Scraping futtatási hiba: {e}")
        return False

def validate_enhanced_data():
    """Enhanced CSV validálása"""
    print("\n� ENHANCED CSV VALIDÁLÁS...")
    
    enhanced_file = "ingatlan_reszletes_enhanced_text_features.csv"
    
    if not os.path.exists(enhanced_file):
        print(f"❌ Enhanced CSV nem található: {enhanced_file}")
        return False
    
    try:
        import pandas as pd
        df = pd.read_csv(enhanced_file, encoding='utf-8-sig')
        
        # Alapvető ellenőrzések
        print(f"📊 Sorok száma: {len(df)}")
        print(f"📋 Oszlopok száma: {len(df.columns)}")
        
        # Text feature oszlopok ellenőrzése
        text_feature_cols = [col for col in df.columns if any(x in col.lower() 
                           for x in ['luxus_', 'kert_', 'parkolas_', 'komfort_', 'van_', 'pont'])]
        
        print(f"🌟 Text feature oszlopok: {len(text_feature_cols)}")
        
        if len(text_feature_cols) >= 15:  # Legalább 15 text feature
            print("✅ Enhanced CSV validálás sikeres!")
            
            # Statisztikák
            luxus_count = df['van_luxus_kifejezés'].sum() if 'van_luxus_kifejezés' in df.columns else 0
            kert_count = df['van_kert_terulet'].sum() if 'van_kert_terulet' in df.columns else 0
            garage_count = df['van_garage_parkolas'].sum() if 'van_garage_parkolas' in df.columns else 0
            
            print(f"📈 Luxus ingatlanok: {luxus_count}")
            print(f"🌳 Kertes ingatlanok: {kert_count}")
            print(f"🚗 Garázsos ingatlanok: {garage_count}")
            
            return True
        else:
            print(f"❌ Hiányos text feature-k: {len(text_feature_cols)} < 15")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced CSV validálási hiba: {e}")
        return False
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
    """Főprogram - Integrált Enhanced ingatlan adatok frissítése"""
    print("🔄 INTEGRÁLT ENHANCED INGATLAN ADATFRISSÍTÉS - PRODUCTION")
    print("="*60)
    
    print("\n🌟 INTEGRÁLT ADATFRISSÍTÉS:")
    print("✨ Egy lépéses folyamat - Enhanced CSV egyből")
    print("📊 18 text feature automatikusan hozzáadva")
    print("⚡ Egyszerűsített workflow")
    print("⏱️ Várható időtartam: 10-30 perc")
    
    # Megerősítés kérése
    answer = input("\n⚠️ Ez frissíteni fogja az összes adatot az integrált módszerrel!\nFolytatod? (yes/no): ").lower()
    
    if answer != 'yes':
        print("❌ Adatfrissítés megszakítva.")
        return
    
    # 1. Backup
    backup_dir = backup_existing_csv()
    
    # 2. Integrált Enhanced Scraping
    if not run_integrated_scraping():
        print("❌ Integrált scraping sikertelen, megszakítás.")
        return
    
    # 3. Enhanced adatok validálása
    if not validate_enhanced_data():
        print("❌ Enhanced adatok validálása sikertelen, visszaállítás szükséges!")
        return
    
    print("\n" + "="*60)
    print("🎉 INTEGRÁLT ENHANCED ADATFRISSÍTÉS SIKERES!")
    print(f"💾 Backup helye: {backup_dir}/")
    print("🌟 Enhanced CSV automatikusan generálva text feature-ökkel!")
    print("🚀 A dashboard most az új Enhanced adatokkal fog működni!")
    print("\n📋 Következő lépés: streamlit alkalmazás újraindítása")

if __name__ == "__main__":
    main()
