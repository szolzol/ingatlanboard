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
from dotenv import load_dotenv

# .env fájl betöltése
load_dotenv()
import sys
import random
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import pandas as pd
import numpy as np
import subprocess
from collections import Counter, defaultdict
from playwright.async_api import async_playwright

# ENHANCED LOKÁCIÓ MEGHATÁROZÁS - GOOGLE MAPS + SZEMANTIKUS ELEMZÉS
try:
    import googlemaps
    from geopy.distance import geodesic
    GOOGLE_MAPS_AVAILABLE = True
except ImportError:
    print("⚠️ Google Maps és geopy csomagok nem elérhetők. pip install googlemaps geopy")
    GOOGLE_MAPS_AVAILABLE = False

# ==== ENHANCED LOKÁCIÓ MEGHATÁROZÁSI RENDSZER ====

class GoogleMapsLocationAnalyzer:
    """Egyszerűsített Google Maps geocoding - dinamikus városrész felismeréssel"""
    
    def __init__(self, api_key=None):
        self.gmaps = None
        self.available = False
        if api_key and GOOGLE_MAPS_AVAILABLE:
            try:
                self.gmaps = googlemaps.Client(key=api_key)
                self.available = True
                print("✅ Google Maps API inicializálva")
            except Exception as e:
                print(f"⚠️ Google Maps API hiba: {e}")
    
    def geocode_address(self, address):
        """Cím geocoding-ja Google Maps API-val - teljes információval"""
        if not self.available:
            return None
        
        try:
            # Budapest hozzáadása ha nincs benne
            if 'budapest' not in address.lower():
                address += ', Budapest, Hungary'
            
            result = self.gmaps.geocode(address)
            if result:
                location = result[0]['geometry']['location']
                formatted_address = result[0].get('formatted_address', address)
                return {
                    'coordinates': (location['lat'], location['lng']),
                    'formatted_address': formatted_address,
                    'raw_result': result[0]
                }
        except Exception as e:
            print(f"Geocoding hiba {address}: {e}")
        
        return None

    def analyze_location(self, address, description=""):
        """Egyszerűsített lokáció elemzés - Google Maps alapú városrész felismerés"""
        results = {'source': 'google_maps', 'confidence': 0.0}
        
        # Geocoding
        geocode_result = self.geocode_address(address)
        if geocode_result:
            # Dinamikus városrész kinyerés a Google Maps eredményből
            district = self._extract_district_from_result(geocode_result, address)
            
            results.update({
                'district': district,
                'confidence': 0.85,  # Jó konfidencia geocoding alapján
                'coordinates': geocode_result['coordinates'],
                'formatted_address': geocode_result['formatted_address']
            })
        
        return results
    
    def _extract_district_from_result(self, geocode_result, original_address):
        """Városrész kinyerése Google Maps eredményből"""
        import re
        
        formatted_address = geocode_result.get('formatted_address', '')
        raw_result = geocode_result.get('raw_result', {})
        
        # 1. Próba: Address components elemzése
        for component in raw_result.get('address_components', []):
            types = component.get('types', [])
            long_name = component.get('long_name', '')
            
            # Kerület típusú komponens keresése
            if 'sublocality' in types or 'political' in types:
                # Kerület szám vagy név keresése
                district_match = re.search(r'(District|kerület)\s*([IVX]+|\d+)', long_name, re.IGNORECASE)
                if district_match:
                    return f"{district_match.group(2)}. kerület"
                
                # Római szám keresése
                roman_match = re.search(r'([IVX]+)\.?\s*(ker|District)', long_name, re.IGNORECASE)
                if roman_match:
                    return f"{roman_match.group(1)}. kerület"
        
        # 2. Próba: Formatted address elemzése
        all_text = formatted_address + ' ' + original_address
        
        # Kerület szám keresése
        kerület_matches = re.findall(r'(\w+)\s*\.?\s*ker(?:ület)?', all_text, re.IGNORECASE)
        if kerület_matches:
            return f"{kerület_matches[0]}. kerület"
        
        # Római szám önállóan
        roman_matches = re.findall(r'([IVX]+)\.?\s*(?=\s|,|$)', all_text)
        if roman_matches:
            return f"{roman_matches[0]}. kerület"
        
        # 3. Próba: Szám keresése
        number_matches = re.findall(r'(\d+)\.?\s*ker', all_text, re.IGNORECASE)
        if number_matches:
            return f"{number_matches[0]}. kerület"
        
        # Fallback: Budapest általános
        return "Budapest általános"


class DescriptionLocationExtractor:
    """Leírásokból történő szemantikus lokáció kinyerés fejlett pattern matching-el"""
    
    def __init__(self):
        # KORRIGÁLT kerületi rész --> utca mapping
        self.corrected_street_mapping = {
            'Krisztinaváros': [
                'márvány', 'margitta', 'attila', 'krisztina', 'LogodiLogodi', 'tabán',
                'naphegy', 'gellérthegy', 'várhegy', 'anjou', 'vérmező'
            ],
            'Svábhegy': [
                'svábhegy', 'normafa', 'eötvös', 'cseppkő', 'beethoven', 
                'költő', 'tóth árpád', 'kuruclesi', 'galvani'
            ],
            'Orbánhegy': [
                'orbán', 'törökugrató', 'nagy', 'szilágyi dezső', 'fillér', 
                'görög', 'maros', 'margit', 'toldy'
            ],
            'Virányos': [
                'virányos', 'istenhegyi', 'alkotás', 'böszörményi', 
                'csaba', 'németvölgyi', 'sas'
            ],
            'Rózsadomb': [
                'rózsadomb', 'palatinus', 'apostol', 'törökvész', 'szerb',
                'pasaréti', 'fellner', 'frankel leó'
            ],
            'Zugliget': [
                'zugligeti', 'szépvölgyi', 'máriaremetei', 'hűvösvölgyi',
                'zugliget', 'budakeszi', 'cseppkő'
            ]
        }
        
        # Kontextuális modifikátorok
        self.context_modifiers = {
            'premium': ['panoráma', 'kilátás', 'egyedi', 'exkluzív', 'prémium', 'luxus'],
            'nature': ['erdő', 'park', 'természet', 'hegyi', 'csendes'],
            'transport': ['metro', 'busz', 'villamos', 'közlekedés'],
            'amenities': ['iskola', 'óvoda', 'bolt', 'pláza', 'orvos']
        }
    
    def extract_locations_from_text(self, text):
        """Szövegből lokáció pattern-ek kinyerése"""
        if not text:
            return []
        
        text = text.lower().strip()
        found_locations = []
        
        # 1. Közvetlen kerületi rész említések
        for district, keywords in self.corrected_street_mapping.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    # Kontextuális elemzés
                    context_score = self._calculate_context_confidence(text)
                    confidence = min(0.95, 0.7 + context_score)
                    
                    found_locations.append({
                        'district': district,
                        'confidence': confidence,
                        'keyword': keyword,
                        'context_score': context_score,
                        'source': 'description'
                    })
        
        return found_locations
    
    def _calculate_context_confidence(self, text):
        """Kontextuális konfidencia számítás"""
        confidence_boost = 0.0
        
        for category, keywords in self.context_modifiers.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches > 0:
                confidence_boost += min(0.15, matches * 0.05)
        
        # Hosszabb leírás = magasabb konfidencia
        length_boost = min(0.1, len(text) / 1000)
        
        return confidence_boost + length_boost
    
    def analyze_description(self, description):
        """Teljes leírás elemzés eredmény aggregálással"""
        locations = self.extract_locations_from_text(description)
        
        if not locations:
            return {'district': 'Ismeretlen', 'confidence': 0.0, 'source': 'description'}
        
        # Legnagyobb konfidenciájú találat kiválasztása
        best_location = max(locations, key=lambda x: x['confidence'])
        
        return {
            'district': best_location['district'],
            'confidence': best_location['confidence'],
            'source': 'description',
            'all_matches': len(locations),
            'best_keyword': best_location['keyword']
        }


class EnhancedLocationCategorizer:
    """4-lépéses hibrid lokáció kategorizálás hierarchikus fallback-kel"""
    
    def __init__(self, google_maps_api_key=None):
        self.google_analyzer = GoogleMapsLocationAnalyzer(google_maps_api_key)
        self.description_analyzer = DescriptionLocationExtractor()
        
        # Fallback címelemzés egyszerű pattern matching-el
        self.address_patterns = {
            'Krisztinaváros': ['krisztina', 'attila', 'logodi', 'tabán', 'márvány'],
            'Svábhegy': ['svábhegy', 'normafa', 'eötvös', 'beethoven'],
            'Orbánhegy': ['orbánhegy', 'szilágyi dezső', 'törökugrató'],
            'Rózsadomb': ['rózsadomb', 'palatinus', 'törökvész', 'pasaréti'],
            'Virányos': ['virányos', 'istenhegyi', 'alkotás'],
            'Zugliget': ['zugliget', 'hűvösvölgy', 'máriaremete']
        }
    
    def categorize_location(self, address="", description="", price=None):
        """4-lépéses lokáció kategorizálás"""
        results = []
        
        # 1. LÉPÉS: Google Maps koordináta-alapú elemzés
        if address:
            google_result = self.google_analyzer.analyze_location(address, description)
            if google_result.get('confidence', 0) > 0.5:
                results.append(google_result)
        
        # 2. LÉPÉS: Szemantikus leírás elemzés
        if description:
            desc_result = self.description_analyzer.analyze_description(description)
            if desc_result.get('confidence', 0) > 0.4:
                results.append(desc_result)
        
        # 3. LÉPÉS: Egyszerű cím pattern matching (fallback)
        if address:
            addr_result = self._simple_address_match(address)
            if addr_result.get('confidence', 0) > 0.3:
                results.append(addr_result)
        
        # 4. LÉPÉS: Eredmény aggregálás és végső döntés
        final_result = self._aggregate_results(results, price)
        
        return final_result
    
    def _simple_address_match(self, address):
        """Egyszerű cím pattern matching fallback módszer"""
        address_lower = address.lower()
        
        for district, patterns in self.address_patterns.items():
            for pattern in patterns:
                if pattern in address_lower:
                    return {
                        'district': district,
                        'confidence': 0.4,
                        'source': 'address_pattern',
                        'matched_pattern': pattern
                    }
        
        return {'district': 'Ismeretlen', 'confidence': 0.0, 'source': 'address_pattern'}
    
    def _aggregate_results(self, results, price=None):
        """Többszörös eredmény aggregálás súlyozott átlaggal + koordináták megőrzése"""
        if not results:
            return {'district': 'Ismeretlen', 'confidence': 0.0, 'source': 'none', 'method': 'fallback'}
        
        # District-konfidencia párok gyűjtése + koordináták keresése
        district_scores = defaultdict(list)
        best_coordinates = None
        
        for result in results:
            district = result.get('district', 'Ismeretlen')
            confidence = result.get('confidence', 0.0)
            source = result.get('source', 'unknown')
            
            # 🌍 KOORDINÁTÁK MEGŐRZÉSE - elsőbbség a Google Maps-nek
            if source == 'google_maps' and result.get('coordinates'):
                best_coordinates = result['coordinates']
            elif not best_coordinates and result.get('coordinates'):
                best_coordinates = result['coordinates']
            
            # Forrás típus súlyozás
            source_weight = {
                'google_maps': 1.0,      # Legmegbízhatóbb
                'description': 0.8,      # Jó
                'address_pattern': 0.6   # Fallback
            }.get(source, 0.5)
            
            weighted_confidence = confidence * source_weight
            district_scores[district].append(weighted_confidence)
        
        # Legjobb district kiválasztása
        best_district = 'Ismeretlen'
        best_confidence = 0.0
        
        for district, confidences in district_scores.items():
            # Súlyozott átlag számítás
            avg_confidence = sum(confidences) / len(confidences)
            
            if avg_confidence > best_confidence:
                best_confidence = avg_confidence
                best_district = district
        
        # Ár-alapú konfidencia finomhangolás
        if price and best_confidence > 0.3:
            price_modifier = self._get_price_confidence_modifier(best_district, price)
            best_confidence = min(0.98, best_confidence * price_modifier)
        
        # 🌍 JAVÍTOTT VISSZATÉRÉS - koordinátákkal
        result = {
            'district': best_district,
            'confidence': round(best_confidence, 3),
            'source': f"aggregated_from_{len(results)}_sources",
            'method': 'enhanced_4step',
            'total_analyses': len(results)
        }
        
        # Koordináták hozzáadása ha vannak
        if best_coordinates:
            result['coordinates'] = best_coordinates
        
        return result
    
    def _get_price_confidence_modifier(self, district, price):
        """Ár-alapú konfidencia módosítás (logikus ár-lokáció párosítás)"""
        try:
            price_num = float(re.sub(r'[^\d]', '', str(price)))
        except:
            return 1.0
        
        # Kerületi részek tipikus árszintjei (millió Ft)
        typical_price_ranges = {
            'Rózsadomb': (150, 800),
            'Krisztinaváros': (100, 600), 
            'Svábhegy': (120, 500),
            'Zugliget': (80, 400),
            'Virányos': (90, 450),
            'Orbánhegy': (70, 350)
        }
        
        if district in typical_price_ranges:
            min_price, max_price = typical_price_ranges[district]
            
            if min_price <= price_num <= max_price:
                return 1.1  # Logikus ár -> konfidencia növelés
            elif price_num < min_price * 0.7 or price_num > max_price * 1.5:
                return 0.8  # Szokatlan ár -> konfidencia csökkentés
        
        return 1.0  # Semleges


# ==== VÉGESLENYULT ENHANCED LOKÁCIÓ RENDSZER ====

class IngatlanSzovegelemzo:
    """
    Beépített szöveganalízis modul - Enhanced feature-k generálása + LOKÁCIÓ ANALÍZIS
    """
    def __init__(self, google_maps_api_key=None):
        """Inicializálja a kategóriákat és kulcsszavakat + Enhanced Lokáció Rendszer"""
        
        # 🗺️ ENHANCED LOKÁCIÓ KATEGORIZÁLÓ INICIALIZÁLÁSA
        self.location_categorizer = EnhancedLocationCategorizer(google_maps_api_key)
        print("✅ Enhanced lokáció kategorizáló inicializálva")
        
        # 🔥 MODERN ÁRFELHAJTÓ KATEGÓRIÁK - 2025 INGATLANPIACI TRENDEK
        self.kategoriak = {
            # 🌞 ZÖLD ENERGIA & FENNTARTHATÓSÁG - TOP ÁRFELHAJTÓ 2025
            'ZOLD_ENERGIA_PREMIUM': {
                'kulcsszavak': [
                    'napelem', 'napelempark', 'fotovoltaikus', 'szoláris', 'napenergia',
                    'geotermikus', 'geotermia', 'földhő', 'hőszivattyú', 'hőszivattyús',
                    'levegő-víz hőszivattyú', 'föld-víz hőszivattyú', 'inverteres',
                    'hibrid fűtés', 'megújuló energia', 'önellátó', 'energiafüggetlenség',
                    'netzero', 'carbon neutral', 'passzívház', 'energiahatékony',
                    'AA+ energetikai', '0 rezsikölts', 'elektromos töltő', 'e-töltő'
                ],
                'pontszam': 4.5  # Legnagyobb árfelhajtó hatás 2025-ben
            },
            
            # 🏊 WELLNESS & LUXUS REKREÁCIÓ - PRÉMIUM KATEGÓRIA
            'WELLNESS_LUXURY': {
                'kulcsszavak': [
                    'úszómedence', 'infinity pool', 'úszómedence fedett', 'jakuzzi',
                    'spa', 'szauna', 'gőzfürdő', 'wellness részleg', 'masszázsszoba',
                    'fitneszterem', 'konditerem', 'sportpálya', 'teniszpálya',
                    'bor pince', 'borospince', 'privát mozi', 'házi mozi',
                    'panoráma erkély', 'tetőterasz', 'sky bar', 'privát lift',
                    'szolgálati lakás', 'vendégház', 'poolház'
                ],
                'pontszam': 4.0  # Nagy prémium érték
            },
            
            # 🏠 SMART HOME & TECHNOLÓGIA - 2025 TREND
            'SMART_TECHNOLOGY': {
                'kulcsszavak': [
                    'okos otthon', 'smart home', 'okos vezérlés', 'app vezérlés',
                    'voice control', 'automatizált', 'riasztórendszer', 'biztonsági',
                    'kamerarendszer', 'beléptető', 'ujjlenyomat', 'arcfelismerés',
                    'központi porszívó', 'hangosítás', 'multiroom', 'kábelezés',
                    'strukturált hálózat', 'fiber', 'gigabit', '5G ready',
                    'elektromos redőny', 'árnyékoló automatika', 'időzíthető'
                ],
                'pontszam': 3.5  # Teknológiai prémium
            },
            
            # 💎 PRÉMIUM DESIGN & ANYAGHASZNÁLAT
            'PREMIUM_DESIGN': {
                'kulcsszavak': [
                    'prémium', 'luxus', 'exkluzív', 'egyedi tervezés', 'építész tervezett',
                    'designer', 'belsőépítész', 'olasz csempe', 'márvány', 'gránit',
                    'tömör fa', 'parkett', 'természetes anyagok', 'kőburkolat',
                    'nemesacél', 'inox', 'kristály', 'LED világítás', 'rejtett világítás',
                    'Miele', 'Bosch', 'Gaggenau', 'prémium konyhagép', 'beépített',
                    'márkás bútor', 'olasz bútor', 'egyedi bútor'
                ],
                'pontszam': 3.8  # Design prémium
            },
            
            # 🚗 MODERN PARKOLÁS & GARÁZS
            'PREMIUM_PARKING': {
                'kulcsszavak': [
                    'dupla garázs', 'tripla garázs', 'többállásos garázs', 'fedett parkoló',
                    'automata garázsajtó', 'távnyitós', 'elektromos töltő', 'tesla töltő',
                    'műhelyrész', 'tároló garázs', 'fűtött garázs', 'dupla behajtó',
                    'körbehajtó', 'vendég parkoló', 'több autó', '4+ autó'
                ],
                'pontszam': 2.8  # Parkolás prémium
            },
            
            # 🌿 KIVÁLÓ LOKÁCIÓ & KÖRNYEZET
            'PREMIUM_LOCATION': {
                'kulcsszavak': [
                    'csendes utca', 'zsákutca', 'panorámás', 'erdőszéli', 'vízparti',
                    'dunai panoráma', 'budai hegyek', 'zöldövezet', 'park szomszédság',
                    'villa negyed', 'reprezentatív környezet', 'diplomata negyed',
                    'golfpálya közel', 'nemzetközi iskola', 'elit környezet',
                    'privát utca', 'őrzött terület', 'biztonsági szolgálat'
                ],
                'pontszam': 3.2  # Lokációs prémium
            },
            
            # 🏗️ ÉPÍTÉSI MINŐSÉG & ÁLLAPOT
            'BUILD_QUALITY': {
                'kulcsszavak': [
                    'kulcsrakész', 'újépítésű', 'nulla ráfordítás', 'költözhető',
                    'teljes felújítás', 'prémium felújítás', 'generálkivitelező',
                    'minőségi kivitelezés', 'új gépészet', 'új elektromos',
                    'új tető', 'új nyílászárók', 'hőszigetelés', 'külső szigetelés',
                    'új fűtés', 'új burkolatok', 'garancia', 'eredetiség'
                ],
                'pontszam': 2.5  # Minőségi prémium
            },
            
            # ⚠️ NEGATÍV ÁRBEFOLYÁSOLÓ TÉNYEZŐK - CSÖKKENTŐ HATÁS
            'NEGATIV_TENYEZOK': {
                'kulcsszavak': [
                    # Állapotproblémák
                    'felújítandó', 'felújításra szorul', 'rossz állapot', 'elhanyagolt',
                    'problémás', 'javítandó', 'cserélendő', 'hiányos', 'hiányosságok',
                    'beázás', 'nedvesség', 'penész', 'rothadás', 'repedt', 'repedések',
                    
                    # Költségnövelő tényezők
                    'drága fűtés', 'magas rezsi', 'rezsikölts', 'energiaigényes',
                    'rossz szigetelés', 'régi fűtés', 'régi gépészet', 'cserélendő tető',
                    
                    # Környezeti problémák
                    'forgalmas', 'zajos', 'zajterhelés', 'közút mellett', 'vasút melletti',
                    'ipari környezet', 'szennyezett', 'bűzös', 'kellemetlen',
                    'földút', 'rossz megközelítés', 'közlekedés nehéz',
                    
                    # Jogias és értékcsökkentő
                    'jogi probléma', 'per', 'zárlat', 'hagyaték', 'kényszerű eladás',
                    'sürgős', 'gyors eladás', 'alku', 'alkuképes', 'áron alul'
                ],
                'pontszam': -2.0  # Negatív hatás
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

    def enhanced_location_analysis(self, address="", description="", price=None):
        """
        🗺️ ENHANCED LOKÁCIÓ ELEMZÉS - 4-lépéses hibrid rendszer
        """
        try:
            location_result = self.location_categorizer.categorize_location(
                address=address, 
                description=description, 
                price=price
            )
            
            # Eredmény formázás + koordináták kinyerése
            result = {
                'keruleti_resz': location_result.get('district', 'Ismeretlen'),
                'konfidencia': location_result.get('confidence', 0.0),
                'elemzesi_modszer': location_result.get('method', 'unknown'),
                'forras': location_result.get('source', 'none'),
                'elemzesek_szama': location_result.get('total_analyses', 0),
                
                # 🌍 Koordináták hozzáadása
                'coordinates': location_result.get('coordinates', None),
                'latitude': None,
                'longitude': None,
                'geocoded_address': ''
            }
            
            # Koordináták szétbontása
            if result['coordinates']:
                result['latitude'] = result['coordinates'][0]
                result['longitude'] = result['coordinates'][1]
                result['geocoded_address'] = address
                
            return result
        except Exception as e:
            print(f"⚠️ Enhanced lokáció elemzés hiba: {e}")
            return {
                'keruleti_resz': 'Ismeretlen',
                'konfidencia': 0.0,
                'elemzesi_modszer': 'error',
                'forras': 'fallback',
                'elemzesek_szama': 0,
                'coordinates': None,
                'latitude': None,
                'longitude': None,
                'geocoded_address': ''
            }

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
        print("   https://ingatlan.com/lista/elado+lakas+kobanya-ujhegyi-lakotelep")
        print("   https://ingatlan.com/lista/elado+haz+erd-erdliget")
        print("   https://ingatlan.com/lista/elado+haz+budaors")
        print("   https://ingatlan.com/lista/elado+lakas+100-500-m2+xi-ker")
        
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
        print("   300  - Óriás minta (45-90 perc)")
        
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
        """Lokáció kinyerése URL-ből fájlnév generálásához - CSAK FÖLDRAJZI HELYSÉG"""
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
            
            # FÖLDRAJZI LOKÁCIÓ KINYERÉSE
            # Eltávolítjuk a típus és állapot szűrőket, csak a helységet hagyjuk meg
            location_only = search_part
            
            # Eltávolítjuk az ingatlan típust (elado+haz, elado+lakas, stb.)
            location_only = re.sub(r'(elado|kiado|berlet)\+[^+]*\+?', '', location_only)
            
            # Eltávolítjuk az állapot szűrőket
            allapot_szurok = [
                'uj_epitesu', 'ujszeru', 'felujitott', 'jo_allapot', 'kituno_allapot', 
                'kozepes_allapot', 'felujitando', 'rossz_allapot', 'bonthato',
                'uj-epitesu', 'jo-allapot', 'kituno-allapot', 'kozepes-allapot',
                'epitesu', 'ujszeru', 'felujitott', 'jo', 'allapot'
            ]
            
            for szuro in allapot_szurok:
                location_only = location_only.replace(f'+{szuro}', '').replace(f'{szuro}+', '').replace(szuro, '')
            
            # Speciális "allapotu" kezelés - teljes eltávolítás
            location_only = location_only.replace('jo-allapotu', '').replace('-allapotu', '').replace('allapotu', '')
            
            # Speciális "uj" kezelés - csak akkor távolítsuk el, ha önálló vagy állapot kontextusban
            # Ne távolítsuk el, ha része egy nagyobb szónak (pl. "ujorszagut")
            location_only = re.sub(r'(\+|^)uj(\+|$)', r'\1\2', location_only)  # Csak önálló "uj"
            location_only = re.sub(r'\+uj(?=\+[a-z])', '+', location_only)  # "uj" + következő szó elején
            
            # Maradó "u" betűk eltávolítása ha önállóak
            location_only = re.sub(r'(\+|^)u(\+)', r'\1\2', location_only)  # Önálló "u" betű
            
            # Ár szűrők eltávolítása (pl: 80-500-mFt, 80-500-mft, 100_200_m_ft)
            location_only = re.sub(r'\+?\d+[\-_]\d+[\-_]?m?[Ff]t\+?', '', location_only)
            location_only = re.sub(r'\+?\d+_\d+_m_ft\+?', '', location_only)
            location_only = re.sub(r'\+?\d+\-\d+\-m\-?ft\+?', '', location_only)
            location_only = re.sub(r'\+?\d+\-\d+\-mft\+?', '', location_only)
            
            # Szobaszám szűrők eltávolítása (pl: 3-szoba, 4-szoba, 3-szoba-felett, 2-szoba-alatt)
            location_only = re.sub(r'\+?\d+[\-_]szoba[\-_]?(felett|alatt)?\+?', '', location_only)
            location_only = re.sub(r'\+?szoba[\-_]?(felett|alatt)?\+?', '', location_only)
            location_only = re.sub(r'\+?(felett|alatt)\+?', '', location_only)  # Maradék "felett", "alatt" szavak
            
            # Alapterület szűrők eltávolítása (pl: 60-120-m2, 80-nm)
            location_only = re.sub(r'\+?\d+[\-_]\d+[\-_]?m2?\+?', '', location_only)
            location_only = re.sub(r'\+?\d+[\-_]nm\+?', '', location_only)
            location_only = re.sub(r'\+?\d+nm\+?', '', location_only)
            
            # Állapot-specifikus számok eltávolítása (pl. "20" csak ha ár/méret kontextusban)
            # DE: ne távolítsunk el minden számot, mert kerületek is számok lehetnek
            # Helyette csak akkor távolítsunk el, ha m2, ft, szoba, nm kontextusban van
            location_only = re.sub(r'\+?\d{1,3}(?=[+_]?(m2?|ft|szoba|nm))\+?', '', location_only)
            
            # Dupla + jelek eltávolítása és tisztítás
            location_only = re.sub(r'\+{2,}', '+', location_only)
            location_only = location_only.strip('+')
            
            # Ha üres, akkor próbáljunk kivenni budapest/helység részeket
            if not location_only or len(location_only) < 3:
                # Eredeti search_part-ból keressük a budapest, kerület, vagy helység részeket
                helyseg_reszek = []
                parts = search_part.replace('+', ' ').replace('-', ' ').split()
                
                budapest_found = False
                for i, part in enumerate(parts):
                    part_lower = part.lower()
                    # Budapest vagy kerület
                    if part_lower in ['budapest', 'bp']:
                        helyseg_reszek.append('budapest')
                        budapest_found = True
                    elif 'kerulet' in part_lower or 'ker' in part_lower:
                        # Előző rész keresése (pl: ii, xiii, 12, stb.)
                        if i > 0:
                            prev_part = parts[i-1].lower()
                            if prev_part in ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x', 'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'xvii', 'xviii', 'xix', 'xx', 'xxi', 'xxii', 'xxiii'] or prev_part.isdigit():
                                helyseg_reszek.append(f'{prev_part}_ker')
                        elif not budapest_found:
                            helyseg_reszek.append('kerulet')
                    elif part_lower in ['budaors', 'budaörs', 'erd', 'torokbalint', 'törökbálint', 'szentendre', 'godllo', 'gödöllő', 'vac', 'vác', 'dunakeszi', 'pilisvorosvar', 'piliscsaba']:
                        helyseg_reszek.append(part_lower.replace('ö', 'o').replace('ő', 'o').replace('á', 'a').replace('é', 'e'))
                
                if helyseg_reszek:
                    location_only = '_'.join(helyseg_reszek)
                else:
                    # Utolsó esély: első 2-3 értelmesnek tűnő rész
                    meaningful_parts = []
                    for part in parts[:4]:  # Első 4 részt nézzük
                        part_lower = part.lower()
                        if part_lower not in ['elado', 'kiado', 'berlet', 'haz', 'lakas', 'telek', 'iroda', 'uzlet'] and len(part) > 2:
                            meaningful_parts.append(part_lower)
                        if len(meaningful_parts) >= 2:  # Max 2 rész
                            break
                    location_only = '_'.join(meaningful_parts) if meaningful_parts else 'ingatlan_kereses'
            
            # Biztonságos fájlnév készítése - JAVÍTOTT VERZIÓ
            safe_name = re.sub(r'[^\w\-_]', '_', location_only)
            safe_name = safe_name.replace('-', '_')
            safe_name = re.sub(r'_{2,}', '_', safe_name)
            safe_name = safe_name.strip('_')
            
            # XXII kerület speciális kezelés - "muxxii" helyett "xxii"
            if 'muxxii' in safe_name:
                safe_name = safe_name.replace('muxxii', 'xxii')
            
            return safe_name[:50] if safe_name else "ingatlan_kereses"
            
        except Exception as e:
            print(f"⚠️ Location extraction hiba: {e}")
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
                # Streamlit dashboard automatikus indítása
                try:
                    # Egyedi port keresése (8501-től kezdve)
                    port = self._find_available_port(8501)
                    
                    print(f"🌐 Dashboard indítása porton: {port}")
                    print(f"📋 Parancs: streamlit run {self.dashboard_file} --server.port={port}")
                    
                    # Streamlit indítása háttérben
                    process = subprocess.Popen([
                        sys.executable, '-m', 'streamlit', 'run', self.dashboard_file,
                        '--server.port', str(port),
                        '--server.headless', 'true'
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                except Exception as e:
                    print(f"⚠️ Dashboard automatikus indítás sikertelen: {e}")
                    print(f"🔧 Manuális indítás: streamlit run {self.dashboard_file}")
                
                return True
            else:
                print("❌ Dashboard generálás sikertelen")
                return False
                
        except Exception as e:
            print(f"❌ Dashboard hiba: {e}")
            return False
    
    def _find_available_port(self, start_port=8501):
        """Elérhető port keresése Streamlit számára"""
        import socket
        
        port = start_port
        while port < start_port + 20:  # Maximum 20 portot próbál
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                port += 1
        return start_port  # Ha nem talál, visszaadja az eredetit
    
    def _create_custom_dashboard(self):
        """Dashboard template testreszabása - ÚJ TEMPLATE PLACEHOLDER RENDSZER"""
        try:
            # streamlit_app.py template beolvasása
            if not os.path.exists('streamlit_app.py'):
                print("❌ Dashboard template nem található!")
                return False

            with open('streamlit_app.py', 'r', encoding='utf-8') as f:
                template = f.read()

            # Lokáció név formázása megjelenítéshez
            display_name = self.location_name.replace('_', ' ').upper()
            display_name = re.sub(r'\bELADO\b', 'ELADÓ', display_name)
            display_name = re.sub(r'\bHAZ\b', 'HÁZ', display_name) 
            display_name = re.sub(r'\bLAKAS\b', 'LAKÁS', display_name)
            display_name = re.sub(r'\bKER\b', 'KERÜLET', display_name)

            print(f"📝 Dashboard generálás: {self.location_name} -> {display_name}")

            # ÚJ TEMPLATE PLACEHOLDER CSERÉK
            # 1. Location név placeholder cseréje
            customized = template.replace("{{LOCATION_NAME}}", display_name)

            # 2. CSV Pattern placeholder-ek cseréje - lokáció alapú pattern generálás
            base_location = self.location_name.lower()
            
            # Dinamikus CSV pattern-ek generálása
            csv_patterns = []
            
            # Pattern 1: Részletes enhanced fájlok (prioritás)
            if 'enhanced_text_features' in self.details_csv_file:
                pattern1 = f"ingatlan_reszletes_enhanced_text_features_*{base_location}*.csv"
            else:
                pattern1 = f"ingatlan_reszletes_*{base_location}*.csv"
            csv_patterns.append(pattern1)
            
            # Pattern 2: Modern enhanced fájlok (fallback)  
            pattern2 = f"ingatlan_modern_enhanced_{base_location}_*.csv"
            csv_patterns.append(pattern2)
            
            # Pattern 3: Általános keresés (utolsó fallback)
            pattern3 = f"ingatlan_*{base_location}*.csv"
            csv_patterns.append(pattern3)

            # CSV pattern placeholder-ek cseréje
            customized = customized.replace("{{CSV_PATTERN_1}}", csv_patterns[0])
            customized = customized.replace("{{CSV_PATTERN_2}}", csv_patterns[1])  
            customized = customized.replace("{{CSV_PATTERN_3}}", csv_patterns[2])

            print(f"📊 Generált CSV pattern-ek:")
            for i, pattern in enumerate(csv_patterns, 1):
                print(f"   Pattern {i}: {pattern}")

            # Dashboard fájl mentése
            dashboard_filename = f"dashboard_{self.location_name}.py"
            with open(dashboard_filename, 'w', encoding='utf-8') as f:
                f.write(customized)

            print(f"✅ Dashboard létrehozva: {dashboard_filename}")
            print(f"🎯 Lokáció: {display_name}")
            print(f"📁 CSV minta: {csv_patterns[0]}")

            return True

        except Exception as e:
            print(f"❌ Dashboard létrehozási hiba: {e}")
            return False
            
            # Dinamikus szemantikai elemzés generálása
            semantic_insights = self._generate_dynamic_semantic_insights()
            
            # Hardkódolt semantic_insights lecserélése
            if semantic_insights:
                # Keressük a teljes semantic_insights dictionary-t és cseréljük le dinamikusra
                semantic_pattern = r'semantic_insights\s*=\s*\{.*?\n\s+\}'
                semantic_replacement = f"semantic_insights = {semantic_insights}"
                
                # Ha nem találjuk az első formában, próbáljuk hosszabb verzióval
                if not re.search(semantic_pattern, customized, flags=re.DOTALL):
                    semantic_pattern = r'semantic_insights\s*=\s*\{[^}]*?\n[^}]*?\n[^}]*?\n[^}]*?\n[^}]*?\n[^}]*?\n[^}]*?\n[^}]*?\n\s+\}'
                
                customized = re.sub(semantic_pattern, semantic_replacement, customized, flags=re.DOTALL)
            
            # Dashboard mentése
            with open(self.dashboard_file, 'w', encoding='utf-8') as f:
                f.write(customized)
            
            return True
            
        except Exception as e:
            print(f"❌ Template hiba: {e}")
            return False
    
    def _generate_dynamic_semantic_insights(self):
        """Dinamikus szemantikai elemzés generálása a modern árfelhajtó trendek alapján"""
        try:
            import pandas as pd
            
            # CSV betöltése
            df = pd.read_csv(self.details_csv_file, encoding='utf-8-sig', sep='|')
            total_count = len(df)
            
            if total_count == 0:
                return None
            
            # Szemantikai kategóriák dinamikus számítása - ÚJ MODERN KATEGÓRIÁK
            insights = {}
            
            # 🌞 ZÖLD ENERGIA & FENNTARTHATÓSÁG - TOP ÁRFELHAJTÓ 2025
            zold_pont_col = next((col for col in df.columns if 'zold_energia' in col.lower() and 'pont' in col.lower()), None)
            zold_van_col = next((col for col in df.columns if 'zold_energia' in col.lower() and 'van_' in col.lower()), None)
            if zold_pont_col and zold_van_col:
                zold_count = int((df[zold_van_col] > 0).sum())
                zold_avg_pont = float(df[zold_pont_col].mean())
                insights['🌞 Zöld Energia Premium'] = {
                    'hirdetések': zold_count,
                    'arány': round(zold_count/total_count*100, 1),
                    'átlag_pontszám': round(zold_avg_pont, 2),
                    'leírás': 'Napelem, geotermikus, hőszivattyú, energiafüggetlenség'
                }
            
            # 🏊 WELLNESS & LUXUS REKREÁCIÓ
            wellness_pont_col = next((col for col in df.columns if 'wellness' in col.lower() and 'pont' in col.lower()), None)
            wellness_van_col = next((col for col in df.columns if 'wellness' in col.lower() and 'van_' in col.lower()), None)
            if wellness_pont_col and wellness_van_col:
                wellness_count = int((df[wellness_van_col] > 0).sum())
                wellness_avg_pont = float(df[wellness_pont_col].mean())
                insights['🏊 Wellness & Luxury'] = {
                    'hirdetések': wellness_count,
                    'arány': round(wellness_count/total_count*100, 1),
                    'átlag_pontszám': round(wellness_avg_pont, 2),
                    'leírás': 'Úszómedence, jakuzzi, szauna, spa, fitness'
                }
            
            # 🏠 SMART HOME & TECHNOLÓGIA
            smart_pont_col = next((col for col in df.columns if 'smart' in col.lower() and 'pont' in col.lower()), None)
            smart_van_col = next((col for col in df.columns if 'smart' in col.lower() and 'van_' in col.lower()), None)
            if smart_pont_col and smart_van_col:
                smart_count = int((df[smart_van_col] > 0).sum())
                smart_avg_pont = float(df[smart_pont_col].mean())
                insights['� Smart Technology'] = {
                    'hirdetések': smart_count,
                    'arány': round(smart_count/total_count*100, 1),
                    'átlag_pontszám': round(smart_avg_pont, 2),
                    'leírás': 'Okos otthon, automatizáció, biztonsági rendszer'
                }
            
            # 💎 PRÉMIUM DESIGN & ANYAGHASZNÁLAT
            premium_pont_col = next((col for col in df.columns if 'premium' in col.lower() and 'pont' in col.lower()), None)
            premium_van_col = next((col for col in df.columns if 'premium' in col.lower() and 'van_' in col.lower()), None)
            if premium_pont_col and premium_van_col:
                premium_count = int((df[premium_van_col] > 0).sum())
                premium_avg_pont = float(df[premium_pont_col].mean())
                insights['💎 Premium Design'] = {
                    'hirdetések': premium_count,
                    'arány': round(premium_count/total_count*100, 1),
                    'átlag_pontszám': round(premium_avg_pont, 2),
                    'leírás': 'Designer bútor, márvány, tömör fa, exkluzív anyagok'
                }
            
            # 🌿 KIVÁLÓ LOKÁCIÓ & KÖRNYEZET
            lokacio_pont_col = next((col for col in df.columns if ('lokacio' in col.lower() or 'location' in col.lower()) and 'pont' in col.lower()), None)
            lokacio_van_col = next((col for col in df.columns if ('lokacio' in col.lower() or 'location' in col.lower()) and 'van_' in col.lower()), None)
            if lokacio_pont_col and lokacio_van_col:
                lokacio_count = int((df[lokacio_van_col] > 0).sum())
                lokacio_avg_pont = float(df[lokacio_pont_col].mean())
                insights['🌿 Premium Lokáció'] = {
                    'hirdetések': lokacio_count,
                    'arány': round(lokacio_count/total_count*100, 1),
                    'átlag_pontszám': round(lokacio_avg_pont, 2),
                    'leírás': 'Villa negyed, panoráma, csendes környezet'
                }
            
            # ⚠️ NEGATÍV TÉNYEZŐK
            negativ_pont_col = next((col for col in df.columns if 'negativ' in col.lower() and 'pont' in col.lower()), None)
            negativ_van_col = next((col for col in df.columns if 'negativ' in col.lower() and 'van_' in col.lower()), None)
            if negativ_pont_col and negativ_van_col:
                negativ_count = int((df[negativ_van_col] > 0).sum())
                negativ_avg_pont = float(df[negativ_pont_col].mean())
                insights['⚠️ Negatív Tényezők'] = {
                    'hirdetések': negativ_count,
                    'arány': round(negativ_count/total_count*100, 1),
                    'átlag_pontszám': round(abs(negativ_avg_pont), 2),  # Abszolút érték a megjelenítéshez
                    'leírás': 'Felújítandó állapot, zajos környezet, problémás helyzet'
                }
            
            return insights if insights else None
            
        except Exception as e:
            print(f"Dinamikus szemantikai elemzés hiba: {e}")
            return None
    
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
        """Chrome kapcsolat létrehozása - Headless módban (bevált konfiguráció)"""
        try:
            print("🔗 Chrome indítása (headless mód)...")
            self.playwright = await async_playwright().start()
            
            # Headless browser indítása - eredeti bevált konfiguráció
            self.browser = await self.playwright.chromium.launch(
                headless=True,  # Headless mód - ez volt a bevált
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-gpu'
                ]
            )
            
            # Új context és page létrehozása
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
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
            
            # Több próbálkozás robusztusabb betöltéssel - BIZTONSÁGOS VERZIÓ
            for attempt in range(3):
                try:
                    print(f"  📡 Próbálkozás {attempt + 1}/3...")
                    await self.page.goto(self.search_url, wait_until='domcontentloaded', timeout=60000)
                    await asyncio.sleep(5)  # Visszaállítva biztonságos értékre
                    
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
                        await asyncio.sleep(3)  # Visszaállítva biztonságos értékre
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
                    
                    # Szobák száma - specifikus logikával új DOM struktúra alapján
                    property_data['szobak'] = ""
                    try:
                        # Új struktúra: listing-property divekben keresünk
                        property_divs = await element.query_selector_all('.listing-property')
                        for div in property_divs:
                            spans = await div.query_selector_all('span')
                            if len(spans) >= 2:
                                label_text = await spans[0].inner_text()
                                if 'Szobák' in label_text:
                                    value_text = await spans[1].inner_text()
                                    # Csak számokat fogadunk el, vagy szám + fél típusú formátumot
                                    if value_text.strip() and (value_text.strip().isdigit() or '+' in value_text or 'fél' in value_text.lower()):
                                        property_data['szobak'] = value_text.strip()
                                        break
                        
                        # Ha nem találtuk az új struktúrában, próbáljuk a régi módszerrel
                        if not property_data['szobak']:
                            all_spans = await element.query_selector_all('span')
                            for i, span in enumerate(all_spans):
                                text = await span.inner_text()
                                if 'Szobák' in text and i + 1 < len(all_spans):
                                    next_span = all_spans[i + 1]
                                    room_text = await next_span.inner_text()
                                    if '+' in room_text or 'szoba' in room_text.lower() or room_text.strip().isdigit():
                                        property_data['szobak'] = room_text.strip()
                                        break
                    except Exception as e:
                        print(f"Szobaszám kinyerési hiba: {e}")
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
        """CSV mentés automatikus fájlnévvel pipe elválasztóval + duplikáció szűrés"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ingatlan_lista_{self.location_name}_{timestamp}.csv"
            
            df = pd.DataFrame(properties)
            original_count = len(df)
            
            # 🔥 DUPLIKÁCIÓ SZŰRÉS - ár, terület és cím alapján
            print(f"🧹 Duplikáció szűrés indítása...")
            print(f"   📊 Eredeti rekordok: {original_count}")
            
            if len(df) > 0:
                # Duplikátumok eltávolítása (első előfordulást megtartjuk)
                df_clean = df.drop_duplicates(subset=['cim', 'teljes_ar', 'terulet'], keep='first')
                duplicates_removed = original_count - len(df_clean)
                
                print(f"   🗑️ Eltávolított duplikátumok: {duplicates_removed}")
                print(f"   ✅ Egyedi rekordok: {len(df_clean)}")
                
                df = df_clean
            
            # Oszlop sorrend
            columns = ['id', 'cim', 'teljes_ar', 'nm_ar', 'terulet', 'telekterulet', 'szobak', 'kepek_szama', 'link']
            available_columns = [col for col in columns if col in df.columns]
            df = df[available_columns]
            
            # CSV mentés PIPE elválasztóval (|) - vesszők a leírásban problémát okoznának
            df.to_csv(filename, index=False, encoding='utf-8-sig', sep='|')
            
            print(f"💾 Lista CSV mentve (| elválasztó): {filename}")
            print(f"📊 Végső rekordszám: {len(df)}")
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
        
        # Bot elkerülő stratégiák
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self.current_user_agent_index = 0
        self.referer_urls = [
            'https://ingatlan.com/',
            'https://ingatlan.com/lista/',
            'https://www.google.com/',
        ]
    
    async def process_all_properties(self):
        """Összes ingatlan részletes feldolgozása"""
        # CSV beolvasás pipe elválasztóval
        try:
            df = pd.read_csv(self.list_csv_file, sep='|')
            print(f"📊 CSV beolvasva: {len(df)} ingatlan")
        except Exception as e:
            print(f"❌ CSV hiba: {e}")
            return []
        
        if 'link' not in df.columns:
            print("❌ Nincs 'link' oszlop!")
            return []
        
        # NORMÁL PLAYWRIGHT CONNECTION - STABIL MÓDSZER
        try:
            print("🔗 Chrome kapcsolat létrehozása (normál mód)...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=False,  # Látható böngésző
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-extensions'
                ]
            )
            
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            )
            self.page = await self.context.new_page()
            
            print("✅ Chrome kapcsolat részletes scraperhez OK")
            
        except Exception as e:
            print(f"❌ Chrome kapcsolat hiba: {e}")
            return []
        
        # Részletes scraping
        detailed_data = []
        urls = df['link'].dropna().tolist()
        
        # SIMPLE SESSION WARMUP - PIPELINE STYLE - BIZTONSÁGOS VERZIÓ
        try:
            print(f"\n🌐 Session warmup...")
            await self.page.goto('https://ingatlan.com/', wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(5)  # Pipeline proven timing - visszaállított biztonságos érték
            
            print(f"✅ Session előkészítve")
        except Exception as e:
            print(f"⚠️ Session warmup hiba (folytatunk): {e}")
        
        for i, url in enumerate(urls, 1):
            try:
                print(f"\n🏠 {i}/{len(urls)}: {url}")
                
                # Alapadatok az eredeti CSV-ből
                original_data = df[df['link'] == url].iloc[0].to_dict()
                
                # SIMPLE SCRAPING - PIPELINE STYLE
                details = await self._scrape_single_property(url)
                
                # Kombináció
                combined = {**original_data, **details}
                
                # Szobaszám logolás az emelet helyett
                szobak = combined.get('szobak', '')
                if szobak and szobak.strip():
                    print(f"    🏠 Szobák: {szobak}")
                else:
                    print(f"    🏠 Szobák: nincs adat")
                
                detailed_data.append(combined)
                
                # Humán-szerű várakozás változatos időkkel - BIZTONSÁGOS VERZIÓ
                if i < len(urls):
                    # Visszaállított várakozási idők a captcha elkerülésére
                    base_wait = random.uniform(2.5, 4.5)  # Visszaállítva biztonságosra
                    if i > 5:  # 5. kérés után kissé lassabb
                        base_wait = random.uniform(4.0, 6.5)  # Visszaállítva biztonságosra
                    if i > 10:  # 10. kérés után még lassabb
                        base_wait = random.uniform(5.5, 8.0)  # Visszaállítva biztonságosra
                        
                    # Minden 5. kérésnél extra szünet - visszaállítva
                    if i % 5 == 0:
                        base_wait += random.uniform(2.0, 4.0)  # Visszaállítva biztonságosra
                        print(f"  🔄 Extra szünet {i}. kérésnél...")
                    
                    print(f"  ⏰ Várakozás {base_wait:.1f}s...")
                    await asyncio.sleep(base_wait)
                    
            except Exception as e:
                print(f"  ❌ Hiba: {e}")
                # Üres részletes adatok hozzáadása
                empty_details = self._get_empty_details()
                combined = {**original_data, **empty_details}
                detailed_data.append(combined)
                continue
        
        return detailed_data
    
    async def _scrape_single_property(self, url):
        """Egyetlen ingatlan részletes scraping - PIPELINE STYLE"""
        details = {}
        
        try:
            print(f"  🏠 Adatlap: {url}")
            
            # SIMPLE NAVIGATION - PIPELINE PROVEN
            await self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(random.uniform(2.5, 4.0))  # Pipeline timing - visszaállított biztonságos érték
            
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
                    
                # SIMPLE CAPTCHA DETECTION
                if details.get('reszletes_cim', '').lower().find('gyors ellenőrzés') != -1:
                    print(f"    🚨 CAPTCHA DETECTED: {details['reszletes_cim']}")
                    details['reszletes_cim'] = "CAPTCHA_DETECTED"
                    
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
                            
                            # Prioritásos mezők - dupla logolás elkerülése
                            if 'ingatlan állapota' in label or 'állapot' in label:
                                # Csak akkor írja ki újra, ha még nincs beállítva vagy eltérő az érték
                                if 'ingatlan_allapota' not in table_data or table_data['ingatlan_allapota'] != value:
                                    table_data['ingatlan_allapota'] = value
                                    print(f"    🎯 Állapot: {value}")
                            elif 'szint' in label and 'szintjei' not in label:
                                if 'szint' not in table_data or table_data['szint'] != value:
                                    table_data['szint'] = value
                                    # Szint/emelet logolás eltávolítva - szobaszám logolás lesz helyette
                            elif 'emelet' in label:
                                if 'szint' not in table_data or table_data['szint'] != value:
                                    table_data['szint'] = value
                                    # Emelet logolás eltávolítva - szobaszám logolás lesz helyette
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
            
            # HIRDETŐ TÍPUS MEGHATÁROZÁSA - egyszerűsített
            details['hirdeto_tipus'] = await self._determine_advertiser_type_from_page()
            
            # Ha nem sikerült az oldalról, akkor szemantikai elemzés
            if details['hirdeto_tipus'] == "ismeretlen" and details['leiras']:
                details['hirdeto_tipus'] = self._detect_advertiser_type(details['leiras'])
            
            # Ha még mindig ismeretlen, akkor alapértelmezett
            if details['hirdeto_tipus'] == "ismeretlen":
                details['hirdeto_tipus'] = "bizonytalan"
                            
            # További mezők alapértékekkel
            additional_fields = ['ingatlanos', 'telefon', 'allapot', 'epulet_szintjei', 
                               'kilatas', 'parkolohely_ara', 'komfort', 'legkondicionalas',
                               'akadalymentesites', 'furdo_wc', 'tetoter', 'pince', 
                               'parkolo', 'tajolas', 'kert', 'napelem', 'szigeteles', 'rezsikoltség']
            
            for field in additional_fields:
                if field not in details:
                    details[field] = ""
            
            # Javított logolás - ÖSSZES kinyert mező számlálása
            all_fields = ['reszletes_cim', 'reszletes_ar', 'epitesi_ev', 'szint', 'ingatlan_allapota', 
                         'futes', 'erkely', 'parkolas', 'energetikai', 'leiras', 'ingatlanos', 
                         'telefon', 'hirdeto_tipus'] + additional_fields
            filled_fields = [field for field in all_fields if details.get(field, "")]
            print(f"  ✅ Kinyert mezők: {len(filled_fields)}/{len(all_fields)}")
            return details
            
        except Exception as e:
            print(f"  ❌ Scraping hiba: {e}")
            return self._get_empty_details()
    
    async def _determine_advertiser_type_from_page(self):
        """Hirdető típus azonosítás a self.page-ről"""
        try:
            # Keressük a pontos szelektort
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
            return "ismeretlen"
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
    
    def _categorize_district(self, cim, reszletes_cim, leiras, location_name=""):
        """Dinamikus városrész kategorizálás lokáció alapján - CÍM SPECIFIKUS ELEMZÉSSEL"""
        
        # Egyesített szöveg elemzéshez
        teljes_szoveg = f"{cim} {reszletes_cim} {leiras}".lower()
        
        # 🎯 CÍM ALAPÚ SPECIFIKUS VÁROSRÉSZ FELISMERÉS
        if 'kőbánya' in teljes_szoveg or 'kobanya' in teljes_szoveg or 'x. kerület' in teljes_szoveg:
            return self._categorize_kobanya_district(cim, reszletes_cim, leiras)
        elif 'törökbálint' in teljes_szoveg or 'torokbalint' in teljes_szoveg:
            return self._categorize_torokbalint_district(cim, reszletes_cim, leiras)
        elif 'budaörs' in teljes_szoveg or 'budaors' in teljes_szoveg:
            return self._categorize_budaors_district(cim, reszletes_cim, leiras)
        elif 'xii' in teljes_szoveg or 'xii.' in cim:
            return self._categorize_budapest_xii_district(cim, reszletes_cim, leiras)
        elif any(word in teljes_szoveg for word in ['budapest', 'pest', 'buda']):
            return self._categorize_budapest_general_district(cim, reszletes_cim, leiras)
        elif 'érd' in teljes_szoveg:
            return self._categorize_erd_district(cim, reszletes_cim, leiras)
        else:
            # ÁLTALÁNOS KATEGORIZÁLÁS - LOKÁCIÓ FÜGGETLEN
            return self._categorize_general_district(cim, reszletes_cim, leiras)

    def _categorize_kobanya_district(self, cim, reszletes_cim, leiras):
        """Kőbánya X. kerület specifikus városrész kategorizálás"""
        
        # Egyesített szöveg elemzéshez
        teljes_szoveg = f"{cim} {reszletes_cim} {leiras}".lower()
        
        # KŐBÁNYA X. KERÜLET VÁROSRÉSZEK
        varosreszek = {
            'Kőbánya-Újhegyi lakótelep': {
                'kulcsszavak': ['újhegy', 'újhegyi', 'lakótelep', 'panelház', 'panel',
                               'tóvirág', 'mélytó', 'szövőszék', 'oltó', 'kővágó',
                               'dombtető', 'gőzmozdony', 'harmat', 'bányató'],
                'premium_szorzo': 1.0,
                'leiras': 'Kőbánya-Újhegyi lakótelep, paneles lakónegyed'
            },
            
            'Kőbánya központ': {
                'kulcsszavak': ['központ', 'belváros', 'főút', 'közlekedés',
                               'bevásárlóközpont', 'szolgáltatás'],
                'premium_szorzo': 0.95,
                'leiras': 'Kőbánya központi területe'
            },
            
            'Kőbánya egyéb terület': {
                'kulcsszavak': ['kőbánya', 'kobanya', 'x. kerület'],
                'premium_szorzo': 0.9,
                'leiras': 'Kőbánya egyéb területei'
            }
        }
        
        return self._find_best_district_match(varosreszek, teljes_szoveg, 'Kőbánya-Újhegyi lakótelep')

    def _categorize_torokbalint_district(self, cim, reszletes_cim, leiras):
        """Törökbálint specifikus városrész kategorizálás"""
        
        # Egyesített szöveg elemzéshez
        teljes_szoveg = f"{cim} {reszletes_cim} {leiras}".lower()
        
        # TÖRÖKBÁLINT VÁROSRÉSZEK
        varosreszek = {
            'Törökbálint-Tükörhegy': {
                'kulcsszavak': ['tükörhegy', 'tukorhegy', 'hegy', 'panoráma', 'kilátás',
                               'családi ház', 'villa', 'nagy telek', 'természet'],
                'premium_szorzo': 1.2,
                'leiras': 'Törökbálint-Tükörhegy, családi házas negyed'
            },
            
            'Törökbálint központ': {
                'kulcsszavak': ['központ', 'főút', 'szolgáltatás', 'bevásárlóközpont'],
                'premium_szorzo': 1.0,
                'leiras': 'Törökbálint központi területe'
            },
            
            'Törökbálint lakópark': {
                'kulcsszavak': ['lakópark', 'új építés', 'modern', 'fejlesztés'],
                'premium_szorzo': 1.1,
                'leiras': 'Törökbálinti új lakóparkok'
            }
        }
        
        return self._find_best_district_match(varosreszek, teljes_szoveg, 'Törökbálint központ')

    def _categorize_budapest_xii_district(self, cim, reszletes_cim, leiras):
        """Budapest XII. kerület városrész kategorizálás"""
        
        # Egyesített szöveg elemzéshez
        teljes_szoveg = f"{cim} {reszletes_cim} {leiras}".lower()
        
        # BUDAPEST XII. KERÜLET VÁROSRÉSZEK ÉS PRÉMIUM KATEGÓRIÁK
        varosreszek = {
            # PRÉMIUM TERÜLETEK - 1.4x szorzó
            'XII. ker. Budai hegyek - Villa negyed': {
                'kulcsszavak': ['svábhegy', 'rózsadomb', 'széchenyi-hegy', 'villa', 'panoráma',
                               'budai hegyek', 'erdő', 'természet', 'csendes', 'prestige'],
                'premium_szorzo': 1.4,
                'leiras': 'Budai hegyek, villanegyed, panorámás kilátás'
            },
            
            'XII. ker. Hegyvidék prémium': {
                'kulcsszavak': ['hegyvidék', 'normafa', 'jános-hegy', 'zugliget',
                               'családi ház', 'nagy telek', 'zöld környezet'],
                'premium_szorzo': 1.35,
                'leiras': 'Hegyvidéki prémium lokáció'
            },
            
            # KIVÁLÓ LOKÁCIÓK - 1.25x szorzó  
            'XII. ker. Orbánhegy': {
                'kulcsszavak': ['orbánhegy', 'orbán', 'erdőalja', 'family park',
                               'bevásárlóközpont', 'infrastruktúra', 'modern'],
                'premium_szorzo': 1.25,
                'leiras': 'Orbánhegy, jó infrastruktúra, bevásárlóközpontok'
            },
            
            'XII. ker. Krisztinaváros': {
                'kulcsszavak': ['krisztina', 'várfok', 'attila', 'logodi',
                               'várnegyed', 'központhoz közel', 'történelmi'],
                'premium_szorzo': 1.25,
                'leiras': 'Krisztinaváros, várnegyedhez közel'
            },
            
            # JÓ LAKÓNEGYEDEK - 1.15x szorzó
            'XII. ker. Németvölgy': {
                'kulcsszavak': ['németvölgy', 'német völgy', 'csendes utca',
                               'lakónegyed', 'családbarát', 'iskola'],
                'premium_szorzo': 1.15,
                'leiras': 'Németvölgyi lakónegyed'
            },
            
            'XII. ker. Farkasrét': {
                'kulcsszavak': ['farkasrét', 'farkas rét', 'új lakópark',
                               'modern építés', 'fejlesztés', 'tömegközlekedés'],
                'premium_szorzo': 1.15,
                'leiras': 'Farkasréti új fejlesztések'
            },
            
            # STANDARD TERÜLETEK - 1.0x szorzó
            'XII. ker. Belváros': {
                'kulcsszavak': ['belváros', 'központ', 'közlekedés', 'móricz zsigmond',
                               'szolgáltatás', 'bolt', 'étterem', 'kultúra'],
                'premium_szorzo': 1.0,
                'leiras': 'XII. kerületi központi rész'
            },
            
            # FORGALMAS TERÜLETEK - 0.9x szorzó
            'XII. ker. Főutak mellett': {
                'kulcsszavak': ['budai alsó rakpart', 'hegyalja út', 'alkotás',
                               'forgalmas', 'zajos', 'nagy forgalom'],
                'premium_szorzo': 0.9,
                'leiras': 'Főutak melletti forgalmas terület'
            }
        }
        
        return self._find_best_district_match(varosreszek, teljes_szoveg, 'XII. ker. Általános')

    def _categorize_general_district(self, cim, reszletes_cim, leiras):
        """Általános városrész kategorizálás minden lokációhoz"""
        
        # Egyesített szöveg elemzéshez
        teljes_szoveg = f"{cim} {reszletes_cim} {leiras}".lower()
        
        # ÁLTALÁNOS KATEGÓRIÁK - LOKÁCIÓ FÜGGETLEN
        varosreszek = {
            # PRÉMIUM TERÜLETEK
            'Prémium villa negyed': {
                'kulcsszavak': ['villa', 'panoráma', 'erdő', 'természet', 'csendes',
                               'prestige', 'exkluzív', 'nagy telek', 'luxus'],
                'premium_szorzo': 1.3,
                'leiras': 'Prémium villa negyed'
            },
            
            # JÓ LOKÁCIÓK
            'Jó lakónegyed': {
                'kulcsszavak': ['lakópark', 'modern', 'új építés', 'családbarát',
                               'infrastruktúra', 'iskola', 'óvoda', 'szolgáltatás'],
                'premium_szorzo': 1.15,
                'leiras': 'Jó lakónegyed, megfelelő infrastruktúrával'
            },
            
            # STANDARD
            'Központi terület': {
                'kulcsszavak': ['központ', 'belváros', 'közlekedés', 'bolt',
                               'szolgáltatás', 'munkahely', 'kultúra'],
                'premium_szorzo': 1.0,
                'leiras': 'Központi elhelyezkedés'
            },
            
            # PROBLÉMÁS TERÜLETEK
            'Forgalmas terület': {
                'kulcsszavak': ['főút', 'forgalmas', 'zajos', 'autópálya',
                               'nagy forgalom', 'zajterhelés', 'levegőszennyezés'],
                'premium_szorzo': 0.9,
                'leiras': 'Forgalmas, zajos környezet'
            }
        }
        
        return self._find_best_district_match(varosreszek, teljes_szoveg, 'Általános terület')

    def _categorize_budapest_general_district(self, cim, reszletes_cim, leiras):
        """Általános budapesti városrész kategorizálás"""
        
        # Egyesített szöveg elemzéshez
        teljes_szoveg = f"{cim} {reszletes_cim} {leiras}".lower()
        
        # BUDAPEST ÁLTALÁNOS KATEGÓRIÁK
        varosreszek = {
            'Budapest prémium kerület': {
                'kulcsszavak': ['i.', 'ii.', 'v.', 'vi.', 'várnegyed', 'budai hegyek',
                               'rózsadomb', 'villa', 'panoráma', 'prémium'],
                'premium_szorzo': 1.3,
                'leiras': 'Prémium budapesti kerület'
            },
            
            'Budapest jó lokáció': {
                'kulcsszavak': ['iii.', 'ix.', 'xi.', 'xiii.', 'lakópark',
                               'tömegközlekedés', 'modern', 'fejlesztés'],
                'premium_szorzo': 1.1,
                'leiras': 'Jó budapesti lokáció'
            },
            
            'Budapest külső kerület': {
                'kulcsszavak': ['xiv.', 'xv.', 'xvi.', 'xvii.', 'xviii.', 'xix.', 'xx.',
                               'xxi.', 'xxii.', 'xxiii.', 'külső', 'agglomeráció'],
                'premium_szorzo': 0.95,
                'leiras': 'Külső budapesti kerület'
            }
        }
        
        return self._find_best_district_match(varosreszek, teljes_szoveg, 'Budapest általános')

    def _categorize_erd_district(self, cim, reszletes_cim, leiras):
        """Érd városrész kategorizálás"""
        
        # Egyesített szöveg elemzéshez
        teljes_szoveg = f"{cim} {reszletes_cim} {leiras}".lower()
        
        # ÉRD VÁROSRÉSZEK
        varosreszek = {
            'Érd Erdliget - Prémium': {
                'kulcsszavak': ['erdliget', 'erdő', 'természet', 'csendes',
                               'villa', 'családi ház', 'nagy telek'],
                'premium_szorzo': 1.2,
                'leiras': 'Erdligeti prémium terület'
            },
            
            'Érd Központ': {
                'kulcsszavak': ['központ', 'belváros', 'szolgáltatás', 'közlekedés',
                               'bevásárlóközpont', 'iskola', 'óvoda'],
                'premium_szorzo': 1.0,
                'leiras': 'Érdi központi terület'
            },
            
            'Érd Lakótelep': {
                'kulcsszavak': ['lakótelep', 'panel', 'tégla', 'társasház',
                               'tömeges beépítés', 'sűrű beépítés'],
                'premium_szorzo': 0.9,
                'leiras': 'Érdi lakótelepi rész'
            }
        }
        
        return self._find_best_district_match(varosreszek, teljes_szoveg, 'Érd általános')

    def _find_best_district_match(self, varosreszek, teljes_szoveg, default_category):
        """Legjobb városrész egyezés keresése"""
        
        best_match = {
            'kategoria': default_category,
            'premium_szorzo': 1.0,
            'leiras': 'Általános terület'
        }
        
        max_score = 0
        
        for varosresz_nev, info in varosreszek.items():
            score = 0
            for kulcsszo in info['kulcsszavak']:
                if kulcsszo in teljes_szoveg:
                    score += teljes_szoveg.count(kulcsszo)
            
            if score > max_score:
                max_score = score
                best_match = {
                    'kategoria': varosresz_nev,
                    'premium_szorzo': info['premium_szorzo'],
                    'leiras': info['leiras']
                }
        
        return best_match

    def _categorize_budaors_district(self, cim, reszletes_cim, leiras):
        """Budaörs városrész kategorizálás és prémium szorzó meghatározás"""
        
        # Egyesített szöveg elemzéshez
        teljes_szoveg = f"{cim} {reszletes_cim} {leiras}".lower()
        
        # BUDAÖRS VÁROSRÉSZEK ÉS PRÉMIUM KATEGÓRIÁK
        varosreszek = {
            # PRÉMIUM VILLA NEGYEDEK - 1.3x szorzó
            'Budaörs Központ - Villa Negyed': {
                'kulcsszavak': ['villa park', 'villa negyed', 'károlyi', 'fő utca', 'templom', 
                               'központ', 'budaörsi főút', 'ady endre', 'petőfi sándor'],
                'premium_szorzo': 1.3,
                'leiras': 'Központi villa negyed, magas presztizsű környezet'
            },
            
            # KIVÁLÓ LOKÁCIÓK - 1.25x szorzó  
            'Budaörs Kamaraerdő': {
                'kulcsszavak': ['kamaraerdő', 'erdő szél', 'természet közel', 'erdős környezet',
                               'csendes', 'zöldövezet', 'panorámás'],
                'premium_szorzo': 1.25,
                'leiras': 'Erdőszéli, természetközeli, csendes környék'
            },
            
            'Budaörs Törökbálint határ': {
                'kulcsszavak': ['törökbálint', 'törökbálinti', 'határ', 'nagy telek',
                               'tágas', 'családi ház', 'sarok telek'],
                'premium_szorzo': 1.2,
                'leiras': 'Törökbálint határán, nagy telkekkel'
            },
            
            # JÓ LAKÓNEGYEDEK - 1.15x szorzó
            'Budaörs Új Lakónegyed': {
                'kulcsszavak': ['új építésű', 'lakópark', 'modern', 'újépítésű',
                               'családbarát', 'infrastruktúra', 'szolgáltatások'],
                'premium_szorzo': 1.15,
                'leiras': 'Modern lakónegyed, jó infrastruktúrával'
            },
            
            # STANDARD TERÜLETEK - 1.0x szorzó
            'Budaörs Belváros': {
                'kulcsszavak': ['belváros', 'központhoz közel', 'közlekedés',
                               'bolt', 'iskola', 'óvoda', 'szolgáltatás'],
                'premium_szorzo': 1.0,
                'leiras': 'Belvárosi, jó közlekedéssel és szolgáltatásokkal'
            },
            
            # FORGALMAS/ZAJOS TERÜLETEK - 0.9x szorzó
            'Budaörs Főút mellett': {
                'kulcsszavak': ['főút', 'forgalmas', 'zajos', 'közlekedés',
                               'autópálya', 'nagy forgalom', 'zajterhelés'],
                'premium_szorzo': 0.9,
                'leiras': 'Főút melletti, forgalmas terület'
            },
            
            # IPARI KÖRNYEZET - 0.85x szorzó
            'Budaörs Ipari Környék': {
                'kulcsszavak': ['ipari', 'telephely', 'raktár', 'kereskedelmi',
                               'üzemi', 'logisztikai', 'műhely'],
                'premium_szorzo': 0.85,
                'leiras': 'Ipari környezetben'
            }
        }
        
        # Városrész azonosítás - pontszám alapú
        best_match = {
            'kategoria': 'Budaörs Általános',
            'premium_szorzo': 1.0,
            'leiras': 'Általános budaörsi terület'
        }
        
        max_score = 0
        
        for varosresz_nev, info in varosreszek.items():
            score = 0
            for kulcsszo in info['kulcsszavak']:
                if kulcsszo in teljes_szoveg:
                    score += teljes_szoveg.count(kulcsszo)
            
            if score > max_score:
                max_score = score
                best_match = {
                    'kategoria': varosresz_nev,
                    'premium_szorzo': info['premium_szorzo'],
                    'leiras': info['leiras']
                }
        
        return best_match
    
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
        """Részletes CSV mentés Enhanced Text Feature-kkel + duplikáció szűrés"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"ingatlan_reszletes_{self.location_name}_{timestamp}.csv"
            
            df = pd.DataFrame(detailed_data)
            original_count = len(df)
            
            # 🔥 DUPLIKÁCIÓ SZŰRÉS - ár, terület és cím alapján
            print(f"🧹 Részletes adatok duplikáció szűrése...")
            print(f"   📊 Eredeti rekordok: {original_count}")
            
            if len(df) > 0:
                # Duplikátumok eltávolítása (első előfordulást megtartjuk)
                df_clean = df.drop_duplicates(subset=['cim', 'teljes_ar', 'terulet'], keep='first')
                duplicates_removed = original_count - len(df_clean)
                
                print(f"   🗑️ Eltávolított duplikátumok: {duplicates_removed}")
                print(f"   ✅ Egyedi rekordok: {len(df_clean)}")
                
                df = df_clean
            
            # Oszlop sorrend
            priority_cols = ['id', 'cim', 'reszletes_cim', 'teljes_ar', 'reszletes_ar', 
                           'terulet', 'nm_ar', 'szobak', 'epitesi_ev', 'szint', 
                           'ingatlan_allapota', 'futes', 'erkely', 'parkolas', 
                           'hirdeto_tipus', 'kepek_szama', 'leiras', 'link']
            
            available_priority = [col for col in priority_cols if col in df.columns]
            other_cols = [col for col in df.columns if col not in available_priority]
            
            final_columns = available_priority + other_cols
            df = df[final_columns]
            
            # Alap CSV mentése (backup) PIPE elválasztóval
            df.to_csv(base_filename, index=False, encoding='utf-8-sig', sep='|')
            print(f"💾 Alap CSV mentve (| elválasztó): {base_filename}")
            print(f"📊 Végső rekordszám: {len(df)}")
            
            # 🌟 ENHANCED TEXT FEATURES + LOKÁCIÓ GENERÁLÁS
            print(f"🔍 Enhanced text feature-k + lokáció elemzés...")
            
            # Szövegelemző inicializálása GOOGLE MAPS API-VAL
            # Ha van GOOGLE_MAPS_API_KEY environment változó, használja
            google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY', None)
            analyzer = IngatlanSzovegelemzo(google_maps_api_key=google_api_key)
            
            if google_api_key:
                print("🗺️ Google Maps API használatával - ENHANCED lokáció elemzés")
            else:
                print("⚠️ Google Maps API key nincs beállítva - fallback lokáció elemzés")
            
            # Új oszlopok inicializálása - MODERN ÁRFELHAJTÓ KATEGÓRIÁK (2025) + ENHANCED LOKÁCIÓ
            text_feature_columns = {
                # Pontszám oszlopok - ÚJ MODERN KATEGÓRIÁK
                'zold_energia_premium_pont': 0.0,
                'wellness_luxury_pont': 0.0,
                'smart_technology_pont': 0.0,
                'premium_design_pont': 0.0,
                'premium_parking_pont': 0.0,
                'premium_location_pont': 0.0,
                'build_quality_pont': 0.0,
                'negativ_tenyezok_pont': 0.0,
                
                # Binary dummy változók (0/1) - modern kategóriákhoz
                'van_zold_energia': 0,
                'van_wellness_luxury': 0,
                'van_smart_tech': 0,
                'van_premium_design': 0,
                'van_premium_parking': 0,
                'van_premium_location': 0,
                'van_build_quality': 0,
                'van_negativ_elem': 0,
                
                # Összesített pontszámok
                'ossz_pozitiv_pont': 0.0,
                'ossz_negativ_pont': 0.0,
                'netto_szoveg_pont': 0.0,
                
                # 🗺️ ENHANCED LOKÁCIÓ OSZLOPOK - XII. KERÜLETI RÉSZEK + KOORDINÁTÁK
                'enhanced_keruleti_resz': 'Ismeretlen',
                'lokacio_konfidencia': 0.0,
                'lokacio_elemzesi_modszer': 'none',
                'lokacio_forras': 'none',
                'lokacio_elemzesek_szama': 0,
                
                # 🌍 GEOLOKÁCIÓS KOORDINÁTÁK
                'geo_latitude': None,
                'geo_longitude': None,
                'geo_address_from_api': '',
                
                # VÁROSRÉSZ KATEGORIZÁLÁS - BUDAÖRS SPECIFIKUS (régi, kompatibilitás miatt)
                'varosresz_kategoria': 'Ismeretlen',
                'varosresz_premium_szorzo': 1.0
            }
            
            # Oszlopok hozzáadása - SettingWithCopyWarning elkerülése
            df = df.copy()  # Explicit másolat készítése
            for col_name, default_value in text_feature_columns.items():
                df[col_name] = default_value
            
            # Text feature-k generálása minden sorhoz
            processed_count = 0
            for idx, row in df.iterrows():
                if pd.notna(row.get('leiras', '')):
                    # Kategória pontszámok kinyerése az ÚJ kategóriák alapján
                    scores, details = analyzer.extract_category_scores(row['leiras'])
                    
                    # MODERN KATEGÓRIÁK pontszámainak mentése
                    df.at[idx, 'zold_energia_premium_pont'] = scores.get('ZOLD_ENERGIA_PREMIUM', 0)
                    df.at[idx, 'wellness_luxury_pont'] = scores.get('WELLNESS_LUXURY', 0)
                    df.at[idx, 'smart_technology_pont'] = scores.get('SMART_TECHNOLOGY', 0)
                    df.at[idx, 'premium_design_pont'] = scores.get('PREMIUM_DESIGN', 0)
                    df.at[idx, 'premium_parking_pont'] = scores.get('PREMIUM_PARKING', 0)
                    df.at[idx, 'premium_location_pont'] = scores.get('PREMIUM_LOCATION', 0)
                    df.at[idx, 'build_quality_pont'] = scores.get('BUILD_QUALITY', 0)
                    df.at[idx, 'negativ_tenyezok_pont'] = scores.get('NEGATIV_TENYEZOK', 0)
                    
                    # Binary dummy változók - modern kategóriákhoz
                    df.at[idx, 'van_zold_energia'] = 1 if scores.get('ZOLD_ENERGIA_PREMIUM', 0) > 0 else 0
                    df.at[idx, 'van_wellness_luxury'] = 1 if scores.get('WELLNESS_LUXURY', 0) > 0 else 0
                    df.at[idx, 'van_smart_tech'] = 1 if scores.get('SMART_TECHNOLOGY', 0) > 0 else 0
                    df.at[idx, 'van_premium_design'] = 1 if scores.get('PREMIUM_DESIGN', 0) > 0 else 0
                    df.at[idx, 'van_premium_parking'] = 1 if scores.get('PREMIUM_PARKING', 0) > 0 else 0
                    df.at[idx, 'van_premium_location'] = 1 if scores.get('PREMIUM_LOCATION', 0) > 0 else 0
                    df.at[idx, 'van_build_quality'] = 1 if scores.get('BUILD_QUALITY', 0) > 0 else 0
                    df.at[idx, 'van_negativ_elem'] = 1 if scores.get('NEGATIV_TENYEZOK', 0) < 0 else 0
                    
                    # 🗺️ ENHANCED LOKÁCIÓ ELEMZÉS - ÚJ 4-lépéses rendszer
                    enhanced_location = analyzer.enhanced_location_analysis(
                        address=str(row.get('cim', '')),
                        description=str(row.get('leiras', '')),
                        price=row.get('ar', None)
                    )
                    
                    df.at[idx, 'enhanced_keruleti_resz'] = enhanced_location['keruleti_resz']
                    df.at[idx, 'lokacio_konfidencia'] = enhanced_location['konfidencia']
                    df.at[idx, 'lokacio_elemzesi_modszer'] = enhanced_location['elemzesi_modszer']
                    df.at[idx, 'lokacio_forras'] = enhanced_location['forras']
                    df.at[idx, 'lokacio_elemzesek_szama'] = enhanced_location['elemzesek_szama']
                    
                    # 🌍 GEOLOKÁCIÓS KOORDINÁTÁK MENTÉSE
                    df.at[idx, 'geo_latitude'] = enhanced_location.get('latitude', None)
                    df.at[idx, 'geo_longitude'] = enhanced_location.get('longitude', None)
                    df.at[idx, 'geo_address_from_api'] = enhanced_location.get('geocoded_address', '')
                    
                    # VÁROSRÉSZ KATEGORIZÁLÁS - DINAMIKUS LOKÁCIÓ ALAPJÁN (régi rendszer, kompatibilitás)
                    varosresz_info = self._categorize_district(str(row.get('cim', '')), str(row.get('reszletes_cim', '')), str(row.get('leiras', '')), self.location_name)
                    df.at[idx, 'varosresz_kategoria'] = varosresz_info['kategoria']
                    df.at[idx, 'varosresz_premium_szorzo'] = varosresz_info['premium_szorzo']
                    
                    # Összesített pontszámok - MODERN KATEGÓRIÁK városrész szorzóval
                    pozitiv_kategoriak = ['ZOLD_ENERGIA_PREMIUM', 'WELLNESS_LUXURY', 'SMART_TECHNOLOGY', 
                                         'PREMIUM_DESIGN', 'PREMIUM_PARKING', 'PREMIUM_LOCATION', 'BUILD_QUALITY']
                    
                    ossz_pozitiv = sum(max(0, scores.get(kat, 0)) for kat in pozitiv_kategoriak)
                    ossz_negativ = abs(min(0, scores.get('NEGATIV_TENYEZOK', 0)))
                    netto_pont = ossz_pozitiv - ossz_negativ
                    
                    # Városrész prémium szorzó alkalmazása
                    netto_pont_adjusted = netto_pont * varosresz_info['premium_szorzo']
                    
                    df.at[idx, 'ossz_pozitiv_pont'] = round(ossz_pozitiv, 2)
                    df.at[idx, 'ossz_negativ_pont'] = round(ossz_negativ, 2)
                    df.at[idx, 'netto_szoveg_pont'] = round(netto_pont_adjusted, 2)
                    df.at[idx, 'netto_szoveg_pont'] = round(ossz_pozitiv - ossz_negativ, 2)
                    
                    processed_count += 1
            
            print(f"✅ Text feature-k generálva: {processed_count} ingatlanhoz")
            
            # Enhanced CSV mentése PIPE elválasztóval
            df.to_csv(base_filename, index=False, encoding='utf-8-sig', sep='|')
            
            print(f"📊 Oszlopok: {len(df.columns)} (+ {len(text_feature_columns)} text feature)")

            return base_filename  # Az enhanced fájlt adjuk vissza
            
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
