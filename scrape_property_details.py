import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import time
import random
from datetime import datetime
import csv

class DetailedPropertyScraper:
    def __init__(self):
        """
        Részletes ingatlan adatok kinyerése
        """
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
            print("💡 Ellenőrizd, hogy fut-e a debug Chrome (start_chrome_debug.bat)")
            return False
    
    async def get_active_tab(self):
        """Aktív tab megkeresése"""
        try:
            contexts = self.browser.contexts
            if not contexts:
                return False
            self.context = contexts[0]
            pages = self.context.pages
            if not pages:
                return False
            self.page = pages[0]
            return True
        except Exception as e:
            print(f"❌ Tab keresési hiba: {str(e)}")
            return False
    
    def _get_empty_details(self):
        """
        Üres adatstruktúra visszaadása hiba esetén
        """
        return {
            'reszletes_cim': '', 'reszletes_ar': '', 'epitesi_ev': '', 'szint': '',
            'allapot': '', 'ingatlan_allapota': '', 'epulet_szintjei': '', 'kilatas': '',
            'parkolas': '', 'parkolohely_ara': '', 'komfort': '', 'legkondicionalas': '',
            'akadalymentesites': '', 'furdo_wc': '', 'tetoter': '', 'pince': '',
            'futes': '', 'erkely': '', 'parkolo': '', 'energetikai': '',
            'tajolas': '', 'kert': '', 'napelem': '', 'szigeteles': '', 'rezsikoltség': '',
            'leiras': '', 'ingatlanos': '', 'telefon': '', 'hirdeto_tipus': ''
        }

    async def check_for_cloudflare_challenge(self):
        """
        Ellenőrzi, hogy Cloudflare challenge vagy reCAPTCHA van-e az oldalon - finomítva
        """
        try:
            # Csak specifikus és egyértelmű jelzők
            cloudflare_indicators = [
                ".cf-browser-verification",
                ".cf-checking-browser", 
                ".cf-challenge-container",
                "#cf-challenge-stage",
                "[data-translate='checking_browser']"
            ]
            
            # reCAPTCHA detektálása - csak egyértelmű
            recaptcha_indicators = [
                ".g-recaptcha",
                "iframe[src*='recaptcha']",
                ".recaptcha-checkbox"
            ]
            
            # Első körben csak vizuális elemeket keresünk
            for selector in cloudflare_indicators + recaptcha_indicators:
                element = await self.page.query_selector(selector)
                if element:
                    # Ellenőrizzük, hogy látható-e
                    is_visible = await element.is_visible()
                    if is_visible:
                        return True
                        
            # Csak akkor keresünk szövegben, ha semmi mást nem találtunk
            page_title = await self.page.title()
            if page_title:
                title_lower = page_title.lower()
                # Nagyon specifikus címek
                if ("checking your browser" in title_lower or 
                    "just a moment" in title_lower or 
                    "cloudflare" in title_lower):
                    return True
                    
            return False
            
        except Exception as e:
            print(f"  ⚠️ Challenge ellenőrzési hiba: {e}")
            return False
    
    async def human_like_navigation(self, url):
        """
        Emberszerű navigálás - random mouse mozgás, scroll, várakozás
        """
        try:
            # Navigálás
            await self.page.goto(url, timeout=30000)
            
            # Random várakozás a betöltődésre
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
            # Emberszerű interakciók véletlenszerűen
            actions = [
                self._random_mouse_movement,
                self._random_scroll,
                self._random_wait
            ]
            
            # Véletlenszerűen végrehajtunk 1-2 akciót
            num_actions = random.randint(1, 2)
            selected_actions = random.sample(actions, num_actions)
            
            for action in selected_actions:
                try:
                    await action()
                except:
                    pass  # Ha nem sikerül, nem baj
                    
        except Exception as e:
            print(f"  ⚠️ Navigálási hiba: {e}")
    
    async def _random_mouse_movement(self):
        """Véletlenszerű egér mozgás"""
        try:
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await self.page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
        except:
            pass
    
    async def _random_scroll(self):
        """Véletlenszerű görgetés"""
        try:
            scroll_amount = random.randint(100, 500)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(0.5, 1.0))
            # Vissza a tetejére
            await self.page.evaluate("window.scrollTo(0, 0)")
        except:
            pass
    
    async def _random_wait(self):
        """Véletlenszerű várakozás"""
        await asyncio.sleep(random.uniform(0.5, 1.5))
    
    async def handle_cloudflare_intervention(self, property_url, attempt_count):
        """
        Cloudflare challenge esetén kézi beavatkozást kér
        """
        print(f"\n🚨 CLOUDFLARE/reCAPTCHA CHALLENGE ÉSZLELVE!")
        print(f"📍 Problémás URL: {property_url}")
        print(f"🔄 Kísérlet száma: {attempt_count}")
        print(f"\n📋 TEENDŐK:")
        print(f"1. 🌐 Menj a Chrome böngészőbe")  
        print(f"2. ✅ Old meg a Cloudflare challenge-t vagy reCAPTCHA-t")
        print(f"3. ⏰ Várj, amíg betöltődik az ingatlan oldala")
        print(f"4. ↩️  Nyomj ENTER-t a folytatáshoz")
        
        # Várakozás a felhasználói beavatkozásra
        input("\n⌨️  Nyomj ENTER-t, amikor megoldottad a challenge-t...")
        
        print("🔄 Folytatás...")
        await asyncio.sleep(2)  # Rövid várakozás a stabilizálódásra
        """
        Cloudflare challenge esetén kézi beavatkozást kér
        """
        print(f"\n🚨 CLOUDFLARE/reCAPTCHA CHALLENGE ÉSZLELVE!")
        print(f"📍 Problémás URL: {property_url}")
        print(f"🔄 Kísérlet száma: {attempt_count}")
        print(f"\n📋 TEENDŐK:")
        print(f"1. 🌐 Menj a Chrome böngészőbe")  
        print(f"2. ✅ Old meg a Cloudflare challenge-t vagy reCAPTCHA-t")
        print(f"3. ⏰ Várj, amíg betöltődik az ingatlan oldala")
        print(f"4. ↩️  Nyomj ENTER-t a folytatáshoz")
        
        # Várakozás a felhasználói beavatkozásra
        input("\n⌨️  Nyomj ENTER-t, amikor megoldottad a challenge-t...")
        
        print("🔄 Folytatás...")
        await asyncio.sleep(2)  # Rövid várakozás a stabilizálódásra

    def detect_advertiser_type(self, description: str) -> str:
        """
        Meghatározza, hogy ingatlaniroda vagy magánszemély hirdeti-e az ingatlant
        """
        if not description:
            return "ismeretlen"
        
        desc_lower = description.lower()
        
        # Ingatlanirodás jelzők
        agency_indicators = [
            'ingatlan', 'iroda', 'otthon', 'center', 'ingatlaniroda',
            'ügyintéz', 'értékesít', 'szakértő', 'tanácsadó', 'ügynök',
            'cég', 'kft', 'bt', 'zrt', 'vállalkozás', 'szolgáltatás',
            'portfólió', 'referencia', 'tapasztalat', 'szakmai', 'ügyfél',
            'kedvezményes jutalék', 'jutalék', 'közvetítő', 'közvetítés',
            'értékbecslés', 'hitel', 'jogi', 'ügyintézés', 'adminisztráció',
            'ingyenes', 'szolgáltatásaink', 'csapatunk', 'kollégáink',
            'további ajánlat', 'hasonló ingatlan', 'egyéb ingatlan', 'keress',
            'elérhetőség', 'munkatársunk', 'kapcsolat', 'ügynökség'
        ]
        
        # Magánszemélyes jelzők  
        private_indicators = [
            'költözés', 'családi', 'gyerek', 'nyugdíj', 'idős', 'öreged',
            'külföld', 'munkahelyi', 'personal', 'személyes', 'saját',
            'lakunk', 'éltünk', 'tulajdonos', 'eladó vagyok', 'tulajdonosa',
            'azonnali', 'sürgős', 'gyors', 'költöznünk kell', 'gyorsan',
            'nem tudjuk', 'sajnos', 'kénytelen', 'csak', 'egyszerű',
            'magán', 'privát', 'lakó', 'lakott', 'családi okok', 'személyes ok'
        ]
        
        agency_count = sum(1 for indicator in agency_indicators if indicator in desc_lower)
        private_count = sum(1 for indicator in private_indicators if indicator in desc_lower)
        
        print(f"    👤 Hirdető analízis - Iroda: {agency_count}, Magán: {private_count}")
        
        # Hosszú, strukturált leírások általában irodásak
        if len(description) > 500 and agency_count > 2:
            return "ingatlaniroda"
        
        # Sok szakmai kifejezés = iroda
        if agency_count >= 3:
            return "ingatlaniroda"
        
        # Személyes hangvétel = magánszemély
        if private_count >= 2:
            return "maganszemely"
        
        # Alapértelmezett heurisztika a leírás hossza alapján
        if len(description) > 300 and agency_count > private_count:
            return "ingatlaniroda"
        elif len(description) < 200 and private_count > 0:
            return "maganszemely"
        
        return "bizonytalan"

    async def scrape_property_details(self, property_url):
        """
        Egyetlen ingatlan részletes adatainak kinyerése Cloudflare detektálással
        """
        details = {}
        
        try:
            print(f"🏠 Adatlap betöltése: {property_url}")
            
            # Emberszerű navigálás
            await self.human_like_navigation(property_url)
            
            # Cloudflare challenge ellenőrzése - csak egyszer, egyszerűbben
            if await self.check_for_cloudflare_challenge():
                print(f"  🚨 Cloudflare/reCAPTCHA challenge észlelve!")
                await self.handle_cloudflare_intervention(property_url, 1)
                
                # Rövid várakozás a megoldás után
                await asyncio.sleep(random.uniform(2, 4))
                
                # Ellenőrzés hogy megoldódott-e
                if await self.check_for_cloudflare_challenge():
                    print(f"  ❌ Challenge még mindig aktív. Ingatlan kihagyása.")
                    return self._get_empty_details()
                else:
                    print(f"  ✅ Challenge megoldva!")
                    
            # További humanizált várakozás
            await asyncio.sleep(random.uniform(1, 2))
            
            # Alap adatok
            try:
                # Cím - pontosabb selectorok
                address_selectors = [
                    "h1.text-onyx", 
                    ".property-address h1", 
                    ".listing-header h1",
                    "h1",
                    ".address"
                ]
                address = ""
                for selector in address_selectors:
                    address_element = await self.page.query_selector(selector)
                    if address_element:
                        address = await address_element.inner_text()
                        if address.strip():  # Csak ha van tartalom
                            break
                details['reszletes_cim'] = address.strip()
            except Exception as e:
                print(f"    ⚠️ Cím kinyerési hiba: {str(e)}")
                details['reszletes_cim'] = ""
            
            # Ár - pontosabb selectorok
            try:
                price_selectors = [
                    ".price-value", 
                    ".property-price .text-onyx", 
                    ".listing-price",
                    "[data-testid='price']",
                    ".price"
                ]
                price = ""
                for selector in price_selectors:
                    price_element = await self.page.query_selector(selector)
                    if price_element:
                        price = await price_element.inner_text()
                        if price.strip():
                            break
                details['reszletes_ar'] = price.strip()
            except Exception as e:
                print(f"    ⚠️ Ár kinyerési hiba: {str(e)}")
                details['reszletes_ar'] = ""
            
            # Ingatlan adatok táblázat - hangsúly az ÁLLAPOT és EMELET adatokon
            property_data = {}
            try:
                # Kulcs-érték párok keresése mind a desktop, mind a mobil táblázatból
                data_rows = await self.page.query_selector_all("table.table-borderless tr")
                print(f"    📋 Táblázat sorok: {len(data_rows)}")
                
                for row in data_rows:
                    try:
                        # Címke és érték - különböző strukturák kezelése
                        label_element = await row.query_selector("td:first-child span")
                        if not label_element:
                            label_element = await row.query_selector("td:first-child")
                        
                        value_element = await row.query_selector("td.fw-bold")
                        if not value_element:
                            value_element = await row.query_selector("td:nth-child(2)")
                        
                        if label_element and value_element:
                            label = (await label_element.inner_text()).strip().lower()
                            value_text = await value_element.inner_text()
                            value = value_text.strip()
                            
                            # Kihagyja az üres vagy "nincs megadva" értékeket
                            if not value or "nincs megadva" in value.lower():
                                continue
                            
                            # PRIORITÁS: ÁLLAPOT és EMELET adatok
                            key = None
                            if 'ingatlan állapota' in label or 'állapot' in label:
                                key = 'ingatlan_allapota'
                                print(f"    🎯 ÁLLAPOT: {value}")  # Debug
                            elif 'szint' in label and 'szintjei' not in label:
                                key = 'szint'
                                print(f"    🎯 EMELET/SZINT: {value}")  # Debug
                            elif 'emelet' in label:
                                key = 'szint'
                                print(f"    🎯 EMELET: {value}")  # Debug
                            elif 'építés éve' in label or 'épült' in label:
                                key = 'epitesi_ev'
                            elif 'épület szintjei' in label:
                                key = 'epulet_szintjei'
                            elif 'kilátás' in label:
                                key = 'kilatas'
                            elif 'parkolás' in label and 'parkolóhely ára' not in label:
                                key = 'parkolas'
                            elif 'parkolóhely ára' in label:
                                key = 'parkolohely_ara'
                            elif 'komfort' in label:
                                key = 'komfort'
                            elif 'légkondicionáló' in label:
                                key = 'legkondicionalas'
                            elif 'akadálymentesített' in label:
                                key = 'akadalymentesites'
                            elif 'fürdő és wc' in label or 'fürdőszoba' in label:
                                key = 'furdo_wc'
                            elif 'tetőtér' in label:
                                key = 'tetoter'
                            elif 'pince' in label:
                                key = 'pince'
                            elif 'fűtés' in label:
                                key = 'futes'
                            elif 'erkély' in label or 'terasz' in label:
                                key = 'erkely'
                            elif 'energetikai' in label:
                                key = 'energetikai'
                            elif 'tájolás' in label:
                                key = 'tajolas'
                            elif 'kert' in label:
                                key = 'kert'
                            elif 'napelem' in label:
                                key = 'napelem'
                            elif 'szigetelés' in label:
                                key = 'szigeteles'
                            elif 'rezsiköltség' in label:
                                key = 'rezsikoltség'
                            
                            # Ha talált kulcsot és még nincs ilyen adat
                            if key and key not in property_data:
                                property_data[key] = value
                                
                    except:
                        continue
                
                # KÜLÖN EMELET KERESÉS - javított xpath megoldás
                if 'szint' not in property_data:
                    try:
                        # Keresés minden lehetséges szint/emelet selector kombinációval
                        emelet_selectors = [
                            # Konkrét xpath a problémás elemekre
                            "//td[@class='fw-bold ps-0 text-gray-900' and string-length(normalize-space(text())) <= 2 and number(normalize-space(text()))]",
                            "//td[contains(text(), 'szint')]/following-sibling::td[1]",
                            "//td[contains(text(), 'Szint')]/following-sibling::td[1]", 
                            "//td[contains(text(), 'emelet')]/following-sibling::td[1]",
                            "//td[contains(text(), 'Emelet')]/following-sibling::td[1]"
                        ]
                        
                        for selector in emelet_selectors:
                            try:
                                emelet_element = await self.page.query_selector(f"xpath={selector}")
                                if emelet_element:
                                    emelet_text = await emelet_element.inner_text()
                                    emelet_clean = emelet_text.strip()
                                    # Numerikus validáció
                                    if emelet_clean.isdigit() or (emelet_clean.replace('.', '').isdigit()):
                                        if 0 <= int(emelet_clean.replace('.', '')) <= 50:  # Reális emelet tartomány
                                            property_data['szint'] = emelet_clean
                                            print(f"    🎯 EMELET (xpath keresés): {emelet_clean}")
                                            break
                            except:
                                continue
                                
                    except Exception as e:
                        print(f"    ⚠️ Emelet xpath keresési hiba: {e}")
                        
            except Exception as e:
                print(f"  ⚠️ Adattáblázat feldolgozási hiba: {str(e)}")
            
            # Alapértelmezett értékek hozzáadása - kibővített mezők
            details.update({
                'epitesi_ev': property_data.get('epitesi_ev', ''),
                'szint': property_data.get('szint', ''),
                'allapot': property_data.get('allapot', ''),
                'ingatlan_allapota': property_data.get('ingatlan_allapota', ''),
                'epulet_szintjei': property_data.get('epulet_szintjei', ''),
                'kilatas': property_data.get('kilatas', ''),
                'parkolas': property_data.get('parkolas', ''),
                'parkolohely_ara': property_data.get('parkolohely_ara', ''),
                'komfort': property_data.get('komfort', ''),
                'legkondicionalas': property_data.get('legkondicionalas', ''),
                'akadalymentesites': property_data.get('akadalymentesites', ''),
                'furdo_wc': property_data.get('furdo_wc', ''),
                'tetoter': property_data.get('tetoter', ''),
                'pince': property_data.get('pince', ''),
                'futes': property_data.get('futes', ''),
                'erkely': property_data.get('erkely', ''),
                'parkolo': property_data.get('parkolo', ''),
                'energetikai': property_data.get('energetikai', ''),
                'tajolas': property_data.get('tajolas', ''),
                'kert': property_data.get('kert', ''),
                'napelem': property_data.get('napelem', ''),
                'szigeteles': property_data.get('szigeteles', ''),
                'rezsikoltség': property_data.get('rezsikoltség', '')
            })
            
            # Leírás - helyes selector
            try:
                description_selectors = [
                    "#listing-description",
                    "p#listing-description", 
                    ".listing-description",
                    ".property-description", 
                    ".description-text"
                ]
                
                description = ""
                for selector in description_selectors:
                    desc_element = await self.page.query_selector(selector)
                    if desc_element:
                        description = await desc_element.inner_text()
                        break
                        
                # Leírás tisztítása és rövidítése
                if description:
                    # Új sorok és extra szóközök eltávolítása
                    description = description.replace('\n', ' ').replace('\r', ' ')
                    description = ' '.join(description.split())  # Többszörös szóközök eltávolítása
                    details['leiras'] = description[:1000] + "..." if len(description) > 1000 else description
                else:
                    details['leiras'] = ""
            except Exception as e:
                print(f"    ⚠️ Leírás kinyerési hiba: {str(e)}")
                details['leiras'] = ""
            
            # HIRDETŐ TÍPUS MEGHATÁROZÁSA
            try:
                if details['leiras']:
                    advertiser_type = self.detect_advertiser_type(details['leiras'])
                    details['hirdeto_tipus'] = advertiser_type
                    print(f"    👤 HIRDETŐ: {advertiser_type}")
                else:
                    details['hirdeto_tipus'] = "ismeretlen"
                    print(f"    👤 HIRDETŐ: ismeretlen (nincs leírás)")
            except Exception as e:
                print(f"    ⚠️ Hirdető típus meghatározási hiba: {str(e)}")
                details['hirdeto_tipus'] = "ismeretlen"
            
            # Ingatlanos adatok
            try:
                agent_selectors = [
                    ".agent-name, .contact-person, .broker-name"
                ]
                
                agent_name = ""
                for selector in agent_selectors:
                    agent_element = await self.page.query_selector(selector)
                    if agent_element:
                        agent_name = await agent_element.inner_text()
                        break
                        
                details['ingatlanos'] = agent_name
            except:
                details['ingatlanos'] = ""
            
            # Telefon
            try:
                phone_selectors = [
                    ".phone-number, .contact-phone, .agent-phone"
                ]
                
                phone = ""
                for selector in phone_selectors:
                    phone_element = await self.page.query_selector(selector)
                    if phone_element:
                        phone = await phone_element.inner_text()
                        break
                        
                details['telefon'] = phone
            except:
                details['telefon'] = ""
            
            print(f"  ✅ Kinyert adatok: {len([v for v in details.values() if v])} mező")
            return details
            
        except Exception as e:
            print(f"  ❌ Hiba: {str(e)}")
            return self._get_empty_details()
    
    async def process_csv_urls(self, csv_file, max_properties=50, start_from=0):
        """
        CSV fájlból URL-ek beolvasása és feldolgozása Cloudflare védelem detektálással
        """
        # CSV beolvasása
        try:
            df = pd.read_csv(csv_file)
            print(f"📊 CSV betöltve: {len(df)} ingatlan")
        except Exception as e:
            print(f"❌ CSV olvasási hiba: {str(e)}")
            return []
        
        if 'link' not in df.columns:
            print("❌ Nincs 'link' oszlop a CSV-ben")
            return []
        
        # URL-ek kinyerése
        urls = df['link'].dropna().tolist()
        print(f"🔗 Talált URL-ek: {len(urls)}")
        
        # Csak a kért számú ingatlan feldolgozása
        if max_properties:
            urls = urls[start_from:start_from + max_properties]
            print(f"📝 Feldolgozandó: {len(urls)} ingatlan ({start_from+1}-től)")
        else:
            urls = urls[start_from:]
            print(f"📝 Feldolgozandó: {len(urls)} ingatlan ({start_from+1}-től)")
        
        # Chrome kapcsolat létrehozása
        if not await self.connect_to_existing_chrome():
            return []
        
        if not await self.get_active_tab():
            print("❌ Nincs elérhető Chrome tab")
            return []
        
        # Részletes adatok gyűjtése
        detailed_data = []
        
        for i, url in enumerate(urls, start_from + 1):
            try:
                print(f"\n📍 {i}/{start_from + len(urls)}: Feldolgozás...")
                
                # Ingatlan adatok kinyerése
                details = await self.scrape_property_details(url)
                
                # Eredeti CSV adatok hozzáadása
                original_data = df[df['link'] == url].iloc[0].to_dict()
                combined_data = {**original_data, **details}
                detailed_data.append(combined_data)
                
                # Humanizált várakozás bot detektálás elkerülésére
                if i < start_from + len(urls):
                    # Változatos várakozási idők
                    base_wait = random.uniform(1.0, 3.0)
                    
                    # Néha hosszabb szünet (minden 10. ingatlannál)
                    if i % 10 == 0:
                        base_wait += random.uniform(2.0, 5.0)
                        print(f"  ⏳ Hosszabb szünet {base_wait:.1f}s (minden 10. ingatlan)...")
                    else:
                        print(f"  ⏰ Várakozás {base_wait:.1f}s...")
                    
                    await asyncio.sleep(base_wait)
                
            except Exception as e:
                print(f"  ❌ Hiba a {i}. ingatlan feldolgozása során: {str(e)}")
                # Eredeti adatok mentése hiba esetén is
                try:
                    original_data = df[df['link'] == url].iloc[0].to_dict()
                    empty_details = self._get_empty_details()
                    combined_data = {**original_data, **empty_details}
                    detailed_data.append(combined_data)
                except:
                    pass
                continue
        
        return detailed_data
    
    def save_detailed_csv(self, data, filename=None):
        """Részletes CSV mentése"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ingatlan_reszletes_{timestamp}.csv"
        
        try:
            df = pd.DataFrame(data)
            
            # Oszlopok sorrendje
            columns = [
                'id', 'cim', 'reszletes_cim', 'teljes_ar', 'reszletes_ar', 'terulet', 'nm_ar', 
                'szobak', 'epitesi_ev', 'szint', 'allapot', 'ingatlan_allapota', 'futes', 'erkely', 
                'parkolas', 'energetikai', 'tajolas', 'kert', 'hirdeto_tipus', 'leiras', 
                'ingatlanos', 'telefon', 'link'
            ]
            
            # Meglévő oszlopok használata
            available_columns = [col for col in columns if col in df.columns]
            df = df[available_columns]
            
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"\n💾 Részletes adatok mentve: {filename}")
            print(f"📊 Összesen {len(df)} ingatlan, {len(df.columns)} oszlop")
            return filename
        except Exception as e:
            print(f"💥 CSV mentési hiba: {e}")
            return None
    
    async def close(self):
        """Kapcsolat bezárása"""
        try:
            if self.playwright:
                await self.playwright.stop()
        except:
            pass

def get_search_url_with_limit():
    """Bekéri a felhasználótól a keresési URL-t és hozzáadja a limit paramétert"""
    print("🔗 INGATLAN KERESÉSI URL MEGADÁSA")
    print("="*50)
    print("💡 Példa URL:")
    print("   https://ingatlan.com/szukites/elado+lakas+kobanyi-ujhegy")
    print("   https://ingatlan.com/szukites/elado+haz+budapest")
    print("")
    
    while True:
        search_url = input("📍 Add meg a keresési URL-t: ").strip()
        
        if not search_url:
            print("❌ Kérlek add meg az URL-t!")
            continue
            
        if not search_url.startswith("https://ingatlan.com"):
            print("❌ Csak ingatlan.com URL-eket támogatunk!")
            continue
            
        # Limit paraméter hozzáadása
        if "?" in search_url:
            # Már vannak paraméterek
            enhanced_url = f"{search_url}&limit=300"
        else:
            # Nincsenek paraméterek
            enhanced_url = f"{search_url}?limit=300"
            
        print(f"✅ Továbbfejlesztett URL: {enhanced_url}")
        print(f"🎯 Maximum találatok: 300 ingatlan")
        
        return enhanced_url

async def main():
    """Főfüggvény dinamikus URL alapú scraping-hez"""
    print("🏠 RÉSZLETES INGATLAN ADATOK SCRAPER")
    print("="*60)
    
    # URL bekérése a felhasználótól
    search_url = get_search_url_with_limit()
    
    print(f"\n📁 Keresési URL: {search_url}")
    print(f"🎯 Feldolgozási limit: maximum 300 ingatlan")
    
    
    scraper = DetailedPropertyScraper()
    
    try:
        # Előbb át kell írnunk a scraper-t, hogy URL-t dolgozzon fel CSV helyett
        print(f"\n⚠️  Jelenleg a scraper CSV fájlból dolgozik.")
        print(f"🔧 Szükséges módosítás: URL-alapú scraping implementálása")
        print(f"💡 Alternatíva: Használd az eredeti list scraper-t először")
        print(f"   majd utána ezt a detail scraper-t a kapott CSV-re")
        
        # Ideiglenesen CSV alapú működés megtartása
        print(f"\n📋 Elérhető CSV fájlok:")
        import os
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and 'ingatlan' in f]
        for i, file in enumerate(csv_files, 1):
            print(f"   {i}. {file}")
        
        if csv_files:
            choice = input(f"\n📝 Válassz CSV fájlt (1-{len(csv_files)}) vagy nyomj ENTER-t a legutóbbihoz: ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(csv_files):
                csv_file = csv_files[int(choice)-1]
            else:
                csv_file = max(csv_files, key=lambda x: os.path.getmtime(x))  # Legújabb fájl
                
            print(f"✅ Kiválasztva: {csv_file}")
            
            # URL-ek feldolgozása - CSV alapon
            detailed_data = await scraper.process_csv_urls(csv_file, max_properties=300, start_from=0)
        
        if detailed_data:
            # CSV mentése
            filename = scraper.save_detailed_csv(detailed_data)
            
            print(f"\n🎉 SIKERES BEFEJEZÉS!")
            print(f"📁 Kimeneti fájl: {filename}")
            
            # Statisztika
            floor_count = len([d for d in detailed_data if d.get('szint', '')])
            advertiser_count = len([d for d in detailed_data if d.get('hirdeto_tipus', '')])
            description_count = len([d for d in detailed_data if d.get('leiras', '')])
            
            print(f"\n📊 EREDMÉNY STATISZTIKA:")
            print(f"   🏢 Emelet adat: {floor_count}/{len(detailed_data)} ({floor_count/len(detailed_data)*100:.1f}%)")
            print(f"   👤 Hirdető típus: {advertiser_count}/{len(detailed_data)} ({advertiser_count/len(detailed_data)*100:.1f}%)")
            print(f"   📝 Leírás: {description_count}/{len(detailed_data)} ({description_count/len(detailed_data)*100:.1f}%)")
        else:
            print("❌ Nem sikerült adatokat kinyerni")
    
    except KeyboardInterrupt:
        print(f"\n⏸️ LEÁLLÍTVA - Feldolgozott adatok mentése...")
        if 'detailed_data' in locals() and detailed_data:
            filename = scraper.save_detailed_csv(detailed_data)
            print(f"💾 Részleges eredmény mentve: {filename}")
        print(f"💡 Folytatáshoz indítsd újra és add meg: {len(detailed_data) if 'detailed_data' in locals() else 0}")
    
    except Exception as e:
        print(f"💥 Főfüggvény hiba: {e}")
    
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
