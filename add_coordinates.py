#!/usr/bin/env python3
"""
INGATLAN CSV KOORDINÁTA BŐVÍTŐ
==============================
Hozzáadja a Google Maps koordinátákat bármely enhanced CSV-hez
"""
import pandas as pd
import googlemaps
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# .env fájl betöltése
load_dotenv()

def add_coordinates_to_csv(csv_file=None):
    """Koordináták hozzáadása a megadott CSV-hez"""
    
    print("🌍 INGATLAN CSV KOORDINÁTA BŐVÍTŐ")
    print("="*50)
    
    # Google Maps API inicializálás
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY environment változó nincs beállítva!")
        return False
        
    gmaps = googlemaps.Client(key=api_key)
    print("✅ Google Maps API inicializálva")
    
    # CSV fájl meghatározása
    if csv_file:
        # Konkrét fájl megadva paraméterként
        if not os.path.exists(csv_file):
            print(f"❌ A megadott CSV fájl nem található: {csv_file}")
            return False
        input_csv = csv_file
        print(f"📂 Input CSV: {csv_file}")
    else:
        # Legfrissebb enhanced CSV keresése (XII. kerület)
        import glob
        csv_files = glob.glob("ingatlan_reszletes_XII*.csv")
        if not csv_files:
            print("❌ Nincs XII. kerületi CSV fájl!")
            return False
        input_csv = max(csv_files, key=os.path.getmtime)
        print(f"📂 Input CSV: {input_csv}")
    
    # CSV betöltése
    try:
        df = pd.read_csv(input_csv, sep='|', encoding='utf-8', on_bad_lines='skip')
        print(f"✅ Betöltve: {len(df)} rekord")
    except Exception as e:
        print(f"❌ CSV betöltési hiba: {e}")
        return False
    
    # Koordináták hozzáadása
    successful_geocodes = 0
    failed_geocodes = 0
    
    print(f"\n🗺️ Koordináta geocoding {len(df)} rekordra...")
    
    for i, row in df.iterrows():
        address = row['cim']
        print(f"   {i+1:3d}/{len(df)}: {address[:50]}", end="")
        
        try:
            # Geocoding
            result = gmaps.geocode(address + ", Hungary")
            
            if result:
                location = result[0]['geometry']['location']
                formatted_addr = result[0]['formatted_address']
                
                # Koordináták mentése
                df.at[i, 'geo_latitude'] = location['lat']
                df.at[i, 'geo_longitude'] = location['lng'] 
                df.at[i, 'geo_address_from_api'] = formatted_addr
                
                print(f" ✅ ({location['lat']:.4f}, {location['lng']:.4f})")
                successful_geocodes += 1
                
            else:
                print(f" ❌ Nincs találat")
                failed_geocodes += 1
                
        except Exception as e:
            print(f" ❌ Hiba: {e}")
            failed_geocodes += 1
        
        # Rate limiting - max 50 kérés/másodperc
        time.sleep(0.05)  # 20ms késleltetés
    
    print(f"\n📊 GEOCODING EREDMÉNY:")
    print(f"   ✅ Sikeres: {successful_geocodes}")
    print(f"   ❌ Sikertelen: {failed_geocodes}")
    print(f"   📈 Sikerességi arány: {successful_geocodes/len(df)*100:.1f}%")
    
    # Koordinátákkal bővített CSV mentése
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Output fájl név generálása az input alapján
    if csv_file:
        # Input fájl nevéből készíti a koordinátás verziót
        base_name = os.path.splitext(os.path.basename(csv_file))[0]
        # Ha már koordinátás, akkor új timestamp-pel
        if "_koordinatak_" in base_name:
            base_name = base_name.split("_koordinatak_")[0]
        output_file = f"{base_name}_koordinatak_{timestamp}.csv"
    else:
        # XII. kerület default
        output_file = f"ingatlan_reszletes_XII_KERÜLET_koordinatak_{timestamp}.csv"
    
    try:
        df.to_csv(output_file, sep='|', encoding='utf-8', index=False)
        print(f"\n💾 Koordinátákkal bővített CSV mentve: {output_file}")
        
        # Ellenőrzés
        coord_count = df['geo_latitude'].notna().sum()
        print(f"✅ Ellenőrzés: {coord_count}/{len(df)} rekordban van koordináta")
        
        return output_file
        
    except Exception as e:
        print(f"❌ CSV mentési hiba: {e}")
        return False

if __name__ == "__main__":
    # Parancssori argumentum ellenőrzése
    csv_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    result = add_coordinates_to_csv(csv_file)
    if result:
        print(f"\n🎯 SIKERES KOORDINÁTA BŐVÍTÉS!")
        print(f"📄 Új fájl: {result}")
    else:
        print(f"\n💥 KOORDINÁTA BŐVÍTÉS SIKERTELEN!")
