#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST: Streamlit Enhanced Mode funkció
Teszteli, hogy az alkalmazás valóban Enhanced Mode-ban tanít-e
"""

import pandas as pd
from optimized_ml_model import OptimalizaltIngatlanModell
import sys
import os

def test_enhanced_training():
    """Teszteli az Enhanced Mode modell tanítást"""
    print("=== STREAMLIT ENHANCED MODE TESZT ===")
    
    # Enhanced CSV betöltése
    enhanced_csv = "ingatlan_reszletes_enhanced_text_features.csv"
    if not os.path.exists(enhanced_csv):
        print(f"❌ HIBA: {enhanced_csv} nem található!")
        return False
    
    # DataFrame betöltése
    df = pd.read_csv(enhanced_csv, encoding='utf-8-sig')
    print(f"✅ Enhanced CSV betöltve: {len(df)} rekord, {len(df.columns)} oszlop")
    
    # Text feature-k ellenőrzése
    text_features = ['luxus_minoseg_pont', 'van_luxus_kifejezés', 
                    'komfort_extra_pont', 'van_komfort_extra', 
                    'parkolas_garage_pont', 'netto_szoveg_pont', 
                    'van_negativ_elem', 'ossz_pozitiv_pont']
    
    available_text = [f for f in text_features if f in df.columns]
    print(f"✅ Text features elérhetők: {len(available_text)}/8")
    for tf in available_text:
        print(f"   - {tf}")
    
    # Modell inicializálása
    modell = OptimalizaltIngatlanModell()
    print(f"✅ Modell inicializálva")
    
    # Adatok feldolgozása (ez az, ami korábban eldobta a text feature-ket)
    processed_df = modell.process_dashboard_data(df)
    
    if processed_df.empty:
        print("❌ HIBA: Adatfeldolgozás sikertelen!")
        return False
    
    print(f"✅ Adatok feldolgozva: {len(processed_df)} rekord, {len(processed_df.columns)} oszlop")
    
    # Text features ellenőrzése a feldolgozott adatokban
    available_text_processed = [f for f in text_features if f in processed_df.columns]
    print(f"✅ Text features feldolgozás után: {len(available_text_processed)}/8")
    
    if len(available_text_processed) == 0:
        print("❌ HIBA: Text features elvesztek az adatfeldolgozás során!")
        return False
    
    # Modell tanítása
    print("\n=== MODELL TANÍTÁS ===")
    modell.modell_tanitas(processed_df)
    
    # Enhanced Mode ellenőrzése
    enhanced_status = modell.enhanced_trained
    feature_count = len(modell.feature_names) if hasattr(modell, 'feature_names') else 0
    
    print(f"\n=== EREDMÉNYEK ===")
    print(f"Enhanced Mode aktív: {enhanced_status}")
    print(f"Feature-k száma: {feature_count}")
    
    if hasattr(modell, 'feature_names'):
        basic_features = [f for f in modell.feature_names if f not in text_features]
        text_features_used = [f for f in modell.feature_names if f in text_features]
        
        print(f"Alap features ({len(basic_features)}): {basic_features[:5]}...")
        print(f"Text features ({len(text_features_used)}): {text_features_used}")
    
    # Siker kritériumok
    success = (
        enhanced_status == True and 
        feature_count >= 18 and  # legalább 12 alap + 6 text
        len(available_text_processed) >= 6
    )
    
    if success:
        print("\n🎉 ✅ TESZT SIKERES! Enhanced Mode működik!")
        print("Az alkalmazásban most már működnie kellene az Enhanced Mode-nak.")
    else:
        print(f"\n❌ TESZT SIKERTELEN!")
        print(f"Enhanced: {enhanced_status}, Features: {feature_count}, Text: {len(available_text_processed)}")
    
    return success

if __name__ == "__main__":
    success = test_enhanced_training()
    sys.exit(0 if success else 1)
