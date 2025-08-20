#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ADATFELDOLGOZÁS DIAGNOSZTIKA
Megvizsgálja, hogy miért vesznek el rekordok az adatfeldolgozás során
"""

import pandas as pd
import numpy as np
from optimized_ml_model import OptimalizaltIngatlanModell

def diagnose_data_processing():
    """Diagnosztizálja az adatfeldolgozási problémákat"""
    print("=== ADATFELDOLGOZÁS DIAGNOSZTIKA ===")
    
    # Enhanced CSV betöltése
    enhanced_csv = "ingatlan_reszletes_enhanced_text_features.csv"
    df = pd.read_csv(enhanced_csv, encoding='utf-8-sig')
    print(f"✅ Eredeti adatok: {len(df)} rekord, {len(df.columns)} oszlop")
    
    # Modell inicializálása
    modell = OptimalizaltIngatlanModell()
    
    # LÉPÉSENKÉNTI DIAGNOSZTIKA
    print("\n=== LÉPÉSENKÉNTI ANALÍZIS ===")
    
    # 1. Ár parsing
    print("\n1. ÁR FELDOLGOZÁS:")
    if 'teljes_ar_millió' in df.columns:
        df_step1 = df.copy()
        df_step1['target_ar'] = df_step1['teljes_ar_millió']
        print(f"   teljes_ar_millió használva")
    elif 'teljes_ar' in df.columns:
        def parse_million_ft(text):
            if pd.isna(text):
                return None
            text = str(text).replace(',', '.')
            import re
            match = re.search(r'(\d+(?:\.\d+)?)\s*M', text)
            return float(match.group(1)) if match else None
        
        df_step1 = df.copy()
        df_step1['target_ar'] = df_step1['teljes_ar'].apply(parse_million_ft)
        print(f"   teljes_ar parsed")
    else:
        print("   ❌ HIBA: Nincs ár adat!")
        return
    
    valid_prices = df_step1['target_ar'].notna()
    print(f"   Érvényes árak: {valid_prices.sum()}/{len(df_step1)} ({valid_prices.sum()/len(df_step1)*100:.1f}%)")
    
    # 2. Outlier szűrés
    print("\n2. OUTLIER SZŰRÉS:")
    valid_mask = (df_step1['target_ar'] >= 50) & (df_step1['target_ar'] <= 300)
    df_step2 = df_step1[valid_mask].copy()
    outliers_removed = len(df_step1) - len(df_step2)
    print(f"   50M-300M Ft tartomány: {len(df_step2)}/{len(df_step1)} rekord ({outliers_removed} outlier kizárva)")
    
    if len(df_step2) < 10:
        print("   ⚠️  KRITIKUS: Túl kevés adat maradt az outlier szűrés után!")
        # Engedékenyebb outlier szűrés
        looser_mask = (df_step1['target_ar'] >= 20) & (df_step1['target_ar'] <= 500)
        df_step2_loose = df_step1[looser_mask].copy()
        print(f"   Engedékenyebb (20M-500M Ft): {len(df_step2_loose)} rekord")
        
    # 3. Feature kinyerés és hiányzó értékek
    print("\n3. FEATURE FELDOLGOZÁS:")
    essential_features = ['terulet', 'szobak_szam', 'allapot_szam', 'haz_kora', 'telekterulet_szam']
    
    for feature in essential_features:
        if feature in df_step2.columns:
            missing_count = df_step2[feature].isna().sum()
            valid_count = df_step2[feature].notna().sum()
            print(f"   {feature}: {valid_count}/{len(df_step2)} érvényes ({missing_count} hiányzó)")
        else:
            print(f"   {feature}: ❌ HIÁNYZIK!")
    
    # 4. Teljes feldolgozás tesztelése
    print("\n4. TELJES FELDOLGOZÁS:")
    try:
        processed_df = modell.process_dashboard_data(df)
        print(f"   Végeredmény: {len(processed_df)} rekord")
        
        if len(processed_df) < 50:
            print(f"   ⚠️  PROBLÉMA: Csak {len(processed_df)} rekord, legalább 50 kellene")
            print("\n=== JAVASOLT MEGOLDÁSOK ===")
            print("1. Engedékenyebb outlier szűrés (20M-500M Ft helyett 50M-300M)")
            print("2. Intelligensebb hiányzó érték kezelés")
            print("3. Kevesebb kötelező mező")
            
    except Exception as e:
        print(f"   ❌ HIBA: {e}")
        
    # 5. Adatminőség jelentés
    print("\n=== ADATMINŐSÉG JELENTÉS ===")
    print(f"Eredeti rekordok: {len(df)}")
    print(f"Érvényes árak: {valid_prices.sum()}")
    print(f"Outlier szűrés után: {len(df_step2)}")
    if 'processed_df' in locals():
        print(f"Végső feldolgozott: {len(processed_df)}")
        retention_rate = len(processed_df) / len(df) * 100
        print(f"Megőrzési arány: {retention_rate:.1f}%")
        
        if retention_rate < 50:
            print("❌ ALACSONY megőrzési arány! Javítás szükséges.")
        elif retention_rate < 70:
            print("⚠️  KÖZEPES megőrzési arány.")
        else:
            print("✅ JÓ megőrzési arány.")

if __name__ == "__main__":
    diagnose_data_processing()
