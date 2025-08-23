#!/usr/bin/env python3

import re
from urllib.parse import urlparse

# Teszteljük az URL tisztítási logikát
test_url = 'https://ingatlan.com/lista/elado+haz+budaors+4-szoba+80-500-mFt'

def _extract_location(url):
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
        print(f"URL parse hiba: {e}")
        return "ingatlan_kereses"

# Tesztelés
print("🧪 URL tisztítás tesztelése...")
print(f"Eredeti URL: {test_url}")

result = _extract_location(test_url)
print(f"Kinyert lokáció: '{result}'")
print(f"Várt eredmény: 'budaors'")

if result == 'budaors':
    print("✅ Sikeres - szobaszám szűrők eltávolítva")
else:
    print(f"❌ Hiba - várt 'budaors', kapott '{result}'")

# További tesztek
test_cases = [
    'https://ingatlan.com/lista/elado+haz+budaors+4-szoba+80-500-mFt',
    'https://ingatlan.com/lista/elado+lakas+budapest+xi+kerulet+2-szoba',
    'https://ingatlan.com/lista/elado+haz+torokbalint+felujitott+100-200-mFt',
    'https://ingatlan.com/lista/elado+lakas+uj-epitesu+ujszeru+felujitott+jo-allapotu+3-szoba-felett+orszagut+vizivaros-ii+krisztinavaros-xii',
    'https://ingatlan.com/lista/elado+haz+budaors+2-szoba-alatt+uj-epitesu'
]

print("\n🧪 További tesztek:")
for test_case in test_cases:
    result = _extract_location(test_case)
    print(f"URL: {test_case}")
    print(f"  -> '{result}'\n")
