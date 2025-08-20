"""
Enhanced Mode teljes teszt - modell tanítás + predikció
"""

import sys
import numpy as np
import pandas as pd
sys.path.append('.')

from optimized_ml_model import OptimalizaltIngatlanModell
from analyze_descriptions_focused import IngatlanSzovegelemzo

# Enhanced CSV betöltése
print("=== ENHANCED CSV BETÖLTÉSE ===")
df = pd.read_csv('ingatlan_reszletes_enhanced_text_features.csv', encoding='utf-8-sig')
print(f"Adatok: {len(df)} rekord, {len(df.columns)} oszlop")

# Szöveges feature-k ellenőrzése
text_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['luxus', 'komfort', 'parkol', 'pont', 'van_'])]
print(f"Szöveges feature-k: {len(text_cols)}")
print("Első pár:", text_cols[:5])

# Modell létrehozása és tanítása
print("\n=== MODELL TANÍTÁS ===")
model = OptimalizaltIngatlanModell()
clean_df = model.process_dashboard_data(df)
print(f"Tisztított adatok: {len(clean_df)} rekord")

if len(clean_df) > 10:
    # Modell tanítása (csendes módban, print nélkül)
    model.modell_tanitas(clean_df)
    
    print(f"Tanítás kész! Enhanced: {getattr(model, 'enhanced_trained', False)}")
    print(f"Feature-k száma: {len(getattr(model, 'feature_names', []))}")
    
    # Test predikció
    print("\n=== PREDIKCIÓ TESZT ===")
    
    # Alap feature-k (150m2 ház, 5 szoba, 25 év, 600m2 telek, felújított)
    base_features = {
        'terulet': 150.0,
        'terulet_log': np.log1p(150.0),
        'szobak_szam': 5.0,
        'allapot_szam': 9.0,  # felújított
        'haz_kora': 25.0,
        'telekterulet_szam': 600.0,
        'telek_log': np.log1p(600.0),
        'van_parkolas': 1.0,
        'kor_kategoria': 2.0,
        'nagy_telek': 0.0,
        'terulet_x_allapot': 150.0 * 9.0,
        'm2_per_szoba': 150.0 / 5.0
    }
    
    # Test 1: Alap leírás
    basic_desc = "Eladó családi ház Erdligeten."
    elemzo = IngatlanSzovegelemzo()
    pontszamok_basic, _ = elemzo.extract_category_scores(basic_desc)
    
    text_features_basic = {
        'luxus_minoseg_pont': pontszamok_basic.get('LUXUS_MINOSEG', 0),
        'van_luxus_kifejezés': int(pontszamok_basic.get('LUXUS_MINOSEG', 0) > 0),
        'komfort_extra_pont': pontszamok_basic.get('KOMFORT_EXTRA', 0),
        'van_komfort_extra': int(pontszamok_basic.get('KOMFORT_EXTRA', 0) > 0),
        'parkolas_garage_pont': pontszamok_basic.get('PARKOLAS_GARAGE', 0),
        'netto_szoveg_pont': sum(pontszamok_basic.values()),
        'van_negativ_elem': int(pontszamok_basic.get('NEGATIV_TENYEZOK', 0) < 0),
        'ossz_pozitiv_pont': sum(max(0, p) for p in pontszamok_basic.values())
    }
    
    all_features_basic = {**base_features, **text_features_basic}
    
    # Test 2: Luxus leírás
    luxury_desc = "Elegáns, luxus családi ház prémium kivitelben. Designer bútorok, modern konyha, klíma minden szobában."
    pontszamok_luxury, _ = elemzo.extract_category_scores(luxury_desc)
    
    text_features_luxury = {
        'luxus_minoseg_pont': pontszamok_luxury.get('LUXUS_MINOSEG', 0),
        'van_luxus_kifejezés': int(pontszamok_luxury.get('LUXUS_MINOSEG', 0) > 0),
        'komfort_extra_pont': pontszamok_luxury.get('KOMFORT_EXTRA', 0),
        'van_komfort_extra': int(pontszamok_luxury.get('KOMFORT_EXTRA', 0) > 0),
        'parkolas_garage_pont': pontszamok_luxury.get('PARKOLAS_GARAGE', 0),
        'netto_szoveg_pont': sum(pontszamok_luxury.values()),
        'van_negativ_elem': int(pontszamok_luxury.get('NEGATIV_TENYEZOK', 0) < 0),
        'ossz_pozitiv_pont': sum(max(0, p) for p in pontszamok_luxury.values())
    }
    
    all_features_luxury = {**base_features, **text_features_luxury}
    
    # Predikció
    feature_list = model.feature_names
    
    vector_basic = np.array([all_features_basic.get(f, 0) for f in feature_list]).reshape(1, -1)
    vector_luxury = np.array([all_features_luxury.get(f, 0) for f in feature_list]).reshape(1, -1)
    
    pred_basic = model.best_model.predict(vector_basic)[0]
    pred_luxury = model.best_model.predict(vector_luxury)[0]
    
    print(f"ALAP leírás ár: {pred_basic:.1f} M Ft")
    print(f"LUXUS leírás ár: {pred_luxury:.1f} M Ft")
    print(f"KÜLÖNBSÉG: {pred_luxury - pred_basic:+.1f} M Ft ({((pred_luxury/pred_basic-1)*100):+.1f}%)")
    
    print(f"\nSzöveg pontok - Alap: {sum(pontszamok_basic.values()):.1f}, Luxus: {sum(pontszamok_luxury.values()):.1f}")
    
else:
    print("Nincs elég adat a tanításhoz!")
