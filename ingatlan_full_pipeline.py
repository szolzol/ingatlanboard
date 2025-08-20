#!/usr/bin/env python3
"""
TELJES INGATLAN ELEMZŐ PIPELINE
===============================
0. URL bekérés és 300-as limit beállítás
1. Lista scraping (URL, ár, m2 ár, cím, alapterület, szobaszám)
2. Részletes scraping (leírás, építés éve, emelet, állapot stb.)
3. Dashboard generálás
"""

import asyncio
import os
import re
import subprocess
import sys
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import pandas as pd

class IngatlanPipeline:
    def __init__(self):
        self.search_url = ""
        self.location_name = ""
        self.list_csv_file = ""
        self.details_csv_file = ""
        
    def get_search_url_with_limit(self):
        """URL bekérés és 300-as limit beállítás"""
        print("🏠 TELJES INGATLAN ELEMZŐ PIPELINE")
        print("="*60)
        
        print("\n🔗 INGATLAN KERESÉSI URL MEGADÁSA")
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
            
            # Keresési rész kinyerése (pl. elado+lakas+kobanyi-ujhegy)
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
    
    async def run_list_scraping(self):
        """1. LÉPÉS: Lista scraping futtatása"""
        print(f"\n" + "="*60)
        print("🔍 1. LÉPÉS: INGATLAN LISTA SCRAPING")
        print("="*60)
        
        print(f"🎯 Célállomás: {self.search_url}")
        print(f"📊 Várható találatok: maximum 300 ingatlan")
        print(f"📁 Lokáció: {self.location_name}")
        
        # Lista scraper futtatása
        try:
            # Importáljuk a refactored scraper osztályt
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            
            # Lista scraper modul importálása
            from ingatlan_list_scraper_refactored import IngatlanListScraper
            
            scraper = IngatlanListScraper()
            
            # Chrome böngészőhöz kapcsolódás
            if not await scraper.connect_to_chrome():
                print("❌ Chrome kapcsolódás sikertelen")
                return False
            
            # Navigáció az URL-re
            print(f"🌐 Navigáció: {self.search_url}")
            await scraper.page.goto(self.search_url)
            
            # Várunk a Cloudflare challenge megoldására (ha szükséges)
            print("🔒 Cloudflare challenge ellenőrzése...")
            await scraper.wait_for_manual_cloudflare_resolution()
            
            # Lista scraping
            properties = await scraper.scrape_multiple_pages(max_pages=15)  # 300 ingatlan = ~15 oldal
            
            if properties:
                # CSV fájl mentése a lokáció nevével
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.list_csv_file = f"ingatlan_lista_{self.location_name}_{timestamp}.csv"
                
                # Scraper saját mentési metódusát használjuk
                saved_file = scraper.save_to_csv(properties, f"ingatlan_lista_{self.location_name}")
                self.list_csv_file = saved_file
                
                print(f"\n🎉 LISTA SCRAPING SIKERES!")
                print(f"📁 Kimeneti fájl: {self.list_csv_file}")
                print(f"📊 Összesen: {len(properties)} ingatlan")
                
                await scraper.close_connection()
                return True
                
            else:
                print("❌ Nem sikerült ingatlanokat találni")
                await scraper.close_connection()
                return False
                
        except Exception as e:
            print(f"❌ Lista scraping hiba: {e}")
            return False
    
    def run_details_scraping(self):
        """2. LÉPÉS: Részletes scraping futtatása"""
        print(f"\n" + "="*60)
        print("🔍 2. LÉPÉS: RÉSZLETES INGATLAN SCRAPING")
        print("="*60)
        
        if not self.list_csv_file or not os.path.exists(self.list_csv_file):
            print("❌ Lista CSV fájl nem található!")
            return False
        
        print(f"📊 Bemeneti fájl: {self.list_csv_file}")
        
        try:
            # A scrape_property_details.py futtatása
            cmd = [
                'python', 
                'scrape_property_details.py'
            ]
            
            print(f"🚀 Részletes scraping indítása...")
            print(f"💡 A program be fogja kérni a CSV fájl nevét - add meg: {self.list_csv_file}")
            
            # Interaktív futtatás
            result = subprocess.run(cmd, cwd=os.getcwd())
            
            if result.returncode == 0:
                # Eredmény fájl keresése
                timestamp = datetime.now().strftime("%Y%m%d")
                pattern = f"ingatlan_reszletes_{timestamp}_*.csv"
                
                import glob
                result_files = glob.glob(pattern)
                
                if result_files:
                    self.details_csv_file = max(result_files, key=os.path.getctime)  # Legújabb fájl
                    print(f"\n🎉 RÉSZLETES SCRAPING SIKERES!")
                    print(f"📁 Kimeneti fájl: {self.details_csv_file}")
                    return True
                else:
                    print("⚠️ Részletes scraping lefutott, de nem találom az eredmény fájlt")
                    # Manuális fájlnév bekérése
                    manual_file = input("📁 Add meg az eredmény fájl nevét: ").strip()
                    if manual_file and os.path.exists(manual_file):
                        self.details_csv_file = manual_file
                        return True
                    return False
            else:
                print("❌ Részletes scraping sikertelen")
                return False
                
        except Exception as e:
            print(f"❌ Részletes scraping hiba: {e}")
            return False
    
    def create_custom_dashboard(self):
        """3. LÉPÉS: Testreszabott dashboard készítése"""
        print(f"\n" + "="*60)
        print("🎨 3. LÉPÉS: TESTRESZABOTT DASHBOARD KÉSZÍTÉSE")
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
        location_display = location.replace('_', ' ').replace('-', '-').title()
        location_display = re.sub(r'\+', ' ', location_display)
        
        customizations = {
            # Cím testreszabása
            r'🏠 Kőbánya-Újhegyi Lakótelep - Részletes Piaci Elemzés': f'🏠 {location_display} - Részletes Piaci Elemzés',
            r'Kőbánya-Újhegyi Lakótelep': location_display,
            r'KŐBÁNYA-ÚJHEGYI LAKÓTELEP': location_display.upper(),
            r'Kőbánya-Újhegy': location_display,
            
            # CSV fájl elérési út
            r'ingatlan_reszletes_\d{8}_\d{6}\.csv': csv_file,
            r'data/ingatlan_reszletes.*\.csv': csv_file,
            
            # Szöveges hivatkozások
            r'a Kőbánya-Újhegyi lakótelepről': f'a(z) {location_display} területről',
            r'Kőbánya X\. kerület, Újhegyi lakótelep': f'{location_display} környéke',
            
            # Dashboard title in set_page_config
            r'🏠 Kőbánya-Újhegy Ingatlan Piaci Elemzés': f'🏠 {location_display} Ingatlan Piaci Elemzés'
        }
        
        # Template módosítása
        customized = template
        for pattern, replacement in customizations.items():
            customized = re.sub(pattern, replacement, customized)
        
        # CSV fájl beolvasási rész módosítása
        load_data_pattern = r'def load_data\(\):\s*""".*?""".*?try:\s*.*?except.*?:'
        new_load_data = f'''def load_data():
    """Adatok betöltése"""
    try:
        df = pd.read_csv("{csv_file}", encoding='utf-8-sig')
        
        # Alapvető oszlopok ellenőrzése
        required_columns = ['link', 'cim']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Hiányzó oszlopok: {{', '.join(missing_columns)}}")
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
        
        customized = re.sub(load_data_pattern, new_load_data, customized, flags=re.DOTALL)
        
        return customized

async def main():
    """Főprogram"""
    pipeline = IngatlanPipeline()
    
    try:
        # 0. URL bekérés
        if not pipeline.get_search_url_with_limit():
            return
        
        # 1. Lista scraping
        print("\n⏳ Lista scraping indítása 5 másodperc múlva...")
        await asyncio.sleep(5)
        
        if not await pipeline.run_list_scraping():
            print("❌ Pipeline megszakítva - lista scraping sikertelen")
            return
        
        # 2. Részletes scraping
        print("\n⏳ Részletes scraping indítása 3 másodperc múlva...")
        print("💡 FONTOS: A következő lépésben be kell írni a CSV fájl nevét!")
        await asyncio.sleep(3)
        
        if not pipeline.run_details_scraping():
            print("❌ Pipeline megszakítva - részletes scraping sikertelen")
            return
        
        # 3. Dashboard készítés
        if not pipeline.create_custom_dashboard():
            print("❌ Pipeline megszakítva - dashboard készítés sikertelen")
            return
        
        print(f"\n" + "🎉"*20)
        print("✅ TELJES PIPELINE SIKERES!")
        print("🎉"*20)
        print(f"\n📋 EREDMÉNY ÖSSZEFOGLALÓ:")
        print(f"   📊 Lista CSV: {pipeline.list_csv_file}")
        print(f"   🔍 Részletes CSV: {pipeline.details_csv_file}")
        print(f"   🎨 Dashboard: dashboard_{pipeline.location_name}.py")
        
        print(f"\n🚀 KÖVETKEZŐ LÉPÉSEK:")
        print(f"   1. Aktiváld a környezetet: ingatlan_agent_env\\Scripts\\activate")
        print(f"   2. Indítsd a dashboardot: streamlit run dashboard_{pipeline.location_name}.py")
        
    except KeyboardInterrupt:
        print(f"\n⏸️ Pipeline megszakítva felhasználó által")
    except Exception as e:
        print(f"\n❌ Pipeline hiba: {e}")

if __name__ == "__main__":
    asyncio.run(main())
