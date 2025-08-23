#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DASHBOARD GENERATOR SCRIPT
==========================

🎯 HASZNÁLAT:
python generate_dashboard.py <csv_filename>

📋 PÉLDA:
python generate_dashboard.py ingatlan_reszletes_orszagut_vizivaros_ii_krisztinavaros_xii_20250823_135915.csv

⚡ A script automatikusan:
1. Felismeri a lokáció nevét a CSV fájlnévből
2. Generálja a megfelelő CSV pattern-eket
3. Létrehozza a dashboard Python fájlt
4. Opcionálisan elindítja a Streamlit dashboard-ot
"""

import sys
import os
import re
import glob
from datetime import datetime

def extract_location_from_csv_name(csv_filename):
    """Lokáció név kinyerése CSV fájlnévből és dashboard-kompatibilis név generálása"""
    try:
        # Eltávolítjuk a .csv kiterjesztést és az "ingatlan_reszletes_" előtagot
        base_name = csv_filename.replace('.csv', '').replace('ingatlan_reszletes_', '')
        
        # Dátum részek eltávolítása (pl. _20250823_135915)
        # Pattern: _YYYYMMDD_HHMMSS formátum keresése és eltávolítása
        base_name = re.sub(r'_\d{8}_\d{6}$', '', base_name)
        
        # Koordináta jelölők eltávolítása (pl. _koordinatak_20250822_221556)
        base_name = re.sub(r'_koordinatak_\d{8}_\d{6}$', '', base_name)
        
        print(f"🔍 Feldolgozott base_name: {base_name}")
        
        # Speciális lokáció nevek felismerése és konverziója
        location_mapping = {
            # Kerületek
            'xi_ker': 'XI. KERÜLET',
            'xii_ker': 'XII. KERÜLET', 
            'xxii_ker': 'XXII. KERÜLET',
            
            # Összetett nevek
            'torokbalint_tukorhegy': 'TÖRÖKBÁLINT-TÜKÖRHEGY',
            'budaors': 'BUDAÖRS',
            'kobanya_hegyi_lakotelep': 'KŐBÁNYA HEGYI LAKÓTELEP',
            'orszagut_vizivaros_ii_krisztinavaros_xii': 'ORSZÁGÚT-VÍZIVÁROS II.-KRISZTINAVÁROS XII.',
            'erd_erdliget_diosd': 'ÉRD-ÉRDLIGET-DIÓSD',
            'uerd_erdliget_diosd': 'ÉRD-ÉRDLIGET-DIÓSD',  # Javított verzió a bug miatt
        }
        
        # Keressük meg a megfelelő lokációt
        for key, display_name in location_mapping.items():
            if key in base_name or base_name == key:
                return display_name, key
        
        # Ha nincs előre definiált mapping, akkor generáljuk
        # Alulvonások cseréje szóközökre és nagybetűsítés
        display_name = base_name.replace('_', ' ').upper()
        dashboard_key = base_name
        
        return display_name, dashboard_key
        
    except Exception as e:
        print(f"❌ Location extraction hiba: {e}")
        return "ISMERETLEN LOKÁCIÓ", "ismeretlen"

def generate_csv_patterns(dashboard_key, csv_filename):
    """CSV pattern-ek generálása a dashboard_key és eredeti fájlnév alapján"""
    patterns = []
    
    # 1. Pontos pattern a fájlnév alapján (időbélyeg nélkül)
    base_pattern = csv_filename
    # Dátum rész eltávolítása a pattern-ből, wildcardal helyettesítése
    base_pattern = re.sub(r'_\d{8}_\d{6}', '_*', base_pattern)
    base_pattern = re.sub(r'_koordinatak_\d{8}_\d{6}', '_koordinatak_*', base_pattern)
    patterns.append(base_pattern)
    
    # 2. Általános pattern ugyanazzal a prefixszel
    prefix_pattern = f"ingatlan_reszletes_{dashboard_key}_*.csv"
    if prefix_pattern not in patterns:
        patterns.append(prefix_pattern)
    
    # 3. Lista pattern is (ha létezik)
    list_pattern = f"ingatlan_lista_{dashboard_key}_*.csv" 
    patterns.append(list_pattern)
    
    # 4. Koordinátás pattern
    coord_pattern = f"ingatlan_reszletes_{dashboard_key}_*_koordinatak_*.csv"
    patterns.append(coord_pattern)
    
    # 5. Fallback wildcard pattern
    wildcard_pattern = f"ingatlan_*{dashboard_key}*.csv"
    if wildcard_pattern not in patterns:
        patterns.append(wildcard_pattern)
    
    return patterns

def create_dashboard_file(location_display, dashboard_key, csv_patterns, csv_filename):
    """Dashboard fájl létrehozása a template alapján"""
    
    # Template fájl beolvasása
    template_path = "streamlit_app.py"
    if not os.path.exists(template_path):
        print(f"❌ Template fájl nem található: {template_path}")
        return None
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Placeholder-ek cseréje
        dashboard_content = template_content.replace('{{LOCATION_NAME}}', location_display)
        
        # CSV pattern-ek behelyettesítése (max 3 pattern)
        for i, pattern in enumerate(csv_patterns[:3], 1):
            placeholder = f"{{{{CSV_PATTERN_{i}}}}}"
            dashboard_content = dashboard_content.replace(placeholder, pattern)
        
        # Maradék placeholder-eket is cseréljük, ha kevesebb mint 3 pattern van
        for i in range(len(csv_patterns) + 1, 4):
            placeholder = f"{{{{CSV_PATTERN_{i}}}}}"
            dashboard_content = dashboard_content.replace(placeholder, f'"# Nincs több pattern"')
        
        # Dashboard fájl neve
        dashboard_filename = f"dashboard_{dashboard_key}.py"
        
        # Fájl mentése
        with open(dashboard_filename, 'w', encoding='utf-8') as f:
            f.write(dashboard_content)
        
        print(f"✅ Dashboard létrehozva: {dashboard_filename}")
        return dashboard_filename
        
    except Exception as e:
        print(f"❌ Dashboard létrehozási hiba: {e}")
        return None

def verify_csv_exists(csv_filename):
    """CSV fájl létezésének ellenőrzése"""
    if not os.path.exists(csv_filename):
        print(f"❌ CSV fájl nem található: {csv_filename}")
        
        # Keressünk hasonló fájlokat
        similar_files = glob.glob(f"ingatlan_*{csv_filename.split('_')[2] if '_' in csv_filename else csv_filename[:10]}*.csv")
        if similar_files:
            print(f"🔍 Hasonló fájlok találhatók:")
            for file in similar_files[:5]:
                print(f"   - {file}")
        return False
    return True

def test_dashboard_patterns(csv_patterns):
    """CSV pattern-ek tesztelése - ellenőrizzük, hogy léteznek-e matching fájlok"""
    print(f"\n🧪 CSV Pattern tesztelés:")
    found_files = []
    
    for i, pattern in enumerate(csv_patterns, 1):
        matching_files = glob.glob(pattern)
        print(f"   Pattern {i}: {pattern}")
        print(f"   Találatok: {len(matching_files)}")
        
        if matching_files:
            # Legfrissebb fájl megkeresése
            latest_file = max(matching_files, key=lambda f: os.path.getmtime(f))
            print(f"   -> Legfrissebb: {latest_file}")
            found_files.extend(matching_files)
        else:
            print(f"   -> Nincs találat")
        print()
    
    return found_files

def main():
    """Főalkalmazás"""
    print("🎯 DASHBOARD GENERATOR")
    print("=" * 50)
    
    # Argumentum ellenőrzés
    if len(sys.argv) != 2:
        print("❌ Használat: python generate_dashboard.py <csv_filename>")
        print("\n📋 Példa:")
        print("   python generate_dashboard.py ingatlan_reszletes_orszagut_vizivaros_ii_krisztinavaros_xii_20250823_135915.csv")
        sys.exit(1)
    
    csv_filename = sys.argv[1]
    print(f"📊 CSV fájl: {csv_filename}")
    
    # CSV fájl létezésének ellenőrzése
    if not verify_csv_exists(csv_filename):
        sys.exit(1)
    
    # Lokáció kinyerése
    location_display, dashboard_key = extract_location_from_csv_name(csv_filename)
    print(f"📍 Lokáció: {location_display}")
    print(f"🔑 Dashboard key: {dashboard_key}")
    
    # CSV pattern-ek generálása
    csv_patterns = generate_csv_patterns(dashboard_key, csv_filename)
    print(f"\n📋 Generált CSV pattern-ek:")
    for i, pattern in enumerate(csv_patterns, 1):
        print(f"   {i}. {pattern}")
    
    # Pattern-ek tesztelése
    found_files = test_dashboard_patterns(csv_patterns)
    
    if not found_files:
        print("⚠️  FIGYELMEZTETÉS: Egyik CSV pattern sem talált fájlokat!")
        response = input("Folytatod a dashboard generálást? (i/n): ")
        if response.lower() != 'i':
            print("❌ Dashboard generálás megszakítva.")
            sys.exit(1)
    
    # Dashboard létrehozása
    dashboard_file = create_dashboard_file(location_display, dashboard_key, csv_patterns, csv_filename)
    
    if dashboard_file:
        print(f"\n🎉 SIKERES GENERÁLÁS!")
        print(f"📄 Dashboard fájl: {dashboard_file}")
        print(f"📊 Lokáció: {location_display}")
        print(f"📋 CSV pattern-ek száma: {len(csv_patterns)}")
        
        # Streamlit indítási opció
        print(f"\n🚀 Dashboard indítás:")
        print(f"   python -m streamlit run {dashboard_file} --server.port 8501")
        
        # Automatikus indítás kérdése
        response = input("\nElindítsam most a dashboard-ot? (i/n): ")
        if response.lower() == 'i':
            import subprocess
            try:
                print(f"🚀 Streamlit indítása...")
                subprocess.run([
                    "python", "-m", "streamlit", "run", dashboard_file, 
                    "--server.port", "8501", "--server.headless", "false"
                ])
            except KeyboardInterrupt:
                print(f"\n⏹️  Dashboard leállítva.")
            except Exception as e:
                print(f"❌ Streamlit indítási hiba: {e}")
                print(f"💡 Manuális indítás: python -m streamlit run {dashboard_file} --server.port 8501")
    else:
        print("❌ Dashboard generálás sikertelen!")
        sys.exit(1)

if __name__ == "__main__":
    main()
