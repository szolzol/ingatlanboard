#!/usr/bin/env python3
"""
PIPELINE KOMPATIBILIS URL-ALAPÚ SCRAPER
======================================
A scrape_url_based.py pipeline használathoz optimalizált verziója
"""

import asyncio
import sys
from datetime import datetime
import pandas as pd
from scrape_url_based import UrlBasedPropertyScraper

class PipelineUrlScraper(UrlBasedPropertyScraper):
    """Pipeline-kompatibilis URL scraper"""
    
    def __init__(self, search_url, location_name):
        super().__init__()
        self.search_url = search_url
        self.location_name = location_name
        
    def save_properties_csv(self, properties):
        """Pipeline-kompatibilis CSV mentés"""
        if not properties:
            print("❌ Nincsenek mentendő adatok")
            return None
            
        try:
            # Fájlnév generálása
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ingatlan_lista_{self.location_name}_{timestamp}.csv"
            
            # DataFrame létrehozása
            df = pd.DataFrame(properties)
            
            # Oszlopok ellenőrzése és rendezése
            expected_columns = ['id', 'cim', 'teljes_ar', 'terulet', 'nm_ar', 'szobak', 'link']
            available_columns = [col for col in expected_columns if col in df.columns]
            
            if available_columns:
                df = df[available_columns]
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                
                print(f"\n💾 Lista mentve: {filename}")
                print(f"📊 Összesen {len(df)} ingatlan, {len(available_columns)} oszlop")
                
                return filename
            else:
                print("❌ Nincs mentendő adat")
                return None
                
        except Exception as e:
            print(f"❌ CSV mentési hiba: {e}")
            return None

async def main():
    """Pipeline main függvény"""
    if len(sys.argv) != 3:
        print("❌ Használat: python scrape_url_based_pipeline.py <URL> <lokáció_név>")
        return
    
    search_url = sys.argv[1]
    location_name = sys.argv[2]
    
    print("URL-ALAPU LISTA SCRAPER - PIPELINE VERZIO")
    print("="*60)
    print(f"URL: {search_url}")
    print(f"Lokacio: {location_name}")
    
    scraper = PipelineUrlScraper(search_url, location_name)
    
    try:
        # Chrome kapcsolat
        if not await scraper.connect_to_existing_chrome():
            print("❌ Chrome kapcsolódás sikertelen")
            return
            
        if not await scraper.get_active_tab():
            print("❌ Tab létrehozás sikertelen")
            return
        
            print(f"\nLista scraping inditasa...")        # Ingatlan lista scraping
        properties = await scraper.scrape_property_list(search_url)
        
        if properties:
            # CSV mentése
            csv_file = scraper.save_properties_csv(properties)
            
            if csv_file:
                print(f"\nLISTA SCRAPING SIKERES!")
                print(f"Kimeneti fajl: {csv_file}")
                print(f"Osszesen: {len(properties)} ingatlan")
            else:
                print("CSV mentes sikertelen")
                
        else:
            print("Nem sikerult ingatlanokat talalni")
            
    except Exception as e:
        print(f"❌ Scraping hiba: {e}")
        
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
