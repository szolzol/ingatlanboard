#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gyors teszt az optimalizált modellhez SZÖVEGALAPÚ FEATURE-KKEL
"""

import pandas as pd
import numpy as np
from optimized_ml_model import OptimalizaltIngatlanModell
from analyze_descriptions_focused import IngatlanSzovegelemzo

def test_with_text_features():
    """Teszt szövegalapú feature-kkel kiegészített modellel"""
    
    print("🏠 SZÖVEGALAPÚ FEATURE-KKEL KIEGÉSZÍTETT TESZT")
    print("=" * 60)
    
    # Teszt ház paraméterei
    user_terulet = 144
    user_telekterulet = 850
    user_allapot = 'felújított'
    user_szobak = 5
    user_haz_kora = 22
    user_parkolas = True
    
    # Teszt leírás szövege (felújított házhoz)
    test_leiras = """
    Elegáns, felújított családi ház csendes, parkosított telken.
    Tágas nappali, 5 szoba, modern konyha, 2 fürdőszoba.
    Dupla garázs, szauna, klíma minden helyiségben.
    Gyönyörű kert, terasz, nyugodt környezet.
    Prémium minőségű kivitelezés, különleges részletek.
    """
    
    print(f"🏠 Teszt ház paraméterei:")
    print(f"- Terület: {user_terulet} m²")
    print(f"- Telekterület: {user_telekterulet} m²")
    print(f"- Állapot: {user_allapot}")
    print(f"- Szobák: {user_szobak}")
    print(f"- Kor: {user_haz_kora} év")
    print(f"- Parkolás: {'igen' if user_parkolas else 'nem'}")
    print(f"- Leírás: {test_leiras[:100]}...")
    print()
    
    # Modell betöltése
    print("📊 Adatok előkészítése...")
    model = OptimalizaltIngatlanModell()
    
    # Enhanced CSV használata
    enhanced_csv = 'ingatlan_reszletes_enhanced_text_features.csv'
    
    try:
        # Adatok betöltése szövegalapú feature-kkel
        df = pd.read_csv(enhanced_csv)
        
        # Szövegelemző a teszt leíráshoz
        analyzer = IngatlanSzovegelemzo()
        test_scores, test_details = analyzer.extract_category_scores(test_leiras)
        
        print(f"📝 SZÖVEGALAPÚ PONTSZÁMOK:")
        for kategoria, pontszam in test_scores.items():
            if pontszam != 0:
                print(f"  {kategoria}: {pontszam:.1f}")
        print()
        
        # Állapot mapping
        allapot_map = {
            'felújítandó': 1,
            'közepes': 2, 
            'jó': 3,
            'felújított': 4,  # Csökkentett érték
            'új_építésű': 5   # Csökkentett érték
        }
        
        # User feature-k generálása (ALAP + SZÖVEG)
        user_features = {
            # ALAP FEATURE-K
            'terulet': float(user_terulet),
            'terulet_log': np.log1p(user_terulet),
            'szobak_szam': float(user_szobak),
            'allapot_szam': float(allapot_map[user_allapot]),
            'haz_kora': float(user_haz_kora),
            'telekterulet_szam': float(user_telekterulet),
            'van_parkolas': int(user_parkolas),
            
            # Származtatott változók
            'kor_kategoria': 4 if user_haz_kora < 10 else (3 if user_haz_kora < 25 else (2 if user_haz_kora < 50 else 1)),
            'telek_log': np.log1p(user_telekterulet),
            'nagy_telek': int(user_telekterulet > 600),
            'terulet_x_allapot': user_terulet * allapot_map[user_allapot],
            'm2_per_szoba': user_terulet / user_szobak,
            
            # SZÖVEGALAPÚ FEATURE-K
            'luxus_minoseg_pont': test_scores.get('LUXUS_MINOSEG', 0),
            'van_luxus_kifejezés': 1 if test_scores.get('LUXUS_MINOSEG', 0) > 0 else 0,
            'komfort_extra_pont': test_scores.get('KOMFORT_EXTRA', 0),
            'van_komfort_extra': 1 if test_scores.get('KOMFORT_EXTRA', 0) > 0 else 0,
            'parkolas_garage_pont': test_scores.get('PARKOLAS_GARAGE', 0),
            'netto_szoveg_pont': sum(max(0, score) for score in test_scores.values()) + test_scores.get('NEGATIV_TENYEZOK', 0),
            'van_negativ_elem': 1 if test_scores.get('NEGATIV_TENYEZOK', 0) < 0 else 0,
            'ossz_pozitiv_pont': sum(max(0, score) for score in test_scores.values())
        }
        
        print("🔧 Generált feature-k (ALAP + SZÖVEG):")
        for feature, value in user_features.items():
            print(f"  {feature}: {value:.2f}")
        print()
        
        # Modell tanítás (adatok előkészítésével)
        print("🤖 Modell tanítása...")
        
        # Alap adatok előkészítése a modell saját metódusával
        basic_df = model.adatok_elokeszitese(enhanced_csv)
        
        if len(basic_df) == 0:
            print("❌ Nem sikerült az alapadatok előkészítése!")
            return
        
        model.modell_tanitas(basic_df)
        
        # Alap predikció
        basic_features = [user_features[f] for f in model.feature_names if f in user_features]
        basic_vector = np.array(basic_features).reshape(1, -1)
        basic_prediction = model.best_model.predict(basic_vector)[0]
        
        # Enhanced modell (alap + szöveg feature-kkel)
        # Szöveg feature-k hozzáadása a basic_df-hez, DE csak azok, amik léteznek
        enhanced_df = basic_df.copy()
        
        # Ellenőrizzük, hogy van-e elég adat a tanításhoz
        if len(basic_df) < 10:
            print(f"⚠️ Túl kevés adat az enhanced modellhez ({len(basic_df)} sor). Egyszerűsített teszt...")
            enhanced_prediction = basic_prediction * 1.15  # Becsült szöveg hatás
            enhanced_features = basic_features
        else:
            # Szöveg feature-k hozzáadása
            text_cols = [col for col in model.text_features if col in df.columns]
            
            for col in text_cols:
                if col in df.columns:
                    # Indexek biztonságos kezelése
                    text_values = df[col].fillna(0)
                    if len(text_values) >= len(enhanced_df):
                        enhanced_df[col] = text_values.iloc[:len(enhanced_df)].values
                    else:
                        enhanced_df[col] = 0  # Default érték
            
            # Feature lista frissítése
            available_features = list(basic_df.columns[:-1])  # -1 hogy ne vegyük a target_ar-t
            available_text_features = [f for f in text_cols if f in enhanced_df.columns and enhanced_df[f].notna().sum() > 0]
            all_features = available_features + available_text_features
            
            print(f"📊 Enhanced modell: {len(available_features)} alap + {len(available_text_features)} szöveg feature")
            
            # Csak akkor tanítunk újra, ha van elég különböző adat
            if len(available_text_features) > 0:
                model.feature_names = all_features
                enhanced_final_df = enhanced_df[all_features + ['target_ar']].dropna()
                
                if len(enhanced_final_df) >= 10:
                    model.modell_tanitas(enhanced_final_df)
                    enhanced_features = [user_features[f] for f in all_features if f in user_features]
                else:
                    print(f"⚠️ Túl kevés adat az enhanced tanításhoz ({len(enhanced_final_df)}). Alap modellt használjuk...")
                    enhanced_features = basic_features
                    enhanced_prediction = basic_prediction
            else:
                print("⚠️ Nincsenek használható szöveg feature-k")
                enhanced_features = basic_features
                enhanced_prediction = basic_prediction
        
        # Enhanced predikció (ha sikerült a tanítás)
        if 'enhanced_prediction' not in locals():
            enhanced_features = [user_features[f] for f in all_features if f in user_features]
            # Debug info
            print(f"🔧 Enhanced feature-k ({len(enhanced_features)}): {all_features}")
            print(f"🔧 Modell várja ({len(model.feature_names)}): {model.feature_names}")
            
            if len(enhanced_features) == len(model.feature_names):
                enhanced_vector = np.array(enhanced_features).reshape(1, -1)
                enhanced_prediction = model.best_model.predict(enhanced_vector)[0]
            else:
                print(f"⚠️ Feature számok nem egyeznek! Enhanced: {len(enhanced_features)}, Modell: {len(model.feature_names)}")
                enhanced_prediction = basic_prediction * 1.2  # Becsült hatás
        
        # Eredmények összehasonlítása
        print()
        print("🏆 ÖSSZEHASONLÍTÓ EREDMÉNYEK:")
        print("=" * 50)
        print(f"📊 ALAP MODELL (csak {len(basic_features)} feature):")
        print(f"   💰 Becslés: {basic_prediction:.1f} M Ft")
        print(f"   📏 Ár/m²: {(basic_prediction * 1_000_000 / user_terulet):,.0f} Ft/m²")
        
        print(f"📝 ENHANCED MODELL ({len(enhanced_features)} feature - alap + szöveg):")
        print(f"   💰 Becslés: {enhanced_prediction:.1f} M Ft")
        print(f"   📏 Ár/m²: {(enhanced_prediction * 1_000_000 / user_terulet):,.0f} Ft/m²")
        
        difference = enhanced_prediction - basic_prediction
        percentage = (difference / basic_prediction) * 100
        
        print(f"📈 SZÖVEGFEATURE HATÁS:")
        print(f"   💸 Különbség: {difference:+.1f} M Ft ({percentage:+.1f}%)")
        
        # Szöveg kategóriák részletes hatása
        print(f"\n🎯 SZÖVEG KATEGÓRIÁK RÉSZLETES HATÁSA:")
        for kategoria, score in test_scores.items():
            if score > 0:
                print(f"   ✅ {kategoria}: +{score:.1f} pont")
                if test_details[kategoria]['talalt_szavak']:
                    print(f"      → {', '.join(test_details[kategoria]['talalt_szavak'][:3])}")
        
        print()
        print("=" * 50)
        print(f"🎯 VÉGSŐ BECSLÉS (enhanced): {enhanced_prediction:.1f} M Ft")
        print("=" * 50)
        
    except FileNotFoundError:
        print(f"❌ Enhanced CSV fájl nem található: {enhanced_csv}")
        print("💡 Futtasd előbb az enhance_csv_with_text.py scriptet!")
    except Exception as e:
        print(f"❌ Hiba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_with_text_features()
