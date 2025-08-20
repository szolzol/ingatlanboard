#!/usr/bin/env python3
"""
KOMPLETT INGATLAN ELEMZŐ PIPELINE
=================================
1. URL bekérés és 300-as limit hozzáadása
2. Lista scraping (URL, ár, m2 ár, cím, alapterület, szobaszám) 
3. Részletes scraping (leírás, építés éve, emelet, állapot stb.)
4. Dashboard generálás automatikus fájlnevekkel

Használat: python ingatlan_komplett_pipeline.py
"""

import asyncio
import os
import re
import sys
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import pandas as pd
import numpy as np
import subprocess
from collections import Counter, defaultdict
from playwright.async_api import async_playwright

class IngatlanSzovegelemzo:
    """
    Beépített szöveganalízis modul - Enhanced feature-k generálása
    """
    def __init__(self):
        """Inicializálja a kategóriákat és kulcsszavakat"""
        
        # ÉRTÉKBEFOLYÁSOLÓ KATEGÓRIÁK ÉS KULCSSZAVAIK
        self.kategoriak = {
            'LUXUS_MINOSEG': {
                'kulcsszavak': [
                    'luxus', 'prémium', 'elegáns', 'exkluzív', 'különleges', 'lenyűgöző',
                    'kivételes', 'egyedi', 'reprezentatív', 'igényes', 'stílusos',
                    'designer', 'magas színvonal', 'minőségi', 'design', 'dizájn'
                ],
                'pontszam': 3.0
            },
            
            'KERT_KULSO': {
                'kulcsszavak': [
                    'parkosított', 'kert', 'telek', 'udvar', 'kertészkedés', 'gyümölcsfa',
                    'növények', 'fű', 'pázsit', 'virágos', 'árnyékos', 'napos kert',
                    'pergola', 'terasz', 'erkély', 'balkon', 'panoráma', 'kilátás',
                    'természet', 'zöld', 'park', 'liget'
                ],
                'pontszam': 2.5
            },
            
            'PARKOLAS_GARAGE': {
                'kulcsszavak': [
                    'garázs', 'parkoló', 'autó', 'gépkocsi', 'állás', 'fedett',
                    'saját parkoló', 'dupla garázs', 'többállásos', 'behajtó',
                    'kocsibeálló', 'két autó', '2 autó', 'parkolási lehetőség'
                ],
                'pontszam': 2.0
            },
            
            'TERULET_MERET': {
                'kulcsszavak': [
                    'tágas', 'nagy', 'széles', 'hatalmas', 'óriás', 'bőséges',
                    'tér', 'alapterület', 'hasznos', 'nappali', 'hálószoba',
                    'szoba', 'helyiség', 'kamra', 'tároló', 'pince', 'tetőtér',
                    'm2', 'négyzetméter', 'quadratmeter'
                ],
                'pontszam': 2.0
            },
            
            'KOMFORT_EXTRA': {
                'kulcsszavak': [
                    'klíma', 'légkondi', 'szauna', 'medence', 'jakuzzi', 'wellness',
                    'hőszivattyú', 'napelem', 'okos otthon', 'riasztó', 'kamerás',
                    'központi porszívó', 'padlófűtés', 'geotermikus',
                    'hangosítás', 'internet', 'kábelezés', 'optika'
                ],
                'pontszam': 2.5
            },
            
            'ALLAPOT_FELUJITAS': {
                'kulcsszavak': [
                    'felújított', 'renovált', 'korszerűsített', 'új', 'frissen',
                    'most készült', 'újépítés', 'modernizált', 'átépített',
                    'beköltözhető', 'kulcsrakész', 'azonnal', 'költözés'
                ],
                'pontszam': 2.0
            },
            
            'LOKACIO_KORNYEZET': {
                'kulcsszavak': [
                    'csendes', 'békés', 'nyugodt', 'családi', 'villa negyed',
                    'központi', 'közel', 'közlekedés', 'iskola', 'óvoda',
                    'bolt', 'bevásárlás', 'játszótér', 'sport', 'erdő', 'domb'
                ],
                'pontszam': 1.5
            },
            
            'FUTES_ENERGIA': {
                'kulcsszavak': [
                    'gáz', 'távfűtés', 'kandalló', 'cserépkályha', 'fatűzés',
                    'energiatakarékos', 'szigetelt', 'alacsony rezsi',
                    'hőszigetelés', 'műanyag ablak', 'redőny'
                ],
                'pontszam': 1.2
            },
            
            'NEGATIV_TENYEZOK': {
                'kulcsszavak': [
                    'felújítandó', 'felújításra szorul', 'régi', 'rossz állapot',
                    'problémás', 'javítandó', 'cserélendő', 'hiányos',
                    'beázás', 'nedves', 'penész', 'rezsikölts', 'drága fűtés',
                    'forgalmas', 'zajos', 'busy'
                ],
                'pontszam': -1.5
            }
        }
    
    def clean_text(self, text):
        """Szöveg tisztítása és normalizálása"""
        if pd.isna(text):
            return ""
        text = str(text).lower()
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_category_scores(self, text):
        """Kategória pontszámok kinyerése egy szövegből"""
        clean_text = self.clean_text(text)
        
        scores = {}
        details = {}
        
        for kategoria, info in self.kategoriak.items():
            kulcsszavak = info['kulcsszavak']
            pontszam = info['pontszam']
            
            talalt_szavak = []
            ossz_pontszam = 0
            
            for kulcsszo in kulcsszavak:
                if kulcsszo in clean_text:
                    talalt_szavak.append(kulcsszo)
                    # Többszörösen előforduló szavak többet érnek
                    elofordulas = clean_text.count(kulcsszo)
                    ossz_pontszam += pontszam * elofordulas
            
            scores[kategoria] = ossz_pontszam
            details[kategoria] = {
                'talalt_szavak': talalt_szavak,
                'db': len(talalt_szavak),
                'pontszam': ossz_pontszam
            }
        
        return scores, details

class KomplettIngatlanPipeline:
    def __init__(self):
        self.search_url = ""
        self.location_name = ""
        self.list_csv_file = ""
        self.details_csv_file = ""
        self.dashboard_file = ""
        self.user_limit = 50  # Alapértelmezett limit
        
    def step_1_get_search_url(self):
        """1. LÉPÉS: URL bekérés és feldolgozási limit beállítás"""
        print("🏠 KOMPLETT INGATLAN ELEMZŐ PIPELINE")
        print("="*60)
        
        print("\n🔗 1. LÉPÉS: KERESÉSI URL MEGADÁSA")
        print("="*40)
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
            
            break
        
        # Feldolgozási limit bekérése
        print(f"\n" + "="*40)
        print("📊 FELDOLGOZÁSI LIMIT BEÁLLÍTÁSA")
        print("="*40)
        print("💡 Opciók:")
        print("   10   - Gyors teszt (2-3 perc)")
        print("   50   - Közepes minta (8-12 perc)")
        print("   100  - Nagy minta (15-25 perc)")
        print("   300  - Teljes állomány (45-90 perc)")
        
        while True:
            try:
                limit_input = input("\n📋 Hány hirdetést dolgozzak fel? (alapértelmezett: 50): ").strip()
                
                if not limit_input:
                    self.user_limit = 50
                    break
                else:
                    user_limit = int(limit_input)
                    if user_limit < 1:
                        print("❌ A limit legalább 1 legyen!")
                        continue
                    elif user_limit > 500:
                        print("⚠️  Nagy limit! Ajánlott maximum 300.")
                        confirm = input("Folytatod? (i/n): ").lower()
                        if confirm in ['i', 'igen', 'y', 'yes']:
                            self.user_limit = user_limit
                            break
                        else:
                            continue
                    else:
                        self.user_limit = user_limit
                        break
                        
            except ValueError:
                print("❌ Kérlek számot adj meg!")
                continue
        
        # URL feldolgozása - mindig 300-as limit az URL-ben (több mint szükséges)
        self.search_url = self._add_limit_300(url)
        self.location_name = self._extract_location(url)
        
        print(f"\n✅ Végleges URL: {self.search_url}")
        print(f"📍 Lokáció ID: {self.location_name}")
        print(f"🎯 Feldolgozandó hirdetések: {self.user_limit}")
        
        return True
    
    def _add_limit_300(self, url):
        """300-as limit hozzáadása az URL-hez"""
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            query_params['limit'] = ['300']
            new_query = urlencode(query_params, doseq=True)
            return urlunparse(parsed._replace(query=new_query))
        except:
            # Fallback módszer
            if 'limit=' in url:
                return re.sub(r'limit=\d+', 'limit=300', url)
            else:
                separator = '&' if '?' in url else '?'
                return f"{url}{separator}limit=300"
    
    def _extract_location(self, url):
        """Lokáció kinyerése URL-ből fájlnév generálásához"""
        try:
            path = urlparse(url).path
            # Keresési rész megtalálása
            path_parts = path.split('/')
            search_part = ""
            
            for part in path_parts:
                if any(word in part for word in ['elado', 'kiado', 'berlet']):
                    search_part = part
                    break
            
            if not search_part and path_parts:
                search_part = path_parts[-1]
            
            # Biztonságos fájlnév
            safe_name = re.sub(r'[^\w\-_+]', '_', search_part)
            safe_name = safe_name.replace('+', '_').replace('-', '_')
            return safe_name[:50] if safe_name else "ingatlan_kereses"
        except:
            return "ingatlan_kereses"
    
    async def step_2_list_scraping(self):
        """2. LÉPÉS: Lista scraping URL-alapú módszerrel"""
        print(f"\n" + "="*60)
        print("📋 2. LÉPÉS: INGATLAN LISTA SCRAPING")
        print("="*60)
        print(f"🎯 URL: {self.search_url}")
        print(f"📁 Lokáció: {self.location_name}")
        
        # URL-alapú scraper osztály
        scraper = UrlListScraper(self.search_url, self.location_name, self.user_limit)
        
        try:
            # Chrome kapcsolat
            if not await scraper.connect_to_chrome():
                print("❌ Chrome kapcsolat sikertelen!")
                print("💡 Indítsd el a Chrome-ot debug módban:")
                print("   chrome.exe --remote-debugging-port=9222")
                return False
            
            # Lista scraping
            properties = await scraper.scrape_property_list()
            
            if properties:
                # CSV mentése automatikus fájlnévvel
                self.list_csv_file = scraper.save_to_csv(properties)
                
                print(f"\n✅ LISTA SCRAPING SIKERES!")
                print(f"📁 Fájl: {self.list_csv_file}")
                print(f"📊 Ingatlanok: {len(properties)}")
                
                await scraper.close()
                return True
            else:
                print("❌ Nem sikerült ingatlanokat találni")
                await scraper.close()
                return False
                
        except Exception as e:
            print(f"❌ Lista scraping hiba: {e}")
            return False
    
    async def step_3_details_scraping(self):
        """3. LÉPÉS: Részletes scraping"""
        print(f"\n" + "="*60)
        print("🔍 3. LÉPÉS: RÉSZLETES SCRAPING")
        print("="*60)
        
        if not self.list_csv_file or not os.path.exists(self.list_csv_file):
            print("❌ Lista CSV nem található!")
            return False
        
        print(f"📊 Bemeneti CSV: {self.list_csv_file}")
        
        # Részletes scraper
        details_scraper = DetailedScraper(self.list_csv_file, self.location_name)
        
        try:
            # Részletes adatok gyűjtése
            detailed_data = await details_scraper.process_all_properties()
            
            if detailed_data:
                # CSV mentése automatikus fájlnévvel
                self.details_csv_file = details_scraper.save_to_csv(detailed_data)
                
                print(f"\n✅ RÉSZLETES SCRAPING SIKERES!")
                print(f"📁 Fájl: {self.details_csv_file}")
                print(f"📊 Részletes adatok: {len(detailed_data)}")
                
                await details_scraper.close()
                return True
            else:
                print("❌ Részletes scraping sikertelen")
                await details_scraper.close()
                return False
                
        except Exception as e:
            print(f"❌ Részletes scraping hiba: {e}")
            return False
    
    def step_4_create_dashboard(self):
        """4. LÉPÉS: Dashboard generálás"""
        print(f"\n" + "="*60)
        print("🎨 4. LÉPÉS: DASHBOARD GENERÁLÁS")
        print("="*60)
        
        if not self.details_csv_file or not os.path.exists(self.details_csv_file):
            print("❌ Részletes CSV nem található!")
            return False
        
        try:
            # Dashboard fájlnév
            self.dashboard_file = f"dashboard_{self.location_name}.py"
            
            print(f"📊 Adatforrás: {self.details_csv_file}")
            print(f"🎨 Dashboard: {self.dashboard_file}")
            
            # Template beolvasása és testreszabása
            success = self._create_custom_dashboard()
            
            if success:
                print(f"\n✅ DASHBOARD GENERÁLÁS SIKERES!")
                print(f"📁 Dashboard fájl: {self.dashboard_file}")
                print(f"\n🚀 DASHBOARD INDÍTÁSA:")
                print(f"   streamlit run {self.dashboard_file}")
                return True
            else:
                print("❌ Dashboard generálás sikertelen")
                return False
                
        except Exception as e:
            print(f"❌ Dashboard hiba: {e}")
            return False
    
    def _create_custom_dashboard(self):
        """Dashboard template testreszabása"""
        try:
            # Template beolvasása
            if not os.path.exists('ingatlan_dashboard_advanced.py'):
                print("❌ Dashboard template nem található!")
                return False
            
            with open('ingatlan_dashboard_advanced.py', 'r', encoding='utf-8') as f:
                template = f.read()
            
            # Lokáció név formázása megjelenítéshez
            display_name = self.location_name.replace('_', ' ').title()
            display_name = re.sub(r'\bElado\b', 'Eladó', display_name)
            display_name = re.sub(r'\bHaz\b', 'Ház', display_name) 
            display_name = re.sub(r'\bLakas\b', 'Lakás', display_name)
            
            # Template módosítások
            customizations = {
                # Címek
                r'🏠 Kőbánya-Újhegyi Lakótelep - Részletes Piaci Elemzés': f'🏠 {display_name} - Részletes Piaci Elemzés',
                r'Kőbánya-Újhegyi Lakótelep': display_name,
                r'KŐBÁNYA-ÚJHEGYI LAKÓTELEP': display_name.upper(),
                r'Kőbánya-Újhegy': display_name,
                
                # CSV fájl referencia
                r'ingatlan_reszletes_\d{8}_\d{6}\.csv': self.details_csv_file,
                
                # Szöveges említések  
                r'a Kőbánya-Újhegyi lakótelepről': f'a(z) {display_name} területről',
                r'Kőbánya X\. kerület, Újhegyi lakótelep': f'{display_name} környéke',
                
                # Page config
                r'🏠 Kőbánya-Újhegy Ingatlan Piaci Elemzés': f'🏠 {display_name} Piaci Elemzés'
            }
            
            # Módosítások alkalmazása
            customized = template
            for pattern, replacement in customizations.items():
                customized = re.sub(pattern, replacement, customized)
            
            # Load_data függvény egyszerűsítése
            load_data_new = f'''def load_data():
    """Adatok betöltése"""
    try:
        df = pd.read_csv("{self.details_csv_file}", encoding='utf-8-sig')
        
        # Alapvető ellenőrzések
        if 'link' not in df.columns:
            st.error("Hiányzó oszlop: link")
            return pd.DataFrame()
        
        # Numerikus konverziók
        for col in ['ar_szam', 'teljes_ar_szam', 'terulet_szam', 'szobak']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
        
    except FileNotFoundError:
        st.error("CSV fájl nem található!")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Betöltési hiba: {{e}}")
        return pd.DataFrame()'''
            
            # Load_data csere
            customized = re.sub(
                r'def load_data\(\):.*?return pd\.DataFrame\(\)',
                load_data_new,
                customized,
                flags=re.DOTALL
            )
            
            # Dashboard mentése
            with open(self.dashboard_file, 'w', encoding='utf-8') as f:
                f.write(customized)
            
            return True
            
        except Exception as e:
            print(f"❌ Template hiba: {e}")
            return False
    
    async def run_complete_pipeline(self):
        """Teljes pipeline futtatása"""
        try:
            print("🚀 KOMPLETT PIPELINE INDÍTÁSA")
            
            # 1. URL bekérés
            if not self.step_1_get_search_url():
                return False
            
            # 2. Lista scraping
            print(f"\n⏳ Lista scraping indítása...")
            if not await self.step_2_list_scraping():
                print("❌ Pipeline leállítva - lista scraping sikertelen")
                return False
            
            # 3. Részletes scraping
            print(f"\n⏳ Részletes scraping indítása...")
            if not await self.step_3_details_scraping():
                print("❌ Pipeline leállítva - részletes scraping sikertelen")  
                return False
            
            # 4. Dashboard
            if not self.step_4_create_dashboard():
                print("❌ Pipeline leállítva - dashboard sikertelen")
                return False
            
            # Sikeres befejezés
            self._show_final_summary()
            return True
            
        except KeyboardInterrupt:
            print(f"\n⏸️ Pipeline megszakítva!")
            return False
        except Exception as e:
            print(f"❌ Pipeline hiba: {e}")
            return False
    
    def _show_final_summary(self):
        """Végső összefoglaló"""
        print(f"\n" + "🎉"*20)
        print("✅ PIPELINE SIKERESEN BEFEJEZVE!")
        print("🎉"*20)
        
        print(f"\n📋 EREDMÉNYEK:")
        print(f"   🔗 Keresési URL: {self.search_url}")
        print(f"   📊 Lista CSV: {self.list_csv_file}")
        print(f"   🔍 Részletes CSV: {self.details_csv_file}")
        print(f"   🎨 Dashboard: {self.dashboard_file}")
        
        print(f"\n🚀 KÖVETKEZŐ LÉPÉS:")
        print(f"   streamlit run {self.dashboard_file}")
        
        # Statisztikák
        try:
            if os.path.exists(self.details_csv_file):
                df = pd.read_csv(self.details_csv_file)
                print(f"\n📈 STATISZTIKÁK:")
                print(f"   📍 Összesen: {len(df)} ingatlan")
                if 'szint' in df.columns:
                    floor_count = df['szint'].notna().sum()
                    print(f"   🏢 Emelet adat: {floor_count}/{len(df)} ({floor_count/len(df)*100:.1f}%)")
                if 'hirdeto_tipus' in df.columns:
                    adv_count = df['hirdeto_tipus'].notna().sum()
                    print(f"   👤 Hirdető típus: {adv_count}/{len(df)} ({adv_count/len(df)*100:.1f}%)")
        except:
            pass

# URL-alapú lista scraper
class UrlListScraper:
    def __init__(self, search_url, location_name, user_limit=50):
        self.search_url = search_url
        self.location_name = location_name
        self.user_limit = user_limit
        self.playwright = None
        self.browser = None
        self.page = None
    
    async def connect_to_chrome(self):
        """Chrome kapcsolat létrehozása"""
        try:
            print("🔗 Chrome kapcsolat létrehozása...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.connect_over_cdp("http://localhost:9222")
            
            # Aktív tab
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                pages = self.context.pages
                if pages:
                    self.page = pages[0]
                else:
                    self.page = await self.context.new_page()
            else:
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
            
            print("✅ Chrome kapcsolat OK")
            return True
            
        except Exception as e:
            print(f"❌ Chrome kapcsolat hiba: {e}")
            return False
    
    async def scrape_property_list(self):
        """Ingatlan lista scraping javított szelektorokkal"""
        try:
            print(f"🌐 Navigálás: {self.search_url}")
            
            # Több próbálkozás robusztusabb betöltéssel
            for attempt in range(3):
                try:
                    print(f"  📡 Próbálkozás {attempt + 1}/3...")
                    await self.page.goto(self.search_url, wait_until='domcontentloaded', timeout=60000)
                    await asyncio.sleep(5)
                    
                    # Ellenőrizzük, hogy betöltődött-e a tartalom
                    content = await self.page.content()
                    if len(content) > 10000 and 'ingatlan' in content.lower():
                        print(f"  ✅ Oldal betöltve ({len(content)} karakter)")
                        break
                    elif attempt < 2:
                        print(f"  ⚠️ Nem teljes betöltés, újrapróbálás...")
                        continue
                except Exception as e:
                    print(f"  ❌ {attempt + 1}. próbálkozás hiba: {e}")
                    if attempt < 2:
                        await asyncio.sleep(3)
                        continue
                    else:
                        raise
            
            # Listing elemek keresése - ingatlan_list_scraper_refactored szelektorok alapján
            print("🔍 Ingatlan elemek keresése...")
            
            # Különböző szelektorok próbálása
            selectors = [
                ".listing-card",
                ".js-listing", 
                "[data-id]",
                ".results-list-item",
                ".search-result",
                ".listing",
                "a[href*='/ingatlan/']"
            ]
            
            property_elements = []
            used_selector = ""
            
            for selector in selectors:
                elements = await self.page.query_selector_all(selector)
                if elements and len(elements) > 3:  # Minimum 3 elem kell
                    property_elements = elements
                    used_selector = selector
                    print(f"✅ {len(elements)} elem találva ({selector})")
                    break
                elif elements:
                    print(f"  🔍 {len(elements)} elem találva ({selector}) - kevés")
            
            if not property_elements:
                # Debug info
                print("❌ Nincsenek ingatlan elemek, debug info:")
                page_title = await self.page.title()
                print(f"  📄 Oldal cím: {page_title}")
                
                # Próbálkozzunk közvetlenül linkekkel
                all_links = await self.page.query_selector_all("a[href]")
                ingatlan_links = []
                
                for link in all_links:
                    href = await link.get_attribute("href")
                    if href and '/ingatlan/' in href:
                        ingatlan_links.append(link)
                
                if ingatlan_links:
                    property_elements = ingatlan_links
                    print(f"✅ {len(ingatlan_links)} ingatlan link találva közvetlen kereséssel")
                else:
                    return []
            
            # Adatok kinyerése - user által megadott limit szerint
            properties = []
            
            # User limit alkalmazása
            max_elements = min(len(property_elements), self.user_limit)
            limited_elements = property_elements[:max_elements]
            
            print(f"🎯 FELDOLGOZÁS: {len(limited_elements)}/{len(property_elements)} ingatlan (user limit: {self.user_limit})")
            
            for i, element in enumerate(limited_elements, 1):
                try:
                    # Link kinyerése
                    link_element = element
                    href = await link_element.get_attribute("href")
                    
                    # Ha nincs href az elemen, keressünk link-et benne
                    if not href:
                        link_element = await element.query_selector("a[href*='/ingatlan/']")
                        if not link_element:
                            continue
                        href = await link_element.get_attribute("href")
                        
                    if not href:
                        continue
                        
                    # Teljes URL létrehozása
                    if href.startswith('/'):
                        full_url = f"https://ingatlan.com{href}"
                    else:
                        full_url = href
                    
                    # Alapadatok kinyerése a listából
                    property_data = {
                        'id': i,
                        'link': full_url
                    }
                    
                    # Cím kinyerése - specifikus selector alapján
                    try:
                        # Cím a .text-gray-900 osztályban
                        cim_elem = await element.query_selector('.text-gray-900')
                        if cim_elem:
                            property_data['cim'] = await cim_elem.inner_text()
                        else:
                            property_data['cim'] = ""
                    except:
                        property_data['cim'] = ""
                    
                    # Ár kinyerése - specifikus selector: .fw-bold.fs-5.text-onyx
                    try:
                        price_elem = await element.query_selector('.fw-bold.fs-5.text-onyx')
                        if price_elem:
                            property_data['teljes_ar'] = await price_elem.inner_text()
                        else:
                            property_data['teljes_ar'] = ""
                    except:
                        property_data['teljes_ar'] = ""
                    
                    # Négyzetméter ár - .listing-card-area-prices osztályból
                    try:
                        m2_price_elem = await element.query_selector('.listing-card-area-prices')
                        if m2_price_elem:
                            property_data['nm_ar'] = await m2_price_elem.inner_text()
                        else:
                            property_data['nm_ar'] = ""
                    except:
                        property_data['nm_ar'] = ""
                    
                    # Alapterület kinyerése - specifikus logikával
                    property_data['terulet'] = ""
                    try:
                        # Keressük az "Alapterület" szöveg mellett lévő értéket
                        all_spans = await element.query_selector_all('span')
                        for i, span in enumerate(all_spans):
                            text = await span.inner_text()
                            if 'Alapterület' in text and i + 1 < len(all_spans):
                                next_span = all_spans[i + 1]
                                area_text = await next_span.inner_text()
                                if 'm' in area_text:
                                    property_data['terulet'] = area_text
                                    break
                    except:
                        pass
                    
                    # Telekterület kinyerése - specifikus selector és fallback
                    property_data['telekterulet'] = ""
                    try:
                        # 1. Próba: Specifikus selector a megadott HTML alapján
                        # <span class="fs-6 text-gray-900 fw-bold">1022 m<sup>2</sup></span>
                        telekterulet_selectors = [
                            'span.fs-6.text-gray-900.fw-bold',
                            'span.text-gray-900.fw-bold',
                            '.fs-6.text-gray-900.fw-bold'
                        ]
                        
                        telekterulet_found = False
                        for tel_selector in telekterulet_selectors:
                            if telekterulet_found:
                                break
                            tel_spans = await element.query_selector_all(tel_selector)
                            for tel_span in tel_spans:
                                tel_text = await tel_span.inner_text()
                                # Keressük azokat amelyek m² -rel végződnek és számot tartalmaznak
                                if tel_text and ('m²' in tel_text or 'm2' in tel_text) and any(char.isdigit() for char in tel_text):
                                    # Telekterület általában nagyobb szám mint alapterület
                                    import re
                                    numbers = re.findall(r'\d+', tel_text)
                                    if numbers and int(numbers[0]) > 200:  # Telekterület általában 200+ m²
                                        property_data['telekterulet'] = tel_text
                                        telekterulet_found = True
                                        break
                        
                        # 2. Fallback: Eredeti logika - "Telekterület" szöveg keresése
                        if not property_data['telekterulet']:
                            all_spans = await element.query_selector_all('span')
                            for i, span in enumerate(all_spans):
                                text = await span.inner_text()
                                if 'Telekterület' in text and i + 1 < len(all_spans):
                                    next_span = all_spans[i + 1]
                                    plot_text = await next_span.inner_text()
                                    if 'm' in plot_text:
                                        property_data['telekterulet'] = plot_text
                                        break
                                        
                    except:
                        pass
                    
                    # Szobák száma - specifikus logikával
                    property_data['szobak'] = ""
                    try:
                        all_spans = await element.query_selector_all('span')
                        for i, span in enumerate(all_spans):
                            text = await span.inner_text()
                            if 'Szobák' in text and i + 1 < len(all_spans):
                                next_span = all_spans[i + 1]
                                room_text = await next_span.inner_text()
                                if '+' in room_text or 'szoba' in room_text.lower():
                                    property_data['szobak'] = room_text
                                    break
                    except:
                        pass
                    
                    # Képek száma - gallery-additional-photos-label-ből
                    property_data['kepek_szama'] = 0
                    try:
                        gallery_elem = await element.query_selector('.gallery-additional-photos-label')
                        if gallery_elem:
                            span_elem = await gallery_elem.query_selector('span')
                            if span_elem:
                                kepek_szam_text = await span_elem.inner_text()
                                property_data['kepek_szama'] = int(kepek_szam_text.strip())
                    except:
                        # Ha nincs gallery label, akkor 1 kép (alapértelmezett)
                        property_data['kepek_szama'] = 1
                    
                    # NÉGYZETMÉTER ÁR - már kinyertük fentebb, de számoljuk újra ha kell
                    if not property_data['nm_ar'] and property_data['teljes_ar'] and property_data['terulet']:
                        try:
                            price_num = self._extract_price_number(property_data['teljes_ar'])
                            area_num = self._extract_area_number(property_data['terulet'])
                            
                            if price_num and area_num:
                                price_per_sqm = int(price_num / area_num)
                                property_data['nm_ar'] = f"{price_per_sqm:,} Ft/m²".replace(',', ' ')
                                
                        except Exception:
                            # Nem kritikus hiba
                            pass
                    
                    properties.append(property_data)
                    
                    # Debug info az első néhány elemhez
                    if len(properties) <= 3:
                        print(f"    ✅ {len(properties)}. ingatlan: {property_data.get('cim', '')[:40]}...")
                    
                    if i % 5 == 0:
                        print(f"  📋 Feldolgozva: {i}/{len(limited_elements)} (összesített: {len(properties)})")
                        
                except Exception as e:
                    print(f"  ⚠️ {i}. elem feldolgozási hiba: {str(e)[:50]}...")
                    continue
            
            print(f"✅ Lista scraping kész: {len(properties)} ingatlan")
            return properties
            
        except Exception as e:
            print(f"❌ Lista scraping hiba: {e}")
            return []
    
    def _extract_price_number(self, price_text):
        """Ár szám kinyerése"""
        try:
            numbers = re.findall(r'[\d,\.]+', price_text.replace(' ', ''))
            if numbers:
                num_str = numbers[0].replace(',', '.')
                num_value = float(num_str)
                
                if 'M' in price_text.upper():
                    num_value *= 1_000_000
                elif 'MRD' in price_text.upper():
                    num_value *= 1_000_000_000
                
                return num_value
        except:
            pass
        return None
    
    def _extract_area_number(self, area_text):
        """Terület szám kinyerése"""
        try:
            numbers = re.findall(r'[\d,\.]+', area_text.replace(' ', ''))
            if numbers:
                num_str = numbers[0].replace(',', '.')
                return float(num_str)
        except:
            pass
        return None
    
    def save_to_csv(self, properties):
        """CSV mentés automatikus fájlnévvel"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ingatlan_lista_{self.location_name}_{timestamp}.csv"
            
            df = pd.DataFrame(properties)
            
            # Oszlop sorrend
            columns = ['id', 'cim', 'teljes_ar', 'nm_ar', 'terulet', 'telekterulet', 'szobak', 'kepek_szama', 'link']
            available_columns = [col for col in columns if col in df.columns]
            df = df[available_columns]
            
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            print(f"💾 Lista CSV mentve: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ CSV mentési hiba: {e}")
            return None
    
    async def close(self):
        """Kapcsolat bezárása"""
        try:
            if self.playwright:
                await self.playwright.stop()
        except:
            pass

# Részletes scraper
class DetailedScraper:
    def __init__(self, list_csv_file, location_name):
        self.list_csv_file = list_csv_file
        self.location_name = location_name
        self.playwright = None
        self.browser = None
        self.page = None
    
    async def process_all_properties(self):
        """Összes ingatlan részletes feldolgozása"""
        # CSV beolvasás
        try:
            df = pd.read_csv(self.list_csv_file)
            print(f"📊 CSV beolvasva: {len(df)} ingatlan")
        except Exception as e:
            print(f"❌ CSV hiba: {e}")
            return []
        
        if 'link' not in df.columns:
            print("❌ Nincs 'link' oszlop!")
            return []
        
        # Chrome kapcsolat
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.connect_over_cdp("http://localhost:9222")
            
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                pages = self.context.pages
                self.page = pages[0] if pages else await self.context.new_page()
            else:
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
                
            print("✅ Chrome kapcsolat részletes scraperhez OK")
            
        except Exception as e:
            print(f"❌ Chrome kapcsolat hiba: {e}")
            return []
        
        # Részletes scraping
        detailed_data = []
        urls = df['link'].dropna().tolist()
        
        for i, url in enumerate(urls, 1):
            try:
                print(f"\n🏠 {i}/{len(urls)}: {url}")
                
                # Alapadatok az eredeti CSV-ből
                original_data = df[df['link'] == url].iloc[0].to_dict()
                
                # Részletes adatok
                details = await self._scrape_single_property(url)
                
                # Kombináció
                combined = {**original_data, **details}
                detailed_data.append(combined)
                
                # Humanizált várakozás
                if i < len(urls):
                    wait_time = random.uniform(2.0, 4.0)
                    print(f"  ⏰ Várakozás {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                print(f"  ❌ Hiba: {e}")
                # Üres részletes adatok hozzáadása
                empty_details = self._get_empty_details()
                combined = {**original_data, **empty_details}
                detailed_data.append(combined)
                continue
        
        return detailed_data
    
    async def _scrape_single_property(self, url):
        """Egyetlen ingatlan részletes scraping - enhanced logikával"""
        details = {}
        
        try:
            print(f"  🏠 Adatlap: {url}")
            
            # Navigálás
            await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(random.uniform(2.0, 3.0))
            
            # Részletes cím
            try:
                address_selectors = ["h1.text-onyx", ".property-address h1", ".listing-header h1", "h1", ".address"]
                for selector in address_selectors:
                    elem = await self.page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text.strip():
                            details['reszletes_cim'] = text.strip()
                            break
                else:
                    details['reszletes_cim'] = ""
            except:
                details['reszletes_cim'] = ""
            
            # Részletes ár
            try:
                price_selectors = [".price-value", ".property-price .text-onyx", ".listing-price", "[data-testid='price']", ".price"]
                for selector in price_selectors:
                    elem = await self.page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text.strip():
                            details['reszletes_ar'] = text.strip()
                            break
                else:
                    details['reszletes_ar'] = ""
            except:
                details['reszletes_ar'] = ""
            
            # Táblázatos adatok - PRIORITÁS: állapot és emelet
            table_data = {}
            try:
                data_rows = await self.page.query_selector_all("table.table-borderless tr")
                
                for row in data_rows:
                    try:
                        label_element = await row.query_selector("td:first-child span")
                        if not label_element:
                            label_element = await row.query_selector("td:first-child")
                        
                        value_element = await row.query_selector("td.fw-bold")
                        if not value_element:
                            value_element = await row.query_selector("td:nth-child(2)")
                        
                        if label_element and value_element:
                            label = (await label_element.inner_text()).strip().lower()
                            value = (await value_element.inner_text()).strip()
                            
                            # Kihagyja az üres értékeket
                            if not value or "nincs megadva" in value.lower():
                                continue
                            
                            # Prioritásos mezők
                            if 'ingatlan állapota' in label or 'állapot' in label:
                                table_data['ingatlan_allapota'] = value
                                print(f"    🎯 Állapot: {value}")
                            elif 'szint' in label and 'szintjei' not in label:
                                table_data['szint'] = value
                                print(f"    🎯 Szint: {value}")
                            elif 'emelet' in label:
                                table_data['szint'] = value
                                print(f"    🎯 Emelet: {value}")
                            elif 'építés éve' in label:
                                table_data['epitesi_ev'] = value
                            elif 'fűtés' in label:
                                table_data['futes'] = value
                            elif 'erkély' in label:
                                table_data['erkely'] = value
                            elif 'parkolás' in label:
                                table_data['parkolas'] = value
                            elif 'energetikai' in label:
                                table_data['energetikai'] = value
                                
                    except:
                        continue
                        
            except:
                pass
            
            # Alapértelmezett táblázatos adatok
            details.update({
                'epitesi_ev': table_data.get('epitesi_ev', ''),
                'szint': table_data.get('szint', ''),
                'ingatlan_allapota': table_data.get('ingatlan_allapota', ''),
                'futes': table_data.get('futes', ''),
                'erkely': table_data.get('erkely', ''),
                'parkolas': table_data.get('parkolas', ''),
                'energetikai': table_data.get('energetikai', '')
            })
            
            # Leírás
            try:
                desc_selectors = ["#listing-description", ".listing-description", ".property-description", "[data-testid='description']"]
                for selector in desc_selectors:
                    elem = await self.page.query_selector(selector)
                    if elem:
                        desc_text = await elem.inner_text()
                        if desc_text.strip():
                            # Rövidítés
                            if len(desc_text) > 800:
                                desc_text = desc_text[:800] + "..."
                            details['leiras'] = desc_text.strip()
                            break
                else:
                    details['leiras'] = ""
            except:
                details['leiras'] = ""
            
            # HIRDETŐ TÍPUS MEGHATÁROZÁSA - ELSŐDLEGES FORRÁS: oldalon lévő jelölés
            details['hirdeto_tipus'] = await self._determine_advertiser_type_from_page()
            
            # Ha nem sikerült az oldalról, akkor szemantikai elemzés
            if details['hirdeto_tipus'] == "ismeretlen" and details['leiras']:
                details['hirdeto_tipus'] = self._detect_advertiser_type(details['leiras'])
            
            # Ha még mindig ismeretlen, akkor alapértelmezett
            if details['hirdeto_tipus'] == "ismeretlen":
                details['hirdeto_tipus'] = "bizonytalan"
                
            print(f"    👤 Hirdető: {details['hirdeto_tipus']}")
            
            # További mezők alapértékekkel
            additional_fields = ['ingatlanos', 'telefon', 'allapot', 'epulet_szintjei', 
                               'kilatas', 'parkolohely_ara', 'komfort', 'legkondicionalas',
                               'akadalymentesites', 'furdo_wc', 'tetoter', 'pince', 
                               'parkolo', 'tajolas', 'kert', 'napelem', 'szigeteles', 'rezsikoltség']
            
            for field in additional_fields:
                if field not in details:
                    details[field] = ""
            
            print(f"  ✅ Kinyert mezők: {len([v for v in details.values() if v])}")
            return details
            
        except Exception as e:
            print(f"  ❌ Scraping hiba: {e}")
            return self._get_empty_details()
    
    async def _determine_advertiser_type_from_page(self):
        """Egyszerűsített hirdető típus azonosítás - csak a pontos HTML elem alapján"""
        try:
            # Keressük a pontos szelektort
            # <span class="d-flex align-items-center text-start h-100 my-auto fw-bold fs-6">Magánszemély</span>
            
            selectors = [
                # Pontos selector a megadott struktúra alapján
                'span.d-flex.align-items-center.text-start.h-100.my-auto.fw-bold.fs-6',
                # Alternatív selectorok ha a pontos nem működik
                'span.fw-bold.fs-6',
                '.fw-bold.fs-6',
                # Általános span keresés
                'span'
            ]
            
            for selector in selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        text = await element.inner_text()
                        if text and text.strip():
                            text_clean = text.strip()
                            
                            # CSAK akkor magánszemély, ha pontosan "Magánszemély" szöveget találunk
                            if text_clean == 'Magánszemély':
                                print(f"    🎯 HTML-ből azonosítva: Magánszemély")
                                return "maganszemely"
                                
                            # Ha ingatlaniroda vagy egyéb professional kifejezés
                            elif any(word in text_clean.lower() for word in [
                                'ingatlaniroda', 'ingatlan iroda', 'közvetítő', 'kozvetito',
                                'ügynök', 'ugynoк', 'irodа', 'professional'
                            ]):
                                print(f"    🎯 HTML-ből azonosítva: {text_clean}")
                                return "ingatlaniroda"
                                
                except Exception:
                    continue
            
            # Ha nem találtunk semmit, akkor ismeretlen
            return "ismeretlen"
            
        except Exception as e:
            print(f"    ⚠️ HTML hirdető típus hiba: {e}")
            return "ismeretlen"

    def _detect_advertiser_type(self, description):
        """Szemantikai alapú hirdető típus meghatározása nagynyelvű elemzéssel"""
        if not description:
            return "ismeretlen"
        
        desc_lower = description.lower()
        
        # ERŐS MAGÁNSZEMÉLY JELZŐK (ezek felülírják az ingatlaniroda jelzőket)
        strong_private_indicators = [
            'ingatlanközvetítő', 'közvetítő', 'ingatlanosok ne', 'ne keressenek',
            'iroda ne', 'ügynök ne', 'ne hívjanak', 'tulajdonos vagyok',
            'saját ingatlan', 'költözés miatt', 'családi ok', 'sürgős eladás',
            'kénytelen vagyok', 'gyorsan el kell', 'magántulajdon',
            'nem vagyok ingatlanközvetítő', 'magánszemély hirdet'
        ]
        
        # ERŐS INGATLANIRODA JELZŐK
        strong_agency_indicators = [
            'kft', 'bt', 'zrt', 'kht', 'nonprofit', 'iroda', 'ingatlan kft',
            'real estate', 'property', 'ingatlanforgalmazó', 'jutalék',
            'közvetítés', 'ügynökség', 'társaság', 'vállalat', 'cég',
            'keressen minket', 'irodánk', 'ügynökünk', 'képviseli',
            'kínáljuk megvételre', 'kínálunk eladásra', 'portfóliónk',
            'referencia ingatlan', 'ügyfelünk', 'megbízásból'
        ]
        
        # KÖZEPESEN ERŐS MAGÁNSZEMÉLY JELZŐK
        moderate_private_indicators = [
            'személyes', 'magán', 'saját', 'tulajdonos', 'eladó vagyok',
            'azonnali', 'sürgős', 'gyorsan', 'költözünk', 'elköltözünk',
            'családunk', 'otthonunk', 'házunk', 'lakásunk', 'ingatlanukat',
            'nyugdíjba', 'külföldre', 'nagyobb házba'
        ]
        
        # KÖZEPESEN ERŐS INGATLANIRODA JELZŐK  
        moderate_agency_indicators = [
            'értékbecslés', 'szakértő', 'tanácsadó', 'szolgáltatás',
            'befektetés', 'ajánlat', 'kínálat', 'megtekintés',
            'időpont egyeztetés', 'bemutató', 'prezentáció', 'marketing',
            'tapasztalat', 'gyakorlat', 'több éves', 'professionális',
            'megbízható', 'hiteles', 'garancia'
        ]
        
        # PONTSZÁMÍTÁS
        strong_private_score = sum(1 for indicator in strong_private_indicators 
                                 if indicator in desc_lower)
        
        strong_agency_score = sum(1 for indicator in strong_agency_indicators 
                                if indicator in desc_lower)
        
        moderate_private_score = sum(1 for indicator in moderate_private_indicators 
                                   if indicator in desc_lower) * 0.5
        
        moderate_agency_score = sum(1 for indicator in moderate_agency_indicators 
                                  if indicator in desc_lower) * 0.5
        
        # VÉGSŐ PONTSZÁMOK
        total_private_score = strong_private_score * 3 + moderate_private_score
        total_agency_score = strong_agency_score * 2 + moderate_agency_score
        
        # DÖNTÉSI LOGIKA
        # Ha van ERŐS magánszemély jelző, akkor magánszemély (felülírja az ingatlaniroda jelzőket)
        if strong_private_score > 0:
            return "maganszemely"
        
        # Ha van ERŐS ingatlaniroda jelző, akkor ingatlaniroda
        if strong_agency_score > 0:
            return "ingatlaniroda" 
        
        # Ha nincs erős jelző, akkor a pontszámok alapján
        if total_private_score > total_agency_score + 0.5:
            return "maganszemely"
        elif total_agency_score > total_private_score + 0.5:
            return "ingatlaniroda"
        
        # HOSSZÚSÁG ALAPÚ HEURISZTIKA (hosszabb leírás általában ingatlaniroda)
        if len(description) > 800:
            return "ingatlaniroda"
        elif len(description) < 200:
            return "maganszemely"
        
        # SPECIFIKUS MINTÁK KERESÉSE
        # Személyes hangvétel keresése
        personal_patterns = ['vagyok', 'vagyunk', 'családunk', 'otthonunk', 'házunk']
        personal_count = sum(1 for pattern in personal_patterns if pattern in desc_lower)
        
        # Formális/üzleti hangvétel keresése
        business_patterns = ['kínáljuk', 'ajánljuk', 'várjuk', 'keresse', 'forduljon']
        business_count = sum(1 for pattern in business_patterns if pattern in desc_lower)
        
        if personal_count > business_count:
            return "maganszemely" 
        elif business_count > personal_count:
            return "ingatlaniroda"
        
        return "bizonytalan"
    
    def _get_empty_details(self):
        """Üres adatstruktúra"""
        return {
            'reszletes_cim': '', 'reszletes_ar': '', 'epitesi_ev': '', 'szint': '',
            'allapot': '', 'ingatlan_allapota': '', 'epulet_szintjei': '', 'kilatas': '',
            'parkolas': '', 'parkolohely_ara': '', 'komfort': '', 'legkondicionalas': '',
            'akadalymentesites': '', 'furdo_wc': '', 'tetoter': '', 'pince': '',
            'futes': '', 'erkely': '', 'parkolo': '', 'energetikai': '',
            'tajolas': '', 'kert': '', 'napelem': '', 'szigeteles': '', 'rezsikoltség': '',
            'leiras': '', 'ingatlanos': '', 'telefon': '', 'hirdeto_tipus': '', 'kepek_szama': 0
        }
    
    def save_to_csv(self, detailed_data):
        """Részletes CSV mentés Enhanced Text Feature-kkel"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"ingatlan_reszletes_{self.location_name}_{timestamp}.csv"
            enhanced_filename = f"ingatlan_reszletes_enhanced_text_features.csv"
            
            df = pd.DataFrame(detailed_data)
            
            # Oszlop sorrend
            priority_cols = ['id', 'cim', 'reszletes_cim', 'teljes_ar', 'reszletes_ar', 
                           'terulet', 'nm_ar', 'szobak', 'epitesi_ev', 'szint', 
                           'ingatlan_allapota', 'futes', 'erkely', 'parkolas', 
                           'hirdeto_tipus', 'kepek_szama', 'leiras', 'link']
            
            available_priority = [col for col in priority_cols if col in df.columns]
            other_cols = [col for col in df.columns if col not in available_priority]
            
            final_columns = available_priority + other_cols
            df = df[final_columns]
            
            # Alap CSV mentése (backup)
            df.to_csv(base_filename, index=False, encoding='utf-8-sig')
            print(f"💾 Alap CSV mentve: {base_filename}")
            
            # 🌟 ENHANCED TEXT FEATURES GENERÁLÁS
            print(f"� Enhanced text feature-k generálása...")
            
            # Szövegelemző inicializálása
            analyzer = IngatlanSzovegelemzo()
            
            # Új oszlopok inicializálása
            text_feature_columns = {
                'luxus_minoseg_pont': 0.0,
                'kert_kulso_pont': 0.0,
                'parkolas_garage_pont': 0.0,
                'terulet_meret_pont': 0.0,
                'komfort_extra_pont': 0.0,
                'allapot_felujitas_pont': 0.0,
                'lokacio_kornyezet_pont': 0.0,
                'futes_energia_pont': 0.0,
                'negativ_tenyezok_pont': 0.0,
                
                # Dummy változók (0/1)
                'van_luxus_kifejezés': 0,
                'van_kert_terulet': 0,
                'van_garage_parkolas': 0,
                'van_komfort_extra': 0,
                'van_negativ_elem': 0,
                
                # Összesített pontszámok
                'ossz_pozitiv_pont': 0.0,
                'ossz_negativ_pont': 0.0,
                'netto_szoveg_pont': 0.0
            }
            
            # Oszlopok hozzáadása
            for col_name, default_value in text_feature_columns.items():
                df[col_name] = default_value
            
            # Text feature-k generálása minden sorhoz
            processed_count = 0
            for idx, row in df.iterrows():
                if pd.notna(row.get('leiras', '')):
                    # Kategória pontszámok kinyerése
                    scores, details = analyzer.extract_category_scores(row['leiras'])
                    
                    # Pontszámok mentése
                    df.at[idx, 'luxus_minoseg_pont'] = scores.get('LUXUS_MINOSEG', 0)
                    df.at[idx, 'kert_kulso_pont'] = scores.get('KERT_KULSO', 0)
                    df.at[idx, 'parkolas_garage_pont'] = scores.get('PARKOLAS_GARAGE', 0)
                    df.at[idx, 'terulet_meret_pont'] = scores.get('TERULET_MERET', 0)
                    df.at[idx, 'komfort_extra_pont'] = scores.get('KOMFORT_EXTRA', 0)
                    df.at[idx, 'allapot_felujitas_pont'] = scores.get('ALLAPOT_FELUJITAS', 0)
                    df.at[idx, 'lokacio_kornyezet_pont'] = scores.get('LOKACIO_KORNYEZET', 0)
                    df.at[idx, 'futes_energia_pont'] = scores.get('FUTES_ENERGIA', 0)
                    df.at[idx, 'negativ_tenyezok_pont'] = scores.get('NEGATIV_TENYEZOK', 0)
                    
                    # Dummy változók
                    df.at[idx, 'van_luxus_kifejezés'] = 1 if scores.get('LUXUS_MINOSEG', 0) > 0 else 0
                    df.at[idx, 'van_kert_terulet'] = 1 if scores.get('KERT_KULSO', 0) > 0 else 0
                    df.at[idx, 'van_garage_parkolas'] = 1 if scores.get('PARKOLAS_GARAGE', 0) > 0 else 0
                    df.at[idx, 'van_komfort_extra'] = 1 if scores.get('KOMFORT_EXTRA', 0) > 0 else 0
                    df.at[idx, 'van_negativ_elem'] = 1 if scores.get('NEGATIV_TENYEZOK', 0) < 0 else 0
                    
                    # Összesített pontszámok
                    pozitiv_kategoriak = ['LUXUS_MINOSEG', 'KERT_KULSO', 'PARKOLAS_GARAGE', 
                                         'TERULET_MERET', 'KOMFORT_EXTRA', 'ALLAPOT_FELUJITAS',
                                         'LOKACIO_KORNYEZET', 'FUTES_ENERGIA']
                    
                    ossz_pozitiv = sum(max(0, scores.get(k, 0)) for k in pozitiv_kategoriak)
                    ossz_negativ = abs(min(0, scores.get('NEGATIV_TENYEZOK', 0)))
                    
                    df.at[idx, 'ossz_pozitiv_pont'] = ossz_pozitiv
                    df.at[idx, 'ossz_negativ_pont'] = ossz_negativ
                    df.at[idx, 'netto_szoveg_pont'] = ossz_pozitiv - ossz_negativ
                    
                    processed_count += 1
            
            print(f"✅ Text feature-k generálva: {processed_count} ingatlanhoz")
            
            # Text feature statisztikák
            print(f"📊 ENHANCED FEATURE STATISZTIKÁK:")
            print(f"💎 Luxus: {df['van_luxus_kifejezés'].sum()} ingatlan")
            print(f"🌳 Kert: {df['van_kert_terulet'].sum()} ingatlan") 
            print(f"🚗 Garázs: {df['van_garage_parkolas'].sum()} ingatlan")
            print(f"🏡 Komfort: {df['van_komfort_extra'].sum()} ingatlan")
            print(f"⚠️ Negatív: {df['van_negativ_elem'].sum()} ingatlan")
            
            # Enhanced CSV mentése
            df.to_csv(enhanced_filename, index=False, encoding='utf-8-sig')
            
            print(f"🌟 Enhanced CSV mentve: {enhanced_filename}")
            print(f"📊 Oszlopok: {len(df.columns)} (+ {len(text_feature_columns)} text feature)")
            print(f"✨ Használatra kész az Enhanced ML modellhez!")
            
            return enhanced_filename  # Az enhanced fájlt adjuk vissza
            
        except Exception as e:
            print(f"❌ CSV mentési hiba: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def close(self):
        """Kapcsolat bezárása"""
        try:
            if self.playwright:
                await self.playwright.stop()
        except:
            pass

# Szükséges importok
import random

async def main():
    """Főprogram"""
    pipeline = KomplettIngatlanPipeline()
    await pipeline.run_complete_pipeline()

if __name__ == "__main__":
    asyncio.run(main())
