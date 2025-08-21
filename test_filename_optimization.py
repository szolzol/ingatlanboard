#!/usr/bin/env python3
"""
Teszt script az új egyszerűsített fájlnév generáláshoz - EREDETI KÓDDAL
"""

import sys
import os
import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import re

def extract_location_original(url):
    """EREDETI _extract_location függvény a kódból"""
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
            'epitesu', 'uj', 'ujszeru', 'felujitott', 'jo', 'allapot'  # Részletek is
        ]
        
        for szuro in allapot_szurok:
            location_only = location_only.replace(f'+{szuro}', '').replace(f'{szuro}+', '').replace(szuro, '')
        
        # Ár szűrők eltávolítása (pl: 80-500-mFt, 80-500-mft, 100_200_m_ft)
        location_only = re.sub(r'\+?\d+[\-_]\d+[\-_]?m?[Ff]t\+?', '', location_only)
        location_only = re.sub(r'\+?\d+_\d+_m_ft\+?', '', location_only)
        location_only = re.sub(r'\+?\d+\-\d+\-m\-?ft\+?', '', location_only)
        location_only = re.sub(r'\+?\d+\-\d+\-mft\+?', '', location_only)
        
        # Egyedi számok eltávolítása (pl. "20" négyzetméter vagy egyéb szűrők) 
        location_only = re.sub(r'\+?\d{1,3}\+?', '', location_only)
        
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
        
        # Biztonságos fájlnév készítése
        safe_name = re.sub(r'[^\w\-_]', '_', location_only)
        safe_name = safe_name.replace('-', '_')
        safe_name = re.sub(r'_{2,}', '_', safe_name)
        safe_name = safe_name.strip('_')
        
        return safe_name[:50] if safe_name else "ingatlan_kereses"
    except Exception as e:
        print(f"⚠️ Location extraction hiba: {e}")
        return "ingatlan_kereses"

def test_filename_generation():
    """Teszteljük az új fájlnév generálást"""
    print("🧪 Fájlnév optimalizáció teszt - EREDETI ALGORITMUS")
    print("="*60)
    
    # Test különböző URL-ekkel
    test_cases = [
        "https://ingatlan.com/lista/elado+haz+80-500-mFt+budaors",
        "https://ingatlan.com/lista/elado+haz+80-600-mFt+budapest+xii-ker+20",
        "https://ingatlan.com/lista/elado+haz+uj-epitesu+ujszeru+felujitott+jo-allapot",
        "https://ingatlan.com/lista/elado+haz+erd+erdliget"
    ]
    
    for url in test_cases:
        location = extract_location_original(url)
        
        # Fájlnév generálás szimulálása
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"ingatlan_reszletes_{location}_{timestamp}.csv"
        
        print(f"🔗 URL: {url}")
        print(f"📍 Location: {location}")
        print(f"📁 Filename: {base_filename}")
        print("-" * 60)

if __name__ == "__main__":
    test_filename_generation()
