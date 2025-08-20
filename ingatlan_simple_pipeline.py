#!/usr/bin/env python3
"""
EGYSZERŰSÍTETT INGATLAN ELEMZŐ PIPELINE
======================================
1. URL bekérés és 300-as limit beállítás
2. Lista scraping (scrape_url_based alapján)
3. Részletes scraping (scrape_property_details alapján)
4. Dashboard generálás (ingatlan_dashboard_advanced alapján)
"""

import asyncio
import os
import re
import subprocess
import sys
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import pandas as pd

class SimpleIngatlanPipeline:
    def __init__(self):
        self.search_url = ""
        self.location_name = ""
        self.list_csv_file = ""
        self.details_csv_file = ""
        
    def step_1_get_url(self):
        """1. LÉPÉS: URL bekérés és 300-as limit beállítás"""
        print("🏠 EGYSZERŰSÍTETT INGATLAN ELEMZŐ PIPELINE")
        print("="*60)
        
        print("\n🔗 1. LÉPÉS: INGATLAN KERESÉSI URL MEGADÁSA")
        print("="*50)
        print("💡 Példa URL-ek:")
        print("   https://ingatlan.com/szukites/elado+lakas+kobanyi-ujhegy")
        print("   https://ingatlan.com/lista/elado+haz+erd-erdliget")
        print("   https://ingatlan.com/szukites/elado+lakas+xiii-kerulet")
        print("   https://ingatlan.com/lista/elado+lakas+budapest")
        
        while True:
            url = input("\n📍 Add meg a keresési URL-t: ").strip()
            
            if not url:
                print("❌ Kérlek adj meg egy URL-t!")
                continue
                
            if 'ingatlan.com' not in url:
                print("❌ Csak ingatlan.com URL-ek támogatottak!")
                continue
                
            # URL feldolgozása
            self.search_url = self._add_limit_to_url(url)
            self.location_name = self._extract_location_from_url(url)
            
            print(f"✅ Továbbfejlesztett URL: {self.search_url}")
            print(f"🎯 Maximum találatok: 300 ingatlan")
            print(f"📍 Lokáció azonosító: {self.location_name}")
            
            return True
    
    def _add_limit_to_url(self, url):
        """300-as limit hozzáadása az URL-hez"""
        try:
            # URL részekre bontása
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # Limit beállítása
            query_params['limit'] = ['300']
            
            # URL újraépítése
            new_query = urlencode(query_params, doseq=True)
            new_parsed = parsed._replace(query=new_query)
            
            return urlunparse(new_parsed)
            
        except Exception as e:
            # Fallback megoldás
            separator = '&' if '?' in url else '?'
            if 'limit=' in url:
                # Meglévő limit cseréje
                url = re.sub(r'limit=\d+', 'limit=300', url)
            else:
                # Új limit hozzáadása
                url = f"{url}{separator}limit=300"
            return url
    
    def _extract_location_from_url(self, url):
        """Lokáció kinyerése URL-ből fájlnév generáláshoz"""
        try:
            # URL path részének kinyerése
            path = urlparse(url).path
            
            # Keresési rész kinyerése
            path_parts = path.split('/')
            search_part = ""
            
            for part in path_parts:
                if 'elado' in part or 'kiado' in part:
                    search_part = part
                    break
            
            if not search_part:
                search_part = path_parts[-1] if path_parts else "keresés"
            
            # Biztonságos fájlnév készítése
            safe_name = re.sub(r'[^\w\-_+]', '_', search_part)
            safe_name = safe_name.replace('+', '_')
            safe_name = safe_name[:50]  # Maximális hossz
            
            return safe_name if safe_name else "ingatlan_kereses"
            
        except Exception:
            return "ingatlan_kereses"
    
    def step_2_list_scraping(self):
        """2. LÉPÉS: Lista scraping futtatása"""
        print(f"\n" + "="*60)
        print("🔍 2. LÉPÉS: INGATLAN LISTA SCRAPING")
        print("="*60)
        
        print(f"🎯 Célállomás: {self.search_url}")
        print(f"📊 Várható találatok: maximum 300 ingatlan")
        print(f"📁 Lokáció: {self.location_name}")
        
        try:
            # Az ingatlan_list_scraper_refactored.py-t használjuk
            result = subprocess.run([
                sys.executable,
                'ingatlan_list_scraper_refactored.py'
            ], input=f"{self.search_url}\n1\n10\n", text=True, capture_output=True)
            
            if result.returncode == 0:
                # Keressük meg a generált CSV fájlt
                import glob
                pattern = f"ingatlan_lista_*.csv"
                files = glob.glob(pattern)
                
                if files:
                    self.list_csv_file = max(files, key=os.path.getctime)  # Legújabb fájl
                    
                    # Átnevezzük a fájlt a lokáció nevével
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_name = f"ingatlan_lista_{self.location_name}_{timestamp}.csv"
                    os.rename(self.list_csv_file, new_name)
                    self.list_csv_file = new_name
                    
                    print(f"\n🎉 LISTA SCRAPING SIKERES!")
                    print(f"📁 Kimeneti fájl: {self.list_csv_file}")
                    return True
                else:
                    print(f"⚠️ Nem találom a lista CSV fájlt. Manuálisan add meg:")
                    manual_file = input("📁 CSV fájl neve: ").strip()
                    if manual_file and os.path.exists(manual_file):
                        self.list_csv_file = manual_file
                        return True
                    return False
            else:
                print(f"❌ Lista scraping hiba: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Lista scraping hiba: {e}")
            return False
    
    def step_3_details_scraping(self):
        """3. LÉPÉS: Részletes scraping futtatása"""
        print(f"\n" + "="*60)
        print("🔍 3. LÉPÉS: RÉSZLETES INGATLAN SCRAPING")  
        print("="*60)
        
        if not self.list_csv_file or not os.path.exists(self.list_csv_file):
            print("❌ Lista CSV fájl nem található!")
            return False
        
        print(f"📊 Bemeneti fájl: {self.list_csv_file}")
        
        try:
            # A scrape_property_details.py futtatása
            print(f"\n🚀 Részletes scraper indítása...")
            
            # Automatizált futtatás a CSV fájl nevével
            result = subprocess.run([
                sys.executable,
                'scrape_property_details_pipeline.py',
                self.list_csv_file,
                self.location_name
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                # Eredmény fájl keresése
                timestamp_today = datetime.now().strftime("%Y%m%d")
                import glob
                pattern = f"ingatlan_reszletes_{self.location_name}_*{timestamp_today}*.csv"
                files = glob.glob(pattern)
                
                if files:
                    self.details_csv_file = max(files, key=os.path.getctime)  # Legújabb fájl
                    print(f"\n🎉 RÉSZLETES SCRAPING SIKERES!")
                    print(f"📁 Kimeneti fájl: {self.details_csv_file}")
                    return True
                else:
                    print(f"⚠️ Nem találom a részletes CSV fájlt. Manuálisan add meg:")
                    manual_file = input("📁 CSV fájl neve: ").strip()
                    if manual_file and os.path.exists(manual_file):
                        self.details_csv_file = manual_file
                        return True
                    return False
            else:
                print(f"❌ Részletes scraping hiba: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Részletes scraping hiba: {e}")
            return False
    
    def step_4_dashboard_creation(self):
        """4. LÉPÉS: Dashboard készítés"""
        print(f"\n" + "="*60)
        print("🎨 4. LÉPÉS: TESTRESZABOTT DASHBOARD KÉSZÍTÉSE")
        print("="*60)
        
        if not self.details_csv_file or not os.path.exists(self.details_csv_file):
            print("❌ Részletes CSV fájl nem található!")
            return False
        
        try:
            # Dashboard fájl neve
            dashboard_file = f"dashboard_{self.location_name}.py"
            
            print(f"📊 Adatforrás: {self.details_csv_file}")
            print(f"🎨 Dashboard fájl: {dashboard_file}")
            
            # Dashboard template beolvasása
            with open('ingatlan_dashboard_advanced.py', 'r', encoding='utf-8') as f:
                dashboard_template = f.read()
            
            # Template testreszabása
            customized_dashboard = self._customize_dashboard_template(
                dashboard_template, 
                self.details_csv_file,
                self.location_name
            )
            
            # Új dashboard fájl mentése
            with open(dashboard_file, 'w', encoding='utf-8') as f:
                f.write(customized_dashboard)
            
            print(f"\n🎉 DASHBOARD KÉSZÍTÉS SIKERES!")
            print(f"📁 Dashboard fájl: {dashboard_file}")
            print(f"\n🚀 DASHBOARD INDÍTÁSA:")
            print(f"   streamlit run {dashboard_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Dashboard készítés hiba: {e}")
            return False
    
    def _customize_dashboard_template(self, template, csv_file, location):
        """Dashboard template testreszabása"""
        
        # Lokáció név formázása
        location_display = location.replace('_', ' ').replace('-', ' ').title()
        location_display = re.sub(r'\bElado\b', 'Eladó', location_display)
        location_display = re.sub(r'\bHaz\b', 'Ház', location_display)
        location_display = re.sub(r'\bLakas\b', 'Lakás', location_display)
        
        # Template módosítása
        customizations = {
            # Cím testreszabása
            r'🏠 Kőbánya-Újhegyi Lakótelep - Részletes Piaci Elemzés': f'🏠 {location_display} - Részletes Piaci Elemzés',
            r'Kőbánya-Újhegyi Lakótelep': location_display,
            r'KŐBÁNYA-ÚJHEGYI LAKÓTELEP': location_display.upper(),
            r'Kőbánya-Újhegy': location_display,
            
            # CSV fájl elérési út - egyszerű név használata
            r'ingatlan_reszletes_\d{8}_\d{6}\.csv': csv_file,
            
            # Szöveges hivatkozások
            r'a Kőbánya-Újhegyi lakótelepről': f'a(z) {location_display} területről',
            r'Kőbánya X\. kerület, Újhegyi lakótelep': f'{location_display} környéke',
            
            # Dashboard title
            r'🏠 Kőbánya-Újhegy Ingatlan Piaci Elemzés': f'🏠 {location_display} Ingatlan Piaci Elemzés'
        }
        
        customized = template
        for pattern, replacement in customizations.items():
            customized = re.sub(pattern, replacement, customized)
        
        # Load_data függvény egyszerűsítése
        load_data_replacement = f'''def load_data():
    """Adatok betöltése"""
    try:
        df = pd.read_csv("{csv_file}", encoding='utf-8-sig')
        
        # Alapvető oszlopok ellenőrzése
        if 'link' not in df.columns:
            st.error("Hiányzó oszlop: link")
            return pd.DataFrame()
        
        # Numerikus oszlopok konvertálása
        numeric_columns = ['ar_szam', 'teljes_ar_szam', 'terulet_szam', 'szobak']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
        
    except FileNotFoundError:
        st.error("CSV fájl nem található!")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Adatbetöltési hiba: {{e}}")
        return pd.DataFrame()'''
        
        # Load_data függvény cseréje
        load_data_pattern = r'def load_data\(\):.*?return pd\.DataFrame\(\)'
        customized = re.sub(load_data_pattern, load_data_replacement, customized, flags=re.DOTALL)
        
        return customized
    
    def run_full_pipeline(self):
        """Teljes pipeline futtatása"""
        try:
            # 1. URL bekérés
            print("⏳ Pipeline indítása...")
            if not self.step_1_get_url():
                return False
            
            # 2. Lista scraping
            print(f"\n⏳ Lista scraping indítása 3 másodperc múlva...")
            print("💡 Chrome böngészőt indítsd el debug módban!")
            import time
            time.sleep(3)
            
            if not self.step_2_list_scraping():
                print("❌ Pipeline megszakítva - lista scraping sikertelen")
                return False
            
            # 3. Részletes scraping  
            print(f"\n⏳ Részletes scraping indítása 2 másodperc múlva...")
            time.sleep(2)
            
            if not self.step_3_details_scraping():
                print("❌ Pipeline megszakítva - részletes scraping sikertelen")
                return False
            
            # 4. Dashboard készítés
            if not self.step_4_dashboard_creation():
                print("❌ Pipeline megszakítva - dashboard készítés sikertelen")
                return False
            
            # Eredmény összefoglaló
            print(f"\n" + "🎉"*20)
            print("✅ TELJES PIPELINE SIKERES!")
            print("🎉"*20)
            print(f"\n📋 EREDMÉNY ÖSSZEFOGLALÓ:")
            print(f"   📊 Lista CSV: {self.list_csv_file}")
            print(f"   🔍 Részletes CSV: {self.details_csv_file}")
            print(f"   🎨 Dashboard: dashboard_{self.location_name}.py")
            
            print(f"\n🚀 KÖVETKEZŐ LÉPÉSEK:")
            print(f"   1. Aktiváld a környezetet: ingatlan_agent_env\\Scripts\\activate")
            print(f"   2. Indítsd a dashboardot: streamlit run dashboard_{self.location_name}.py")
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n⏸️ Pipeline megszakítva felhasználó által")
            return False
        except Exception as e:
            print(f"\n❌ Pipeline hiba: {e}")
            return False

def main():
    """Főprogram"""
    pipeline = SimpleIngatlanPipeline()
    pipeline.run_full_pipeline()

if __name__ == "__main__":
    main()
