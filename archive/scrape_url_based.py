import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import time
import random
from datetime import datetime
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class UrlBasedPropertyScraper:
    def __init__(self):
        """URL-alapú ingatlan scraper"""
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    async def connect_to_existing_chrome(self):
        """Kapcsolódás már futó Chrome böngészőhöz"""
        try:
            print("🔗 Kapcsolódás Chrome böngészőhöz...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.connect_over_cdp("http://localhost:9222")
            print("✅ Chrome kapcsolat létrehozva")
            return True
        except Exception as e:
            print(f"❌ Chrome kapcsolódási hiba: {str(e)}")
            print("💡 Ellenőrizd, hogy fut-e a debug Chrome:")
            print("   chrome.exe --remote-debugging-port=9222 --user-data-dir=chrome_debug")
            return False
    
    async def get_active_tab(self):
        """Aktív tab megkeresése vagy új tab létrehozása"""
        try:
            contexts = self.browser.contexts
            if not contexts:
                self.context = await self.browser.new_context()
            else:
                self.context = contexts[0]
                
            pages = self.context.pages
            if not pages:
                self.page = await self.context.new_page()
            else:
                self.page = pages[0]
                
            return True
        except Exception as e:
            print(f"❌ Tab keresési hiba: {str(e)}")
            return False
    
    def get_search_url_with_limit(self):
        """Bekéri a felhasználótól a keresési URL-t és hozzáadja a limit paramétert"""
        print("🔗 INGATLAN KERESÉSI URL MEGADÁSA")
        print("="*50)
        print("💡 Példa URL-ek:")
        print("   https://ingatlan.com/szukites/elado+lakas+kobanyi-ujhegy")
        print("   https://ingatlan.com/szukites/elado+haz+budapest")
        print("   https://ingatlan.com/szukites/elado+lakas+xiii-kerulet")
        print("")
        
        while True:
            search_url = input("📍 Add meg a keresési URL-t: ").strip()
            
            if not search_url:
                print("❌ Kérlek add meg az URL-t!")
                continue
                
            if not search_url.startswith("https://ingatlan.com"):
                print("❌ Csak ingatlan.com URL-eket támogatunk!")
                continue
                
            # URL paraméterek kezelése
            parsed = urlparse(search_url)
            query_params = parse_qs(parsed.query)
            
            # Limit paraméter hozzáadása/felülírása
            query_params['limit'] = ['300']
            
            # URL újraépítése
            new_query = urlencode(query_params, doseq=True)
            enhanced_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, new_query, parsed.fragment
            ))
                
            print(f"✅ Továbbfejlesztett URL: {enhanced_url}")
            print(f"🎯 Maximum találatok: 300 ingatlan")
            
            return enhanced_url

    async def human_like_navigation(self, url):
        """Emberszerű navigálás"""
        try:
            await self.page.goto(url, timeout=30000)
            await asyncio.sleep(random.uniform(2.0, 4.0))
            
            # Véletlenszerű scroll
            if random.choice([True, False]):
                scroll_amount = random.randint(200, 800)
                await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await self.page.evaluate("window.scrollTo(0, 0)")
                
        except Exception as e:
            print(f"  ⚠️ Navigálási hiba: {e}")

    async def check_for_cloudflare_challenge(self):
        """Cloudflare challenge ellenőrzése"""
        try:
            cloudflare_indicators = [
                ".cf-browser-verification",
                ".cf-checking-browser", 
                ".cf-challenge-container",
                "#cf-challenge-stage"
            ]
            
            for selector in cloudflare_indicators:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    return True
                    
            page_title = await self.page.title()
            if page_title and ("checking your browser" in page_title.lower() or 
                              "cloudflare" in page_title.lower()):
                return True
                
            return False
        except:
            return False

    async def scrape_property_list(self, search_url):
        """Ingatlan lista scraping az URL alapján"""
        print(f"\n🏠 INGATLAN LISTA SCRAPING")
        print(f"🔗 URL: {search_url}")
        
        await self.human_like_navigation(search_url)
        
        # Cloudflare check
        if await self.check_for_cloudflare_challenge():
            print(f"🚨 Cloudflare challenge észlelve!")
            print(f"💡 Menj a böngészőbe és old meg a challenge-t, majd nyomj ENTER-t")
            input("⌨️  Nyomj ENTER-t a folytatáshoz...")
            await asyncio.sleep(2)
        
        # Találatok számának ellenőrzése
        try:
            result_count_selectors = [
                ".results-num",
                ".search-results-count", 
                "[data-testid='results-count']",
                ".found-results"
            ]
            
            total_results = 0
            for selector in result_count_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    # Számok kinyerése a szövegből
                    numbers = re.findall(r'\d+', text.replace(' ', '').replace('\xa0', ''))
                    if numbers:
                        total_results = int(numbers[-1])  # Utolsó szám általában a találatok száma
                        break
            
            print(f"📊 Talált ingatlanok száma: {total_results}")
            
        except Exception as e:
            print(f"⚠️ Találatok számának meghatározása sikertelen: {e}")
            total_results = 0
        
        # Ingatlan linkek gyűjtése
        properties = []
        
        try:
            # Ingatlan kártya selectorok - debug alapján javítva
            property_card_selectors = [
                ".listing-card",  # Ez működik a debug alapján
                ".listing__card", 
                ".result-item",
                ".search-result-item",
                "a[href*='/ingatlan/']"
            ]
            
            property_elements = []
            for selector in property_card_selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    property_elements = elements
                    print(f"✅ Találatok: {len(elements)} elem ({selector})")
                    break
            
            if not property_elements:
                print("❌ Nem találhatók ingatlan elemek")
                return []
            
            print(f"🔍 Adatok kinyerése {len(property_elements)} ingatlanból...")
            
            for i, element in enumerate(property_elements, 1):
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
                    
                    # Cím kinyerése - javított megközelítés
                    try:
                        # Keressünk linkeket a listing card-ban
                        link_elements = await element.query_selector_all('a[href*="/ingatlan/"]')
                        for link_elem in link_elements:
                            title_text = await link_elem.inner_text()
                            if title_text and len(title_text.strip()) > 5:  # Legalább 5 karakter
                                property_data['cim'] = title_text.strip()
                                break
                        else:
                            property_data['cim'] = ""
                    except:
                        property_data['cim'] = ""
                    
                    # Ár kinyerése - javított megközelítés  
                    try:
                        # Keressük az ár szövegeket tartalmazó elemeket
                        all_elements = await element.query_selector_all('*')
                        for elem in all_elements:
                            text = await elem.inner_text()
                            if text and ('ft' in text.lower() or 'millió' in text.lower() or re.search(r'\d+\s*M\s*Ft', text)):
                                property_data['teljes_ar'] = text.strip()
                                break
                        else:
                            property_data['teljes_ar'] = ""
                    except:
                        property_data['teljes_ar'] = ""
                    
                    # Terület kinyerése - javított megközelítés
                    try:
                        all_elements = await element.query_selector_all('*')
                        for elem in all_elements:
                            text = await elem.inner_text()
                            if text and ('m²' in text or 'm2' in text) and len(text) < 20:  # Rövid szöveg
                                property_data['terulet'] = text.strip()
                                break
                        else:
                            property_data['terulet'] = ""
                    except:
                        property_data['terulet'] = ""
                    
                    # Szobák száma - javított megközelítés
                    try:
                        all_elements = await element.query_selector_all('*')
                        for elem in all_elements:
                            text = await elem.inner_text()
                            if text and ('szoba' in text.lower() or '+' in text) and len(text) < 15:
                                property_data['szobak'] = text.strip()
                                break
                        else:
                            property_data['szobak'] = ""
                    except:
                        property_data['szobak'] = ""
                    
                    # NÉGYZETMÉTER ÁR SZÁMÍTÁSA (ha van ár és terület)
                    property_data['nm_ar'] = ""
                    if property_data['teljes_ar'] and property_data['terulet']:
                        try:
                            price_num = self._extract_number_from_price(property_data['teljes_ar'])
                            area_num = self._extract_number_from_area(property_data['terulet'])
                            
                            if price_num and area_num:
                                price_per_sqm = int(price_num / area_num)
                                property_data['nm_ar'] = f"{price_per_sqm:,} Ft / m2".replace(',', ' ')
                                
                        except Exception:
                            # Nem kritikus hiba
                            pass
                    
                    properties.append(property_data)
                    
                    if i % 10 == 0:
                        print(f"  📋 Feldolgozva: {i}/{len(property_elements)}")
                        
                except Exception as e:
                    print(f"  ⚠️ {i}. elem feldolgozási hiba: {e}")
                    continue
            
            print(f"✅ Lista scraping befejezve: {len(properties)} ingatlan")
            return properties
            
        except Exception as e:
            print(f"❌ Lista scraping hiba: {e}")
            return []

    def save_properties_csv(self, properties, search_url):
        """Ingatlan lista mentése CSV-be"""
        if not properties:
            print("❌ Nincsenek mentendő adatok")
            return None
            
        try:
            # Fájlnév generálása az URL alapján
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # URL-ből keresési terület kinyerése
            url_parts = search_url.split('/')
            search_term = url_parts[-1] if url_parts else "keresés"
            search_term = re.sub(r'[^\w\-_]', '_', search_term)[:30]  # Biztonságos fájlnév
            
            filename = f"ingatlan_lista_{search_term}_{timestamp}.csv"
            
            df = pd.DataFrame(properties)
            
            # Oszlopok sorrendje
            columns = ['id', 'cim', 'teljes_ar', 'terulet', 'nm_ar', 'szobak', 'link']
            available_columns = [col for col in columns if col in df.columns]
            df = df[available_columns]
            
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            print(f"\n💾 Lista mentve: {filename}")
            print(f"📊 Összesen {len(df)} ingatlan, {len(df.columns)} oszlop")
            
            return filename
            
        except Exception as e:
            print(f"❌ CSV mentési hiba: {e}")
            return None

    def _extract_number_from_price(self, price_text: str):
        """
        Ár szövegből numerikus érték kinyerése.
        
        Args:
            price_text: Ár szöveg (pl. "45,5 M Ft", "120 000 Ft")
            
        Returns:
            float or None: Numerikus ár érték
        """
        try:
            # Számjegyek és tizedesjel kinyerése
            import re
            numbers = re.findall(r'[\d,\.]+', price_text.replace(' ', ''))
            if numbers:
                num_str = numbers[0].replace(',', '.')
                num_value = float(num_str)
                
                # Millió/milliárd szorzó kezelése
                if 'M' in price_text.upper():
                    num_value *= 1_000_000
                elif 'MRD' in price_text.upper():
                    num_value *= 1_000_000_000
                
                return num_value
                
        except Exception:
            pass
        
        return None
    
    def _extract_number_from_area(self, area_text: str):
        """
        Terület szövegből numerikus érték kinyerése.
        
        Args:
            area_text: Terület szöveg (pl. "120 m2")
            
        Returns:
            float or None: Numerikus terület érték
        """
        try:
            import re
            numbers = re.findall(r'[\d,\.]+', area_text.replace(' ', ''))
            if numbers:
                num_str = numbers[0].replace(',', '.')
                return float(num_str)
                
        except Exception:
            pass
        
        return None

    async def close(self):
        """Kapcsolat bezárása"""
        try:
            if self.playwright:
                await self.playwright.stop()
        except:
            pass

async def main():
    """Főfüggvény URL-alapú scraping-hez"""
    print("🏠 URL-ALAPÚ INGATLAN SCRAPER")
    print("="*60)
    
    scraper = UrlBasedPropertyScraper()
    
    try:
        # URL bekérése
        search_url = scraper.get_search_url_with_limit()
        
        # Chrome kapcsolat
        if not await scraper.connect_to_existing_chrome():
            print("❌ Chrome kapcsolat sikertelen")
            return
            
        if not await scraper.get_active_tab():
            print("❌ Tab létrehozás sikertelen")
            return
        
        print(f"\n🔍 Lista scraping indítása...")
        
        # Ingatlan lista scraping
        properties = await scraper.scrape_property_list(search_url)
        
        if properties:
            # CSV mentése
            csv_file = scraper.save_properties_csv(properties, search_url)
            
            print(f"\n🎉 LISTA SCRAPING SIKERES!")
            print(f"📁 Kimeneti fájl: {csv_file}")
            print(f"📊 Összesen: {len(properties)} ingatlan")
            
            # Opció: részletes scraping indítása
            print(f"\n💡 KÖVETKEZŐ LÉPÉS:")
            print(f"   A részletes adatok kinyeréséhez használd:")
            print(f"   scrape_property_details.py")
            print(f"   és válaszd ki a {csv_file} fájlt")
            
        else:
            print("❌ Nem sikerült ingatlanokat találni")
            
    except KeyboardInterrupt:
        print(f"\n⏸️ Leállítva...")
        
    except Exception as e:
        print(f"❌ Főfüggvény hiba: {e}")
        
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
