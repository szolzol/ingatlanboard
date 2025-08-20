#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ENHANCED MODE DEMO
Közvetlenül teszteli az Enhanced Mode funkcionalitást
"""

from optimized_ml_model import OptimalizaltIngatlanModell
from analyze_descriptions_focused import IngatlanSzovegelemzo
import pandas as pd

def demo_enhanced_mode():
    """Enhanced Mode demo közvetlenül Python-ban"""
    print("🏡 ENHANCED MODE DEMO")
    print("=" * 50)
    
    # 1. MODELL INICIALIZÁLÁS ÉS TANÍTÁS
    print("1. Modell inicializálás és tanítás Enhanced CSV-vel...")
    
    modell = OptimalizaltIngatlanModell()
    enhanced_csv = "ingatlan_reszletes_enhanced_text_features.csv"
    
    # Enhanced adatok betöltése és tanítás
    try:
        df = pd.read_csv(enhanced_csv, encoding='utf-8-sig')
        processed_df = modell.process_dashboard_data(df)
        modell.modell_tanitas(processed_df)
        
        print(f"✅ Modell tanítva: Enhanced={modell.enhanced_trained}, Features={len(modell.feature_names)}")
        print(f"   Alap features: {[f for f in modell.feature_names if f not in modell.text_features][:3]}...")
        print(f"   Text features: {[f for f in modell.feature_names if f in modell.text_features]}")
        
    except Exception as e:
        print(f"❌ Hiba a modell tanításnál: {e}")
        return
    
    # 2. SZÖVEGELEMZŐ INICIALIZÁLÁS
    print("\n2. Szövegelemző inicializálás...")
    szovegelemzo = IngatlanSzovegelemzo()
    
    # 3. TESZT LEÍRÁSOK
    print("\n3. Teszt leírások elemzése...")
    
    alap_leiras = "Családi ház eladó. 3 szoba, kert."
    luxus_leiras = "Luxus villa medencével, szaunával, panorámás kilátással, dupla garázs, exkluzív környék"
    
    # Szövegek elemzése
    alap_eredmeny = szovegelemzo.elemez_leiras(alap_leiras)
    luxus_eredmeny = szovegelemzo.elemez_leiras(luxus_leiras)
    
    print(f"📝 Alap leírás pontok: {alap_eredmeny['ossz_pozitiv_pont']}")
    print(f"✨ Luxus leírás pontok: {luxus_eredmeny['ossz_pozitiv_pont']}")
    
    # 4. TESZTHAZ ADATOK KÉSZÍTÉSE
    print("\n4. Tesztház adatok készítése...")
    
    # Alapvető ingatlan adatok
    tesztadatok_alap = {
        'terulet': 150,
        'szobak_szam': 4, 
        'allapot_szam': 6,
        'haz_kora': 15,
        'telekterulet_szam': 800,
        'van_parkolas': 1
    }
    
    # Származtatott features hozzáadása
    tesztadatok_alap['terulet_log'] = pd.Series([tesztadatok_alap['terulet']]).apply(lambda x: pd.np.log1p(x)).iloc[0]
    tesztadatok_alap['kor_kategoria'] = 3  # Fiatal ház
    tesztadatok_alap['telek_log'] = pd.Series([tesztadatok_alap['telekterulet_szam']]).apply(lambda x: pd.np.log1p(x)).iloc[0]
    tesztadatok_alap['nagy_telek'] = 1 if tesztadatok_alap['telekterulet_szam'] > 600 else 0
    tesztadatok_alap['terulet_x_allapot'] = tesztadatok_alap['terulet'] * tesztadatok_alap['allapot_szam']
    tesztadatok_alap['m2_per_szoba'] = tesztadatok_alap['terulet'] / tesztadatok_alap['szobak_szam']
    
    # 5. ÁRBECSLÉS ALAP LEÍRÁSSAL
    print("\n5. Árbecslés alap leírással...")
    
    alap_tesztadatok = tesztadatok_alap.copy()
    for feature in modell.text_features:
        alap_tesztadatok[feature] = alap_eredmeny.get(feature, 0)
    
    # Features sorrendezése
    feature_values = [alap_tesztadatok.get(f, 0) for f in modell.feature_names]
    
    try:
        ar_alap = modell.legjobb_modell.predict([feature_values])[0]
        print(f"💰 Becsült ár (alap): {ar_alap:.1f} M Ft")
    except Exception as e:
        print(f"❌ Hiba az alap becslésben: {e}")
        return
    
    # 6. ÁRBECSLÉS LUXUS LEÍRÁSSAL
    print("\n6. Árbecslés luxus leírással...")
    
    luxus_tesztadatok = tesztadatok_alap.copy()
    for feature in modell.text_features:
        luxus_tesztadatok[feature] = luxus_eredmeny.get(feature, 0)
    
    feature_values_luxus = [luxus_tesztadatok.get(f, 0) for f in modell.feature_names]
    
    try:
        ar_luxus = modell.legjobb_modell.predict([feature_values_luxus])[0]
        print(f"✨ Becsült ár (luxus): {ar_luxus:.1f} M Ft")
        
        kulonbseg = ar_luxus - ar_alap
        szazalek = (kulonbseg / ar_alap) * 100
        
        print(f"\n🎯 EREDMÉNY:")
        print(f"   Alap leírás:  {ar_alap:.1f} M Ft")
        print(f"   Luxus leírás: {ar_luxus:.1f} M Ft")
        print(f"   Különbség:    +{kulonbseg:.1f} M Ft ({szazalek:+.1f}%)")
        
        if kulonbseg > 0:
            print("🎉 ✅ ENHANCED MODE MŰKÖDIK! A luxus leírás magasabb árat eredményez!")
        else:
            print("❌ Enhanced Mode nem működik megfelelően.")
            
    except Exception as e:
        print(f"❌ Hiba a luxus becslésben: {e}")

if __name__ == "__main__":
    demo_enhanced_mode()
