#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INGATLAN CSV KOORDINÁTA BŐVÍTŐ
==============================

🎯 HASZNÁLAT:
python add_coordinates.py <csv_filename>

📋 PÉLDA:
python add_coordinates.py ingatlan_reszletes_kobany    # Koordináták hozzáadása
    result = add_coordinates_to_csv(csv_filename, api_key)
    
    if result:
        print(f"\n🎉 SIKERES KOORDINÁTA HOZZÁADÁS!")
        print(f"📄 Eredeti fájl: {csv_filename}")
        print(f"📄 Koordinátás fájl: {result}")
        print(f"\n💡 Most már használhatod a dashboard generáláshoz:")
        print(f"   python generate_dashboard.py {result}")
    else:
        print("❌ Koordináta hozzáadás sikertelen!")
        sys.exit(1)telep_20250822_093251.csv

⚡ A script automatikusan:
1. Hozzáadja a Google Maps koordinátákat (geo_latitude, geo_longitude, geo_address_from_api)
2. Létrehozza a koordinátákkal bővített CSV fájlt
3. Megtartja az eredeti fájlstruktúrát és oszlopsorrendet
"""

import pandas as pd
import googlemaps
import os
import sys
import time
import glob
from datetime import datetime

def load_env_file():
    """Egyszerű .env fájl betöltés dotenv nélkül"""
    env_vars = {}
    try:
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        return env_vars
    except Exception as e:
        print(f"⚠️  .env fájl betöltési hiba: {e}")
        return {}

def verify_csv_exists(csv_filename):
    """CSV fájl létezésének ellenőrzése"""
    if not os.path.exists(csv_filename):
        print(f"❌ CSV fájl nem található: {csv_filename}")
        
        # Keressünk hasonló fájlokat
        base_name = csv_filename.split('_')[0] if '_' in csv_filename else csv_filename[:15]
        similar_files = glob.glob(f"ingatlan_*{base_name}*.csv")[:5]
        if similar_files:
            print(f"🔍 Hasonló fájlok találhatók:")
            for file in similar_files:
                print(f"   - {file}")
        return False
    return True

def check_existing_coordinates(df):
    """Ellenőrzi, hogy van-e már koordináta adat a CSV-ben"""
    coord_columns = ['geo_latitude', 'geo_longitude', 'geo_address_from_api']
    has_coords = all(col in df.columns for col in coord_columns)
    
    if has_coords:
        existing_coords = df['geo_latitude'].notna().sum()
        print(f"📍 Meglévő koordináták: {existing_coords}/{len(df)} rekord")
        return existing_coords
    else:
        print(f"📍 Nincs meglévő koordináta adat")
        return 0

def add_coordinates_to_csv(csv_file, api_key):
    """Koordináták hozzáadása a megadott CSV-hez - JAVÍTOTT verzió"""
    
    print("🌍 INGATLAN CSV KOORDINÁTA BŐVÍTŐ")
    print("="*50)
    print(f"📊 CSV fájl: {csv_file}")
    
    # Google Maps API inicializálás
    gmaps = googlemaps.Client(key=api_key)
    print("✅ Google Maps API inicializálva")
    
    # CSV fájl ellenőrzése
    if not verify_csv_exists(csv_file):
        return False
    
    # CSV betöltése
    try:
        df = pd.read_csv(csv_file, sep='|', encoding='utf-8-sig', on_bad_lines='skip')
        print(f"✅ CSV betöltve: {len(df)} rekord")
        
        if df.empty:
            print("❌ A CSV fájl üres!")
            return False
            
    except Exception as e:
        print(f"❌ CSV betöltési hiba: {e}")
        return False
    
    # Meglévő koordináták ellenőrzése
    existing_coords = check_existing_coordinates(df)
    
    # Koordináta oszlopok hozzáadása, ha még nincsenek
    if 'geo_latitude' not in df.columns:
        df['geo_latitude'] = None
    if 'geo_longitude' not in df.columns:
        df['geo_longitude'] = None
    if 'geo_address_from_api' not in df.columns:
        df['geo_address_from_api'] = None
    
    # Címet tartalmazó oszlop ellenőrzése
    if 'cim' not in df.columns:
        print("❌ Nincs 'cim' oszlop a CSV-ben!")
        return False
    
    # Koordináták hozzáadása
    successful_geocodes = 0
    failed_geocodes = 0
    skipped_geocodes = existing_coords
    
    print(f"\n🗺️ Koordináta geocoding indítása...")
    print(f"   📋 Feldolgozandó rekordok: {len(df)}")
    print(f"   📍 Már meglévő koordináták: {existing_coords}")
    print(f"   🆕 Új geocoding szükséges: {len(df) - existing_coords}")
    
    for i, row in df.iterrows():
        # Ha már van koordináta, akkor kihagyás
        if pd.notna(row.get('geo_latitude')) and pd.notna(row.get('geo_longitude')):
            continue
            
        address = row['cim']
        print(f"   {i+1:3d}/{len(df)}: {address[:60]:<60}", end="")
        
        try:
            # Geocoding - Hungary-t hozzáadjuk a pontosság érdekében
            search_address = f"{address}, Hungary"
            result = gmaps.geocode(search_address)
            
            if result and len(result) > 0:
                location = result[0]['geometry']['location']
                formatted_addr = result[0]['formatted_address']
                
                # Koordináták mentése
                df.at[i, 'geo_latitude'] = location['lat']
                df.at[i, 'geo_longitude'] = location['lng'] 
                df.at[i, 'geo_address_from_api'] = formatted_addr
                
                print(f" ✅ ({location['lat']:.6f}, {location['lng']:.6f})")
                successful_geocodes += 1
                
            else:
                print(f" ❌ Nincs találat")
                failed_geocodes += 1
                
        except Exception as e:
            print(f" ❌ Hiba: {str(e)[:30]}...")
            failed_geocodes += 1
        
        # Rate limiting - max 50 kérés/másodperc (Google Maps limit)
        time.sleep(0.05)  # 20ms késleltetés
        
        # Progressz jelentés minden 10. elemnél
        if (i + 1) % 10 == 0:
            progress = (i + 1) / len(df) * 100
            print(f"   📊 Haladás: {progress:.1f}% ({successful_geocodes} siker, {failed_geocodes} sikertelen)")
    
    print(f"\n� GEOCODING EREDMÉNY:")
    print(f"   ✅ Sikeres geocoding: {successful_geocodes}")
    print(f"   ❌ Sikertelen geocoding: {failed_geocodes}")
    print(f"   ⏭️  Kihagyott (már volt): {skipped_geocodes}")
    print(f"   📈 Sikerességi arány: {successful_geocodes/(len(df)-skipped_geocodes)*100:.1f}%" if len(df)-skipped_geocodes > 0 else "   📈 Minden rekordnak már volt koordinátája")
    
    # Koordinátákkal bővített CSV mentése
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Output fájl név generálása az input alapján
    base_name = os.path.splitext(os.path.basename(csv_file))[0]
    
    # Ha már koordinátás, akkor új timestamp-pel
    if "_koordinatak_" in base_name:
        base_name = base_name.split("_koordinatak_")[0]
    
    output_file = f"{base_name}_koordinatak_{timestamp}.csv"
    
    try:
        # Eredeti oszlopsorrend megtartása + koordináta oszlopok a végén
        original_columns = [col for col in df.columns if col not in ['geo_latitude', 'geo_longitude', 'geo_address_from_api']]
        coord_columns = ['geo_latitude', 'geo_longitude', 'geo_address_from_api']
        final_columns = original_columns + coord_columns
        
        # CSV mentése az eredeti formátumban (pipe separator)
        df[final_columns].to_csv(output_file, sep='|', encoding='utf-8-sig', index=False)
        print(f"\n💾 Koordinátákkal bővített CSV mentve: {output_file}")
        
        # Ellenőrzés
        coord_count = df['geo_latitude'].notna().sum()
        success_rate = coord_count / len(df) * 100
        print(f"✅ Ellenőrzés: {coord_count}/{len(df)} rekordban van koordináta ({success_rate:.1f}%)")
        
        # Fájlméret info
        file_size = os.path.getsize(output_file) / 1024 / 1024  # MB
        print(f"📁 Fájlméret: {file_size:.2f} MB")
        
        return output_file
        
    except Exception as e:
        print(f"❌ CSV mentési hiba: {e}")
        return False

def main():
    """Főalkalmazás"""
    print("🌍 GPS KOORDINÁTA HOZZÁADÓ")
    print("=" * 50)
    
    # Argumentum ellenőrzés
    if len(sys.argv) != 2:
        print("❌ Használat: python add_coordinates.py <csv_filename>")
        print("\n📋 Példa:")
        print("   python add_coordinates.py ingatlan_reszletes_kobanya_hegyi_lakotelep_20250822_093251.csv")
        print("\n💡 Megjegyzések:")
        print("   - A GOOGLE_MAPS_API_KEY automatikusan betöltődik a .env fájlból")
        print("   - A script pipe (|) separátorú CSV fájlokat dolgoz fel")
        print("   - Csak azokhoz a rekordokhoz ad koordinátákat, amelyekhez még nincs")
        sys.exit(1)
    
    csv_filename = sys.argv[1]
    
    # .env fájl betöltése
    env_vars = load_env_file()
    api_key = env_vars.get('GOOGLE_MAPS_API_KEY') or os.environ.get('GOOGLE_MAPS_API_KEY')
    
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY nincs beállítva!")
        print("\n🔧 Megoldások:")
        print("1. Hozz létre .env fájlt a következő tartalommal:")
        print("   GOOGLE_MAPS_API_KEY=your_api_key_here")
        print("2. Vagy állítsd be environment változóban:")
        print('   $env:GOOGLE_MAPS_API_KEY="your_api_key_here"')
        sys.exit(1)
    
    print(f"🗝️  Google Maps API kulcs betöltve (.env fájlból: {'igen' if 'GOOGLE_MAPS_API_KEY' in env_vars else 'nem'})")
    
    # Koordináták hozzáadása
    result = add_coordinates_to_csv(csv_filename, api_key)
    
    if result:
        print(f"\n🎉 SIKERES KOORDINÁTA HOZZÁADÁS!")
        print(f"📄 Eredeti fájl: {csv_filename}")
        print(f"� Koordinátás fájl: {result}")
        print(f"\n💡 Most már használhatod a dashboard generáláshoz:")
        print(f"   python generate_dashboard.py {result}")
    else:
        print("❌ Koordináta hozzáadás sikertelen!")
        sys.exit(1)
if __name__ == "__main__":
    main()
