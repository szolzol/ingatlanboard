"""
Szemantikai elemzés következtetések kinyerése az enhanced CSV-ből
"""

import pandas as pd
import numpy as np

def get_semantic_insights():
    """Szemantikai elemzés statisztikai következtetések"""
    
    # Enhanced CSV betöltése
    try:
        df = pd.read_csv('ingatlan_reszletes_enhanced_text_features.csv', encoding='utf-8-sig')
    except:
        print("Enhanced CSV nem található, alapadatokból dolgozunk")
        return {}
    
    insights = {}
    total_records = len(df)
    
    # Luxus kategória elemzése
    if 'van_luxus_kifejezés' in df.columns:
        luxus_count = df['van_luxus_kifejezés'].sum()
        luxus_pct = (luxus_count / total_records) * 100
        insights['luxus'] = {
            'count': int(luxus_count),
            'percentage': round(luxus_pct, 1),
            'avg_score': round(df['luxus_minoseg_pont'].mean(), 2) if 'luxus_minoseg_pont' in df.columns else 0
        }
    
    # Kert/külső kategória
    if 'van_kert_terulet' in df.columns:
        kert_count = df['van_kert_terulet'].sum()
        kert_pct = (kert_count / total_records) * 100
        insights['kert'] = {
            'count': int(kert_count),
            'percentage': round(kert_pct, 1),
            'avg_score': round(df['kert_kulso_pont'].mean(), 2) if 'kert_kulso_pont' in df.columns else 0
        }
    
    # Parkolás kategória
    if 'van_garage_parkolas' in df.columns:
        parking_count = df['van_garage_parkolas'].sum()
        parking_pct = (parking_count / total_records) * 100
        insights['parkolas'] = {
            'count': int(parking_count),
            'percentage': round(parking_pct, 1),
            'avg_score': round(df['parkolas_garage_pont'].mean(), 2) if 'parkolas_garage_pont' in df.columns else 0
        }
    
    # Komfort extra kategória  
    if 'van_komfort_extra' in df.columns:
        komfort_count = df['van_komfort_extra'].sum()
        komfort_pct = (komfort_count / total_records) * 100
        insights['komfort'] = {
            'count': int(komfort_count),
            'percentage': round(komfort_pct, 1),
            'avg_score': round(df['komfort_extra_pont'].mean(), 2) if 'komfort_extra_pont' in df.columns else 0
        }
    
    # Állapot/felújítás kategória
    if 'allapot_felujitas_pont' in df.columns:
        allapot_count = (df['allapot_felujitas_pont'] > 0).sum()
        allapot_pct = (allapot_count / total_records) * 100
        insights['allapot'] = {
            'count': int(allapot_count),
            'percentage': round(allapot_pct, 1),
            'avg_score': round(df['allapot_felujitas_pont'].mean(), 2)
        }
    
    # Lokáció/környezet kategória
    if 'lokacio_kornyezet_pont' in df.columns:
        lokacio_count = (df['lokacio_kornyezet_pont'] > 0).sum()
        lokacio_pct = (lokacio_count / total_records) * 100
        insights['lokacio'] = {
            'count': int(lokacio_count),
            'percentage': round(lokacio_pct, 1),
            'avg_score': round(df['lokacio_kornyezet_pont'].mean(), 2)
        }
    
    # Terület/méret kategória
    if 'terulet_meret_pont' in df.columns:
        terulet_count = (df['terulet_meret_pont'] > 0).sum()
        terulet_pct = (terulet_count / total_records) * 100
        insights['terulet'] = {
            'count': int(terulet_count),
            'percentage': round(terulet_pct, 1),
            'avg_score': round(df['terulet_meret_pont'].mean(), 2)
        }
    
    # Összesített statisztikák
    insights['total_records'] = total_records
    
    # Ár korrelációk ha van ár adat
    if 'target_ar' in df.columns:
        ar_df = df.dropna(subset=['target_ar'])
        if len(ar_df) > 10:
            insights['price_correlations'] = {}
            
            for category in ['luxus_minoseg_pont', 'kert_kulso_pont', 'parkolas_garage_pont', 
                           'komfort_extra_pont', 'allapot_felujitas_pont', 'lokacio_kornyezet_pont']:
                if category in ar_df.columns:
                    corr = ar_df[category].corr(ar_df['target_ar'])
                    if not np.isnan(corr):
                        insights['price_correlations'][category.replace('_pont', '')] = round(corr, 3)
    
    return insights

if __name__ == "__main__":
    insights = get_semantic_insights()
    print("=== SZEMANTIKAI ELEMZÉS KÖVETKEZTETÉSEK ===")
    
    for category, data in insights.items():
        if isinstance(data, dict) and 'count' in data:
            print(f"{category.upper()}: {data['count']} hirdetés ({data['percentage']}%), átlag pontszám: {data['avg_score']}")
    
    if 'price_correlations' in insights:
        print("\n=== ÁR KORRELÁCIÓK ===")
        for cat, corr in insights['price_correlations'].items():
            print(f"{cat}: {corr}")
