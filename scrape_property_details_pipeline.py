#!/usr/bin/env python3
"""
PIPELINE KOMPATIBILIS RÉSZLETES SCRAPER
======================================
A scrape_property_details.py pipeline használathoz optimalizált verziója
"""

import sys
import os
import pandas as pd
from datetime import datetime
import subprocess

class PipelineDetailsScraper:
    """Pipeline-kompatibilis részletes scraper"""
    
    def __init__(self, list_csv_file, location_name):
        self.list_csv_file = list_csv_file
        self.location_name = location_name
        
    def create_details_csv(self):
        """Részletes CSV fájl létrehozása"""
        try:
            # Eredeti scrape_property_details.py futtatása automatizáltan
            print("🚀 Részletes scraper indítása...")
            
            # Temp fájl készítése az automatizált inputhoz
            temp_input_file = "temp_input.txt"
            with open(temp_input_file, 'w') as f:
                f.write(f"{self.list_csv_file}\n")  # CSV fájl neve
                f.write("1\n")  # Option 1 - start scraping
            
            # Scraper futtatása
            try:
                with open(temp_input_file, 'r') as input_file:
                    result = subprocess.run([
                        sys.executable, 
                        'scrape_property_details.py'
                    ], stdin=input_file, capture_output=True, text=True, timeout=3600)  # 1 óra timeout
                
                print(f"Return code: {result.returncode}")
                if result.stdout:
                    print("STDOUT:", result.stdout[-500:])  # Utolsó 500 karakter
                if result.stderr:
                    print("STDERR:", result.stderr[-500:])  # Utolsó 500 karakter
                
                # Eredmény fájl keresése
                if result.returncode == 0:
                    return self._find_result_file()
                else:
                    print("❌ Részletes scraper futása sikertelen")
                    return None
                    
            finally:
                # Temp fájl törlése
                if os.path.exists(temp_input_file):
                    os.remove(temp_input_file)
                    
        except Exception as e:
            print(f"❌ Részletes scraper hiba: {e}")
            return None
    
    def _find_result_file(self):
        """Eredmény fájl megkeresése"""
        try:
            import glob
            
            # Mai dátummal keresés
            timestamp_today = datetime.now().strftime("%Y%m%d")
            
            # Különböző mintákkal próbálkozunk
            patterns = [
                f"ingatlan_reszletes_{timestamp_today}_*.csv",
                f"ingatlan_reszletes_*{timestamp_today}*.csv",
                f"ingatlan_reszletes_*.csv"
            ]
            
            for pattern in patterns:
                files = glob.glob(pattern)
                if files:
                    # Legújabb fájl visszaadása
                    latest_file = max(files, key=os.path.getctime)
                    
                    # Átnevezés lokáció alapján
                    new_name = f"ingatlan_reszletes_{self.location_name}_{timestamp_today}_{datetime.now().strftime('%H%M%S')}.csv"
                    os.rename(latest_file, new_name)
                    
                    return new_name
            
            return None
            
        except Exception as e:
            print(f"❌ Eredmény fájl keresési hiba: {e}")
            return None

def main():
    """Pipeline main függvény"""
    if len(sys.argv) != 3:
        print("❌ Használat: python scrape_property_details_pipeline.py <lista_csv> <lokáció_név>")
        return
    
    list_csv_file = sys.argv[1]
    location_name = sys.argv[2]
    
    print("🔍 RÉSZLETES SCRAPER - PIPELINE VERZIÓ")
    print("="*60)
    print(f"📊 Bemeneti fájl: {list_csv_file}")
    print(f"📍 Lokáció: {location_name}")
    
    if not os.path.exists(list_csv_file):
        print(f"❌ Lista CSV fájl nem található: {list_csv_file}")
        return
    
    # CSV fájl ellenőrzése
    try:
        df = pd.read_csv(list_csv_file)
        print(f"📋 {len(df)} ingatlan a listában")
        
        if 'link' not in df.columns:
            print("❌ Hiányzó oszlop: link")
            return
            
    except Exception as e:
        print(f"❌ CSV fájl olvasási hiba: {e}")
        return
    
    # Részletes scraper futtatása
    scraper = PipelineDetailsScraper(list_csv_file, location_name)
    result_file = scraper.create_details_csv()
    
    if result_file and os.path.exists(result_file):
        print(f"\n🎉 RÉSZLETES SCRAPING SIKERES!")
        print(f"📁 Kimeneti fájl: {result_file}")
        
        # Eredmény statisztikák
        try:
            result_df = pd.read_csv(result_file)
            print(f"📊 Végső eredmény: {len(result_df)} ingatlan részletes adatokkal")
        except:
            pass
    else:
        print("❌ Részletes scraping sikertelen")

if __name__ == "__main__":
    main()
