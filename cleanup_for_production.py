# 🧹 PRODUCTION CLEANUP SCRIPT
# Futtatás: python cleanup_for_production.py

import os
import shutil
from pathlib import Path

def cleanup_for_production():
    """
    Eltávolítja az összes nem szükséges fájlt a production deploymenthez
    """
    
    # Kötelező production fájlok
    KEEP_FILES = {
        'streamlit_app.py',
        'optimized_ml_model.py', 
        'analyze_descriptions_focused.py',
        'ingatlan_reszletes_enhanced_text_features.csv',
        'requirements.txt',
        # DATA PIPELINE (adatfrissítéshez)
        'ingatlan_list_details_scraper.py',  # ⚠️ Alap CSV előállítása
        'enhance_csv_with_text.py',          # ⚠️ Enhanced CSV előállítása
        'update_data.py',                    # ⚠️ Adatfrissítő script
        # OPCIONÁLIS
        'README.md'
    }
    
    # Elhagyandó mappák
    DELETE_DIRS = {
        'archive',
        '__pycache__',
        'ingatlan_agent_env',
        '.devcontainer',
        '.vscode',
        '.streamlit'
    }
    
    # Elhagyandó fájl minták
    DELETE_PATTERNS = [
        'test_*.py',
        'debug_*.py', 
        'ingatlan_*.py',  # scraping scriptek
        'scrape_*.py',
        'model_diagnostics*.py',
        '*.pyc',
        '.DS_Store'
    ]
    
    print("🧹 PRODUCTION CLEANUP INDÍTÁS...")
    print(f"📂 Working directory: {os.getcwd()}")
    
    deleted_files = 0
    deleted_dirs = 0
    kept_files = 0
    
    # Mappák törlése
    for dir_name in DELETE_DIRS:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"🗑️ Mappa törölve: {dir_name}")
                deleted_dirs += 1
            except Exception as e:
                print(f"❌ Hiba {dir_name} törlésekor: {e}")
    
    # Fájlok vizsgálata
    for file in os.listdir('.'):
        if os.path.isfile(file):
            
            # Kötelező fájlok megőrzése
            if file in KEEP_FILES:
                print(f"✅ Megőrizve: {file}")
                kept_files += 1
                continue
                
            # Egyedi elhagyandó fájlok
            delete_these = [
                'advanced_ml_model.py',
                'analyze_descriptions.py',  # NEM a focused verzió!
                'demo_enhanced_mode.py',
                'diagnose_data_loss.py',
                'get_semantic_insights.py',
                'statistical_analysis.py',
                'check_data.py',
                'dashboard_elado_haz_erd_erdliget.py',
                # Alternatív scraping fájlok (nem a fő scraper)
                'ingatlan_full_pipeline.py',
                'ingatlan_komplett_pipeline.py', 
                'ingatlan_simple_pipeline.py',
                'scrape_property_details_pipeline.py',
                'scrape_url_based.py',
                'scrape_url_based_pipeline.py',
                # Fallback CSV
                'ingatlan_reszletes_elado_haz_erd_erdliget_20250820_014506.csv',  # fallback CSV
                '.gitignore',
                # Dokumentációk (opcionális törlés)
                'HIBRID_UTMUTATO.md',
                'IP_BLOKK_MEGOLDAS.md', 
                'ML_MODEL_SUMMARY.md',
                'PRODUCTION_FILES_ANALYSIS.md'
            ]
            
            if file in delete_these:
                try:
                    os.remove(file)
                    print(f"🗑️ Fájl törölve: {file}")
                    deleted_files += 1
                except Exception as e:
                    print(f"❌ Hiba {file} törlésekor: {e}")
                continue
            
            # Mintázatok alapján törlés
            should_delete = False
            for pattern in DELETE_PATTERNS:
                if file.startswith(pattern.replace('*', '')) or file.endswith(pattern.replace('*', '')):
                    should_delete = True
                    break
            
            if should_delete:
                try:
                    os.remove(file)
                    print(f"🗑️ Fájl törölve (minta): {file}")
                    deleted_files += 1
                except Exception as e:
                    print(f"❌ Hiba {file} törlésekor: {e}")
            else:
                print(f"⚠️ Ismeretlen fájl (kézi ellenőrzés): {file}")
    
    print("\n" + "="*50)
    print("🏁 CLEANUP BEFEJEZVE!")
    print(f"✅ Megőrzött fájlok: {kept_files}")
    print(f"🗑️ Törölt fájlok: {deleted_files}")
    print(f"🗑️ Törölt mappák: {deleted_dirs}")
    print("\n🎯 PRODUCTION READY!")
    print("📋 Következő lépés: python -m streamlit run streamlit_app.py")

if __name__ == "__main__":
    
    # Biztonsági kérdés
    answer = input("\n⚠️ FIGYELEM! Ez törölni fog sok fájlt!\nBiztosan folytatod? (YES/no): ")
    
    if answer.upper() == "YES":
        cleanup_for_production()
    else:
        print("❌ Cleanup megszakítva.")
        print("💡 Készíts előbb backup-ot: git commit -am 'backup before cleanup'")
