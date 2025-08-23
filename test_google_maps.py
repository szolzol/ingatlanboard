#!/usr/bin/env python3
"""
Google Maps API teszt script
"""
import googlemaps
import os
from dotenv import load_dotenv

# .env fájl betöltése
load_dotenv()

def test_google_maps_api():
    # API kulcs
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    print(f"🔑 API kulcs: {'Beállítva' if api_key else 'NINCS'}")
    
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY environment változó nincs beállítva!")
        return False
    
    print(f"📏 API kulcs hossza: {len(api_key)} karakter")
    print(f"🔤 API kulcs kezdete: {api_key[:15]}...")
    
    try:
        # Google Maps kliens inicializálás
        gmaps = googlemaps.Client(key=api_key)
        print("✅ Google Maps kliens inicializálva")
        
        # Tesztelés különböző címekkel
        test_addresses = [
            "Budapest XII. kerület, Svábhegy",
            "Budapest XII. kerület, Orbánhegy", 
            "Budapest XII. kerület, Virányos út 1",
            "Budapest XII. kerület, Istenhegyi út 93"
        ]
        
        success_count = 0
        
        for i, address in enumerate(test_addresses, 1):
            print(f"\n🧪 TESZT {i}: {address}")
            
            try:
                result = gmaps.geocode(address)
                
                if result:
                    location = result[0]['geometry']['location']
                    formatted_address = result[0]['formatted_address']
                    
                    print(f"   ✅ Siker!")
                    print(f"   📍 Koordináták: {location['lat']:.6f}, {location['lng']:.6f}")
                    print(f"   🏠 Formázott cím: {formatted_address}")
                    success_count += 1
                else:
                    print(f"   ❌ Nincs találat")
                    
            except Exception as e:
                print(f"   ❌ Geocoding hiba: {e}")
                print(f"   🔍 Hiba típusa: {type(e).__name__}")
        
        print(f"\n📊 EREDMÉNY: {success_count}/{len(test_addresses)} cím sikeres")
        
        if success_count > 0:
            print("🎉 Google Maps API MŰKÖDIK!")
            return True
        else:
            print("💥 Google Maps API NEM MŰKÖDIK!")
            return False
            
    except Exception as e:
        print(f"❌ Google Maps kliens hiba: {e}")
        print(f"🔍 Hiba típusa: {type(e).__name__}")
        
        # Részletes hiba elemzés
        error_str = str(e).lower()
        if "request_denied" in error_str:
            print("\n🚨 REQUEST_DENIED hiba - lehetséges okok:")
            print("   1. API kulcs nincs engedélyezve Geocoding API-hoz")
            print("   2. Google Cloud Console-ban aktiválni kell a Geocoding API-t")
            print("   3. API kulcs korlátozva van (IP, domain, stb.)")
            
        return False

if __name__ == "__main__":
    test_google_maps_api()
