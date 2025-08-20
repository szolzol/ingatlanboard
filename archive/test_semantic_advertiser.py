#!/usr/bin/env python3
"""
HIRDETŐ TÍPUS SZEMANTIKAI ELEMZŐ TESZTER
=========================================
"""

import pandas as pd
import re

def detect_advertiser_type(description):
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

def main():
    """Teszt futtatása"""
    print("🧠 HIRDETŐ TÍPUS SZEMANTIKAI ELEMZŐ TESZT")
    print("="*50)
    
    # CSV beolvasása
    try:
        csv_file = "ingatlan_reszletes_elado_haz_erd_erdliget_20250820_004656.csv"
        df = pd.read_csv(csv_file)
        
        print(f"📊 Beolvasva: {len(df)} ingatlan")
        print("\n🔍 ÚJ ELEMZÉS vs RÉGI ELEMZÉS:")
        print("-" * 80)
        
        changes = 0
        
        for i, row in df.iterrows():
            old_type = row.get('hirdeto_tipus', 'ismeretlen')
            description = row.get('leiras', '')
            
            new_type = detect_advertiser_type(description)
            
            if old_type != new_type:
                changes += 1
                print(f"📝 {i+1}. ingatlan: {old_type} → {new_type}")
                
                # Leírás rövid előnézet
                if description:
                    preview = description[:100].replace('\n', ' ')
                    print(f"   💬 \"{preview}...\"")
                print()
        
        print("="*50)
        print(f"🔄 Változások száma: {changes}/{len(df)}")
        
        # Statisztikák
        new_types = [detect_advertiser_type(row.get('leiras', '')) for _, row in df.iterrows()]
        
        from collections import Counter
        new_stats = Counter(new_types)
        old_stats = Counter(df['hirdeto_tipus'])
        
        print(f"\n📊 ÚJ STATISZTIKÁK:")
        for type_name, count in new_stats.items():
            print(f"   {type_name}: {count}")
        
        print(f"\n📊 RÉGI STATISZTIKÁK:")
        for type_name, count in old_stats.items():
            print(f"   {type_name}: {count}")
        
    except Exception as e:
        print(f"❌ Hiba: {e}")

if __name__ == "__main__":
    main()
