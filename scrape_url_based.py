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
            # Ingatlan kártya selectorok
            property_card_selectors = [
                ".listing-card",
                ".property-card", 
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
                    link_element = element if element.tag_name.lower() == 'a' else await element.query_selector("a[href*='/ingatlan/']")
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
                    
                    # Cím
                    try:
                        title_selectors = [".listing-title", ".property-title", "h3", "h4", ".title"]
                        for sel in title_selectors:
                            title_elem = await element.query_selector(sel)
                            if title_elem:
                                property_data['cim'] = await title_elem.inner_text()
                                break
                        else:
                            property_data['cim'] = ""
                    except:
                        property_data['cim'] = ""
                    
                    # Ár
                    try:
                        price_selectors = [".price", ".listing-price", ".property-price", "[data-testid='price']"]
                        for sel in price_selectors:
                            price_elem = await element.query_selector(sel)
                            if price_elem:
                                property_data['teljes_ar'] = await price_elem.inner_text()
                                break
                        else:
                            property_data['teljes_ar'] = ""
                    except:
                        property_data['teljes_ar'] = ""
                    
                    # Terület és szobaszám
                    try:
                        details_selectors = [".property-details", ".listing-details", ".details", ".params"]
                        details_text = ""
                        for sel in details_selectors:
                            details_elem = await element.query_selector(sel)
                            if details_elem:
                                details_text = await details_elem.inner_text()
                                break
                        
                        # Terület kinyerése (pl. "65 m²")
                        area_match = re.search(r'(\d+)\s*m²', details_text)
                        property_data['terulet'] = f"{area_match.group(1)} m²" if area_match else ""
                        
                        # Szobaszám (pl. "3 szoba")
                        room_match = re.search(r'(\d+)\s*szoba', details_text)
                        property_data['szobak'] = room_match.group(1) if room_match else ""
                        
                        # Nm ár számítása ha van terület és ár
                        if property_data['teljes_ar'] and property_data['terulet']:
                            try:
                                price_numbers = re.findall(r'[\d,]+', property_data['teljes_ar'].replace(' ', ''))
                                area_numbers = re.findall(r'\d+', property_data['terulet'])
                                
                                if price_numbers and area_numbers:
                                    price_value = float(price_numbers[0].replace(',', '.'))
                                    area_value = int(area_numbers[0])
                                    
                                    if 'millió' in property_data['teljes_ar'].lower():
                                        price_value *= 1000000
                                    elif 'ezer' in property_data['teljes_ar'].lower():
                                        price_value *= 1000
                                    
                                    if area_value > 0:
                                        nm_price = int(price_value / area_value)
                                        property_data['nm_ar'] = f"{nm_price:,} Ft/m²".replace(',', ' ')
                                    else:
                                        property_data['nm_ar'] = ""
                                else:
                                    property_data['nm_ar'] = ""
                            except:
                                property_data['nm_ar'] = ""
                        else:
                            property_data['nm_ar'] = ""
                            
                    except:
                        property_data['terulet'] = ""
                        property_data['szobak'] = ""
                        property_data['nm_ar'] = ""
                    
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
