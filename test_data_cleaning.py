#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GYORS TESZT - Javított adattisztítás ellenőrzése
"""

import pandas as pd
import numpy as np
from optimized_ml_model import OptimalizaltIngatlanModell

def test_data_cleaning():
    """Gyors teszt a javított adattisztításhoz"""
    
    print("🔧 ADATTISZTÍTÁS TESZT")
    print("=" * 50)
    
    try:
        # Modell inicializálása
        model = OptimalizaltIngatlanModell()
        
        # CSV betöltés
        csv_file = "ingatlan_reszletes_elado_haz_erd_erdliget_20250820_014506.csv"
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        
        print(f"📊 Eredeti adatok: {len(df)} rekord")
        
        # Dashboard adatok feldolgozása (javított verzió)
        processed_df = model.process_dashboard_data(df)
        
        print(f"✅ Feldolgozott adatok: {len(processed_df)} rekord")
        print(f"📈 Megtartott adatok: {len(processed_df)/len(df)*100:.1f}%")
        
        if len(processed_df) >= 50:
            print("🎯 SIKERES! Elegendő adat a modell tanításához.")
        else:
            print("⚠️ FIGYELMEZTETŐ! Kevés adat a megbízható modellhez.")
        
        # Feature-k ellenőrzése
        print(f"\n🔧 Elérhető feature-k:")
        available_features = [f for f in model.significant_features if f in processed_df.columns]
        for i, feature in enumerate(available_features, 1):
            missing_pct = (processed_df[feature].isna().sum() / len(processed_df)) * 100
            print(f"  {i:2d}. {feature:<20} - {missing_pct:.1f}% hiányzik")
        
        # Oszlopok statisztika
        print(f"\n📋 Dataset info:")
        print(f"   • Összes oszlop: {len(processed_df.columns)}")
        print(f"   • Elérhető feature: {len(available_features)}")
        print(f"   • Target változó: {'target_ar' in processed_df.columns}")
        
        # Hiányzó értékek összesítése
        total_missing = processed_df.isna().sum().sum()
        total_cells = len(processed_df) * len(processed_df.columns)
        missing_pct = (total_missing / total_cells) * 100
        print(f"   • Össz hiányzó érték: {missing_pct:.1f}%")
        
        return processed_df
        
    except Exception as e:
        print(f"❌ HIBA: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_data_cleaning()
    if result is not None:
        print("\n🎉 TESZT SIKERES!")
    else:
        print("\n💥 TESZT SIKERTELEN!")
