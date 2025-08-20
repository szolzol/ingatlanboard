#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Célzott ingatlan leírás elemzés - érték-befolyásoló kategóriák alapján
"""

import pandas as pd
import numpy as np
import re
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

class IngatlanSzovegelemzo:
    def __init__(self):
        """Inicializálja a kategóriákat és kulcsszavakat"""
        
        # ÉRTÉKBEFOLYÁSOLÓ KATEGÓRIÁK ÉS KULCSSZAVAIK
        self.kategoriak = {
            'LUXUS_MINOSEG': {
                'kulcsszavak': [
                    'luxus', 'prémium', 'elegáns', 'exkluzív', 'különleges', 'lenyűgöző',
                    'kivételes', 'egyedi', 'reprezentatív', 'igényes', 'stílusos',
                    'designer', 'magas színvonal', 'minőségi', 'design', 'dizájn'
                ],
                'pontszam': 3.0
            },
            
            'KERT_KULSO': {
                'kulcsszavak': [
                    'parkosított', 'kert', 'telek', 'udvar', 'kertészkedés', 'gyümölcsfa',
                    'növények', 'fű', 'pázsit', 'virágos', 'árnyékos', 'napos kert',
                    'pergola', 'terasz', 'erkély', 'balkon', 'panoráma', 'kilátás',
                    'természet', 'zöld', 'park', 'liget'
                ],
                'pontszam': 2.5
            },
            
            'PARKOLAS_GARAGE': {
                'kulcsszavak': [
                    'garázs', 'parkoló', 'autó', 'gépkocsi', 'állás', 'fedett',
                    'saját parkoló', 'dupla garázs', 'többállásos', 'behajtó',
                    'kocsibeálló', 'két autó', '2 autó', 'parkolási lehetőség'
                ],
                'pontszam': 2.0
            },
            
            'TERULET_MERET': {
                'kulcsszavak': [
                    'tágas', 'nagy', 'széles', 'hatalmas', 'óriás', 'bőséges',
                    'tér', 'alapterület', 'hasznos', 'nappali', 'hálószoba',
                    'szoba', 'helyiség', 'kamra', 'tároló', 'pince', 'tetőtér',
                    'm2', 'négyzetméter', 'quadratmeter'
                ],
                'pontszam': 2.0
            },
            
            'KOMFORT_EXTRA': {
                'kulcsszavak': [
                    'klíma', 'légkondi', 'szauna', 'medence', 'jakuzzi', 'wellness',
                    'hőszivattyú', 'napelem', 'okos otthon', 'riasztó', 'kamerás',
                    'központi porszívó', 'padlófűtés', 'geotermikus',
                    'hangosítás', 'internet', 'kábelezés', 'optika'
                ],
                'pontszam': 2.5
            },
            
            'ALLAPOT_FELUJITAS': {
                'kulcsszavak': [
                    'felújított', 'renovált', 'korszerűsített', 'új', 'frissen',
                    'most készült', 'újépítés', 'modernizált', 'átépített',
                    'beköltözhető', 'kulcsrakész', 'azonnal', 'költözés'
                ],
                'pontszam': 2.0
            },
            
            'LOKACIO_KORNYEZET': {
                'kulcsszavak': [
                    'csendes', 'békés', 'nyugodt', 'családi', 'villa negyed',
                    'központi', 'közel', 'közlekedés', 'iskola', 'óvoda',
                    'bolt', 'bevásárlás', 'játszótér', 'sport', 'erdő', 'domb'
                ],
                'pontszam': 1.5
            },
            
            'FUTES_ENERGIA': {
                'kulcsszavak': [
                    'gáz', 'távfűtés', 'kandalló', 'cserépkályha', 'fatűzés',
                    'energiatakarékos', 'szigetelt', 'alacsony rezsi',
                    'hőszigetelés', 'műanyag ablak', 'redőny'
                ],
                'pontszam': 1.2
            },
            
            'NEGATIV_TENYEZOK': {
                'kulcsszavak': [
                    'felújítandó', 'felújításra szorul', 'régi', 'rossz állapot',
                    'problémás', 'javítandó', 'cserélendő', 'hiányos',
                    'beázás', 'nedves', 'penész', 'rezsikölts', 'drága fűtés',
                    'forgalmas', 'zajos', 'busy'
                ],
                'pontszam': -1.5
            }
        }
    
    def clean_text(self, text):
        """Szöveg tisztítása és normalizálása"""
        if pd.isna(text):
            return ""
        text = str(text).lower()
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_category_scores(self, text):
        """Kategória pontszámok kinyerése egy szövegből"""
        clean_text = self.clean_text(text)
        
        scores = {}
        details = {}
        
        for kategoria, info in self.kategoriak.items():
            kulcsszavak = info['kulcsszavak']
            pontszam = info['pontszam']
            
            talalt_szavak = []
            ossz_pontszam = 0
            
            for kulcsszo in kulcsszavak:
                if kulcsszo in clean_text:
                    talalt_szavak.append(kulcsszo)
                    # Többszörösen előforduló szavak többet érnek
                    elofordulas = clean_text.count(kulcsszo)
                    ossz_pontszam += pontszam * elofordulas
            
            scores[kategoria] = ossz_pontszam
            details[kategoria] = {
                'talalt_szavak': talalt_szavak,
                'db': len(talalt_szavak),
                'pontszam': ossz_pontszam
            }
        
        return scores, details
    
    def analyze_dataset(self, df):
        """Teljes adathalmaz elemzése"""
        
        # Csak az árazott és leírásos ingatlanokat
        df_clean = df[df['teljes_ar'].notna() & df['leiras'].notna()].copy()
        
        if len(df_clean) == 0:
            print("❌ Nincsenek megfelelő adatok!")
            return None
        
        # Ár konvertálása
        def convert_price(price_str):
            if pd.isna(price_str):
                return np.nan
            price_str = str(price_str).replace(' ', '').replace(',', '.')
            if 'M' in price_str or 'millió' in price_str.lower():
                return float(re.findall(r'[\d.]+', price_str)[0])
            elif 'E' in price_str or 'ezer' in price_str.lower():
                return float(re.findall(r'[\d.]+', price_str)[0]) / 1000
            else:
                numbers = re.findall(r'[\d.]+', price_str)
                if numbers:
                    price = float(numbers[0])
                    if price > 1000:
                        return price / 1000000
                    else:
                        return price
            return np.nan
        
        df_clean['price_mft'] = df_clean['teljes_ar'].apply(convert_price)
        df_clean = df_clean[df_clean['price_mft'].notna()]
        
        print(f"📊 Elemzett ingatlanok: {len(df_clean)}")
        print(f"💰 Ár tartomány: {df_clean['price_mft'].min():.1f} - {df_clean['price_mft'].max():.1f} M Ft")
        
        # Kategória pontszámok kinyerése minden ingatlanhoz
        all_scores = []
        all_details = []
        
        for idx, row in df_clean.iterrows():
            scores, details = self.extract_category_scores(row['leiras'])
            all_scores.append(scores)
            all_details.append(details)
        
        # DataFrame létrehozása a pontszámokból
        scores_df = pd.DataFrame(all_scores)
        scores_df['price'] = df_clean['price_mft'].values
        
        return {
            'df_clean': df_clean,
            'scores_df': scores_df,
            'all_details': all_details,
            'analyzer': self
        }
    
    def show_category_analysis(self, results):
        """Kategóriák árkorrelációs elemzése"""
        
        if not results:
            return
        
        scores_df = results['scores_df']
        
        print(f"\n🎯 KATEGÓRIÁK ÁR-KORRELÁCIÓJA:")
        print("=" * 60)
        
        correlations = {}
        
        for kategoria in self.kategoriak.keys():
            if kategoria in scores_df.columns:
                corr = scores_df[kategoria].corr(scores_df['price'])
                correlations[kategoria] = corr
        
        # Korreláció szerint rendezés
        sorted_correlations = sorted(correlations.items(), 
                                   key=lambda x: abs(x[1]) if not pd.isna(x[1]) else 0, 
                                   reverse=True)
        
        for kategoria, corr in sorted_correlations:
            if not pd.isna(corr):
                effect = "📈 Pozitív" if corr > 0 else "📉 Negatív"
                avg_score = scores_df[kategoria].mean()
                print(f"{kategoria:<25} {corr:>8.3f} (átlag: {avg_score:>6.2f}) {effect}")
        
        return correlations
    
    def show_price_impact_examples(self, results):
        """Ár-hatás példák mutatása"""
        
        scores_df = results['scores_df']
        all_details = results['all_details']
        df_clean = results['df_clean']
        
        print(f"\n💎 TOP DRÁGA INGATLANOK ELEMZÉSE:")
        print("=" * 60)
        
        # Top 5 legdrágább
        top_expensive = scores_df.nlargest(5, 'price')
        
        for idx, (_, row) in enumerate(top_expensive.iterrows()):
            price = row['price']
            orig_idx = scores_df.index[scores_df['price'] == price].tolist()[0]
            details = all_details[orig_idx]
            
            print(f"\n🏆 #{idx+1} - {price:.1f} M Ft:")
            
            for kategoria, info in details.items():
                if info['pontszam'] > 0:
                    print(f"  ✅ {kategoria}: {info['pontszam']:.1f} pont")
                    if info['talalt_szavak']:
                        print(f"     → {', '.join(info['talalt_szavak'][:5])}")
        
        print(f"\n💸 LEGOLCSÓBB INGATLANOK ELEMZÉSE:")
        print("=" * 60)
        
        # Top 5 legolcsóbb
        cheapest = scores_df.nsmallest(5, 'price')
        
        for idx, (_, row) in enumerate(cheapest.iterrows()):
            price = row['price']
            orig_idx = scores_df.index[scores_df['price'] == price].tolist()[0]
            details = all_details[orig_idx]
            
            print(f"\n💸 #{idx+1} - {price:.1f} M Ft:")
            
            # Pozitív kategóriák
            for kategoria, info in details.items():
                if info['pontszam'] > 0:
                    print(f"  ✅ {kategoria}: {info['pontszam']:.1f} pont")
            
            # Negatív kategóriák
            for kategoria, info in details.items():
                if info['pontszam'] < 0:
                    print(f"  ❌ {kategoria}: {info['pontszam']:.1f} pont")
                    if info['talalt_szavak']:
                        print(f"     → {', '.join(info['talalt_szavak'])}")

def main():
    """Főprogram"""
    
    print("🏠 CÉLZOTT INGATLAN SZÖVEGELEMZÉS")
    print("=" * 50)
    print("Fókusz: Tér, Luxus, Kert, Garázs, Extra szolgáltatások")
    
    try:
        # Adatok betöltése
        df = pd.read_csv('ingatlan_reszletes_elado_haz_erd_erdliget_20250820_014506.csv')
        
        # Elemző inicializálása
        analyzer = IngatlanSzovegelemzo()
        
        # Elemzés futtatása
        results = analyzer.analyze_dataset(df)
        
        if results:
            # Kategória korreláció elemzés
            correlations = analyzer.show_category_analysis(results)
            
            # Példa elemzések
            analyzer.show_price_impact_examples(results)
            
            print(f"\n✅ CÉLZOTT ELEMZÉS BEFEJEZVE!")
            return results
        
    except Exception as e:
        print(f"❌ Hiba: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = main()
