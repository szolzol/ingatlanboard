#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV kiegészítése szövegalapú kategória változókkal
"""

import pandas as pd
import numpy as np
import re
from analyze_descriptions_focused import IngatlanSzovegelemzo

def augment_csv_with_text_features():
    """CSV fájl kiegészítése szövegalapú dummy változókkal"""
    
    print("🔧 CSV KIEGÉSZÍTÉSE SZÖVEGFEATURE-KKEL")
    print("=" * 50)
    
    # Eredeti CSV betöltése
    input_file = 'ingatlan_reszletes_elado_haz_erd_erdliget_20250820_014506.csv'
    output_file = 'ingatlan_reszletes_enhanced_text_features.csv'
    
    try:
        df = pd.read_csv(input_file)
        print(f"📊 Eredeti CSV betöltve: {len(df)} sor")
        
        # Szövegelemző inicializálása
        analyzer = IngatlanSzovegelemzo()
        
        # Új oszlopok inicializálása
        new_columns = {
            'luxus_minoseg_pont': 0.0,
            'kert_kulso_pont': 0.0,
            'parkolas_garage_pont': 0.0,
            'terulet_meret_pont': 0.0,
            'komfort_extra_pont': 0.0,
            'allapot_felujitas_pont': 0.0,
            'furdo_konyha_pont': 0.0,
            'lokacio_kornyezet_pont': 0.0,
            'futes_energia_pont': 0.0,
            'negativ_tenyezok_pont': 0.0,
            
            # Dummy változók (0/1)
            'van_luxus_kifejezés': 0,
            'van_kert_terulet': 0,
            'van_garage_parkolas': 0,
            'van_komfort_extra': 0,
            'van_negativ_elem': 0,
            
            # Összesített pontszámok
            'ossz_pozitiv_pont': 0.0,
            'ossz_negativ_pont': 0.0,
            'netto_szoveg_pont': 0.0
        }
        
        # Oszlopok hozzáadása a DataFrame-hez
        for col_name, default_value in new_columns.items():
            df[col_name] = default_value
        
        print(f"✅ {len(new_columns)} új oszlop hozzáadva")
        
        # Minden sor feldolgozása
        processed_count = 0
        
        for idx, row in df.iterrows():
            if pd.notna(row['leiras']):
                # Kategória pontszámok kinyerése
                scores, details = analyzer.extract_category_scores(row['leiras'])
                
                # Pontszámok mentése
                df.at[idx, 'luxus_minoseg_pont'] = scores.get('LUXUS_MINOSEG', 0)
                df.at[idx, 'kert_kulso_pont'] = scores.get('KERT_KULSO', 0)
                df.at[idx, 'parkolas_garage_pont'] = scores.get('PARKOLAS_GARAGE', 0)
                df.at[idx, 'terulet_meret_pont'] = scores.get('TERULET_MERET', 0)
                df.at[idx, 'komfort_extra_pont'] = scores.get('KOMFORT_EXTRA', 0)
                df.at[idx, 'allapot_felujitas_pont'] = scores.get('ALLAPOT_FELUJITAS', 0)
                df.at[idx, 'furdo_konyha_pont'] = scores.get('FURDO_KONYHA', 0)
                df.at[idx, 'lokacio_kornyezet_pont'] = scores.get('LOKACIO_KORNYEZET', 0)
                df.at[idx, 'futes_energia_pont'] = scores.get('FUTES_ENERGIA', 0)
                df.at[idx, 'negativ_tenyezok_pont'] = scores.get('NEGATIV_TENYEZOK', 0)
                
                # Dummy változók
                df.at[idx, 'van_luxus_kifejezés'] = 1 if scores.get('LUXUS_MINOSEG', 0) > 0 else 0
                df.at[idx, 'van_kert_terulet'] = 1 if scores.get('KERT_KULSO', 0) > 0 else 0
                df.at[idx, 'van_garage_parkolas'] = 1 if scores.get('PARKOLAS_GARAGE', 0) > 0 else 0
                df.at[idx, 'van_komfort_extra'] = 1 if scores.get('KOMFORT_EXTRA', 0) > 0 else 0
                df.at[idx, 'van_negativ_elem'] = 1 if scores.get('NEGATIV_TENYEZOK', 0) < 0 else 0
                
                # Összesített pontszámok
                pozitiv_kategoriak = ['LUXUS_MINOSEG', 'KERT_KULSO', 'PARKOLAS_GARAGE', 
                                     'TERULET_MERET', 'KOMFORT_EXTRA', 'ALLAPOT_FELUJITAS',
                                     'FURDO_KONYHA', 'LOKACIO_KORNYEZET', 'FUTES_ENERGIA']
                
                ossz_pozitiv = sum(max(0, scores.get(k, 0)) for k in pozitiv_kategoriak)
                ossz_negativ = abs(min(0, scores.get('NEGATIV_TENYEZOK', 0)))
                
                df.at[idx, 'ossz_pozitiv_pont'] = ossz_pozitiv
                df.at[idx, 'ossz_negativ_pont'] = ossz_negativ
                df.at[idx, 'netto_szoveg_pont'] = ossz_pozitiv - ossz_negativ
                
                processed_count += 1
            
            # Progress report
            if (idx + 1) % 20 == 0:
                print(f"⏳ Feldolgozva: {idx + 1}/{len(df)} sor")
        
        print(f"✅ Feldolgozva {processed_count} sor leírással")
        
        # Statisztikák
        print(f"\n📊 SZÖVEGFEATURE STATISZTIKÁK:")
        print(f"💎 Luxus kifejezés: {df['van_luxus_kifejezés'].sum()} ingatlan")
        print(f"🌳 Kert/terület: {df['van_kert_terulet'].sum()} ingatlan")
        print(f"🚗 Garázs/parkolás: {df['van_garage_parkolas'].sum()} ingatlan")
        print(f"🏡 Komfort extra: {df['van_komfort_extra'].sum()} ingatlan")
        print(f"⚠️ Negatív elem: {df['van_negativ_elem'].sum()} ingatlan")
        
        print(f"\n📈 PONTSZÁM ÁTLAGOK:")
        for col in ['luxus_minoseg_pont', 'kert_kulso_pont', 'parkolas_garage_pont',
                   'komfort_extra_pont', 'ossz_pozitiv_pont', 'netto_szoveg_pont']:
            avg_val = df[col].mean()
            print(f"  {col}: {avg_val:.2f}")
        
        # Kiegészített CSV mentése
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 Kiegészített CSV mentve: {output_file}")
        print(f"📊 Végső oszlopok száma: {len(df.columns)} (eredeti: {len(df.columns) - len(new_columns)})")
        
        return output_file, df
        
    except Exception as e:
        print(f"❌ Hiba: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def check_correlations_with_price(df):
    """Szövegfeature-k és ár közötti korreláció ellenőrzése"""
    
    print(f"\n🔍 SZÖVEGFEATURE KORRELÁCIÓ ELLENŐRZÉS")
    print("=" * 50)
    
    # Ár konvertálása
    def convert_price(price_str):
        if pd.isna(price_str):
            return np.nan
        price_str = str(price_str).replace(' ', '').replace(',', '.')
        if 'M' in price_str:
            return float(re.findall(r'[\d.]+', price_str)[0])
        elif 'E' in price_str:
            return float(re.findall(r'[\d.]+', price_str)[0]) / 1000
        else:
            numbers = re.findall(r'[\d.]+', price_str)
            if numbers:
                price = float(numbers[0])
                return price / 1000000 if price > 1000 else price
        return np.nan
    
    df_temp = df.copy()
    df_temp['price_mft'] = df_temp['teljes_ar'].apply(convert_price)
    df_priced = df_temp[df_temp['price_mft'].notna()]
    
    if len(df_priced) == 0:
        print("❌ Nincsenek áras adatok!")
        return
    
    # Korreláció számítás
    text_columns = [col for col in df.columns if any(x in col for x in 
                   ['luxus_', 'kert_', 'parkolas_', 'komfort_', 'terulet_', 'ossz_', 'netto_', 'van_'])]
    
    correlations = {}
    for col in text_columns:
        if col in df_priced.columns:
            corr = df_priced[col].corr(df_priced['price_mft'])
            if not pd.isna(corr):
                correlations[col] = corr
    
    # Rendezés korreláció szerint
    sorted_corrs = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
    
    print(f"📊 TOP KORRELÁCIÓK (árazott ingatlanok: {len(df_priced)}):")
    for col, corr in sorted_corrs[:15]:
        effect = "📈" if corr > 0 else "📉"
        print(f"  {effect} {col:<25}: {corr:>7.3f}")

def main():
    """Főprogram"""
    
    # CSV kiegészítése
    output_file, enhanced_df = augment_csv_with_text_features()
    
    if enhanced_df is not None:
        # Korrelációk ellenőrzése
        check_correlations_with_price(enhanced_df)
        
        print(f"\n✅ SIKERES CSV KIEGÉSZÍTÉS!")
        print(f"📁 Új fájl: {output_file}")
        print(f"🔧 Használatra kész a továbbfejlesztett árbecslőben!")
        
        return output_file, enhanced_df
    else:
        print("❌ A CSV kiegészítés nem sikerült!")
        return None, None

if __name__ == "__main__":
    main()
