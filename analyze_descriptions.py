#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ingatlan leírások szövegelemzése - kulcsszavak és árbefolyásoló tényezők keresése
"""

import pandas as pd
import numpy as np
import re
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import seaborn as sns
import matplotlib.pyplot as plt

def clean_text(text):
    """Szöveg tisztítása és normalizálása"""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    # HTML tag-ek eltávolítása
    text = re.sub(r'<[^>]+>', ' ', text)
    # Speciális karakterek normalizálása
    text = re.sub(r'[^\w\s]', ' ', text)
    # Többszörös szóközök eltávolítása
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_keywords(descriptions, prices, min_freq=3):
    """Kulcsszavak kinyerése és árkorrelációs elemzés"""
    
    # Szövegek tisztítása
    clean_descriptions = [clean_text(desc) for desc in descriptions]
    
    # Stop words (gyakori, de nem informatív szavak)
    stop_words = {
        'a', 'az', 'és', 'vagy', 'de', 'hogy', 'van', 'volt', 'lesz', 'is', 'el', 'fel',
        'meg', 'ki', 'be', 'le', 'át', 'össz', 'szét', 'rá', 'ide', 'oda', 'minden',
        'egyik', 'másik', 'több', 'kevés', 'sok', 'nagy', 'kicsi', 'új', 'régi',
        'jó', 'rossz', 'szép', 'csúnya', 'igen', 'nem', 'csak', 'már', 'még', 'itt',
        'ott', 'ahol', 'amikor', 'hogyan', 'miért', 'mit', 'ki', 'kik', 'hol', 'mikor',
        'ingatlan', 'ház', 'lakás', 'eladó', 'kiadó', 'budapest', 'pest', 'megye',
        'utca', 'út', 'tér', 'körút', 'sétány', 'köz', 'sor', 'telep', 'kerület',
        'érd', 'erdliget', 'liget', 'diósd', 'érdliget'
    }
    
    # TF-IDF vektorizáció
    vectorizer = TfidfVectorizer(
        max_features=1000,
        min_df=min_freq,
        max_df=0.8,
        stop_words=list(stop_words),
        ngram_range=(1, 2)  # 1-2 szavas kifejezések
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(clean_descriptions)
        feature_names = vectorizer.get_feature_names_out()
        
        # Kulcsszavak és árak közötti korreláció
        correlations = []
        
        for i, keyword in enumerate(feature_names):
            keyword_scores = tfidf_matrix[:, i].toarray().flatten()
            
            if len(set(keyword_scores)) > 1:  # Ha van variancia
                correlation = np.corrcoef(keyword_scores, prices)[0, 1]
                if not np.isnan(correlation):
                    correlations.append((keyword, correlation, np.mean(keyword_scores)))
        
        # Korreláció szerint rendezés
        correlations.sort(key=lambda x: abs(x[1]), reverse=True)
        
        return correlations[:50], feature_names, tfidf_matrix
    
    except Exception as e:
        print(f"Hiba a TF-IDF során: {e}")
        return [], [], None

def analyze_price_keywords(df):
    """Árbefolyásoló kulcsszavak elemzése"""
    
    # Csak az árazott ingatlanokat vizsgáljuk
    df_priced = df[df['teljes_ar'].notna() & df['leiras'].notna()].copy()
    
    if len(df_priced) == 0:
        print("❌ Nincsenek árazott ingatlanok leírással!")
        return None
    
    print(f"📊 Elemzendő ingatlanok: {len(df_priced)} db")
    
    # Ár konvertálása millió forintra
    def convert_price(price_str):
        if pd.isna(price_str):
            return np.nan
        price_str = str(price_str).replace(' ', '').replace(',', '.')
        if 'M' in price_str or 'millió' in price_str.lower():
            return float(re.findall(r'[\d.]+', price_str)[0])
        elif 'E' in price_str or 'ezer' in price_str.lower():
            return float(re.findall(r'[\d.]+', price_str)[0]) / 1000
        else:
            # Próbálunk számot találni
            numbers = re.findall(r'[\d.]+', price_str)
            if numbers:
                price = float(numbers[0])
                if price > 1000:  # Valószínűleg ezer forintban
                    return price / 1000000
                else:
                    return price
        return np.nan
    
    df_priced['price_mft'] = df_priced['teljes_ar'].apply(convert_price)
    df_priced = df_priced[df_priced['price_mft'].notna()]
    
    print(f"✅ Sikeres árkonverzió: {len(df_priced)} db")
    print(f"💰 Ár tartomány: {df_priced['price_mft'].min():.1f} - {df_priced['price_mft'].max():.1f} M Ft")
    print(f"📊 Átlagár: {df_priced['price_mft'].mean():.1f} M Ft")
    
    # Kulcsszavak kinyerése
    descriptions = df_priced['leiras'].tolist()
    prices = df_priced['price_mft'].tolist()
    
    correlations, feature_names, tfidf_matrix = extract_keywords(descriptions, prices)
    
    if not correlations:
        print("❌ Nem találtunk jelentős kulcsszavakat!")
        return None
    
    # Eredmények megjelenítése
    print(f"\n🔍 TOP ÁRBEFOLYÁSOLÓ KULCSSZAVAK:")
    print("=" * 60)
    print(f"{'Kulcsszó':<25} {'Korreláció':<12} {'Átlag TF-IDF':<12} {'Hatás':<10}")
    print("-" * 60)
    
    positive_keywords = []
    negative_keywords = []
    
    for keyword, correlation, avg_score in correlations[:20]:
        effect = "📈 Pozitív" if correlation > 0 else "📉 Negatív"
        print(f"{keyword:<25} {correlation:>10.3f} {avg_score:>10.4f} {effect}")
        
        if correlation > 0.1:
            positive_keywords.append((keyword, correlation))
        elif correlation < -0.1:
            negative_keywords.append((keyword, correlation))
    
    # Kategorizálás
    print(f"\n🏆 LEGERŐSEBB POZITÍV HATÁSÚ KULCSSZAVAK:")
    for keyword, corr in positive_keywords[:10]:
        print(f"  ✅ {keyword}: {corr:.3f}")
    
    print(f"\n📉 LEGERŐSEBB NEGATÍV HATÁSÚ KULCSSZAVAK:")
    for keyword, corr in negative_keywords[:10]:
        print(f"  ❌ {keyword}: {corr:.3f}")
    
    return {
        'df_analyzed': df_priced,
        'correlations': correlations,
        'positive_keywords': positive_keywords,
        'negative_keywords': negative_keywords,
        'tfidf_matrix': tfidf_matrix,
        'feature_names': feature_names
    }

def create_text_features(results):
    """Szövegalapú feature-k létrehozása a modellhez"""
    
    if not results:
        return None
    
    df = results['df_analyzed']
    tfidf_matrix = results['tfidf_matrix']
    feature_names = results['feature_names']
    correlations = results['correlations']
    
    # Top kulcsszavak kiválasztása
    top_keywords = [corr[0] for corr in correlations[:20] if abs(corr[1]) > 0.05]
    
    print(f"\n🔧 SZÖVEGALAPÚ FEATURE-K LÉTREHOZÁSA:")
    print(f"📝 Kiválasztott kulcsszavak száma: {len(top_keywords)}")
    
    # Feature mátrix létrehozása a top kulcsszavakból
    keyword_indices = [i for i, name in enumerate(feature_names) if name in top_keywords]
    text_features = tfidf_matrix[:, keyword_indices].toarray()
    
    # Feature nevek
    text_feature_names = [f"text_{feature_names[i]}" for i in keyword_indices]
    
    print(f"✅ Feature mátrix méret: {text_features.shape}")
    
    # Egyszerű lineáris modell a szövegfeature-kkel
    X = text_features
    y = df['price_mft'].values
    
    if len(X) > 10:  # Ha van elég adat
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        
        print(f"\n📊 SZÖVEGMODELL TELJESÍTMÉNY:")
        print(f"  R² Score: {r2:.3f}")
        print(f"  MAE: {mae:.1f} M Ft")
        
        # Feature fontosságok
        feature_importance = list(zip(text_feature_names, model.coef_))
        feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)
        
        print(f"\n🎯 TOP FEATURE FONTOSSÁGOK:")
        for name, coef in feature_importance[:10]:
            effect = "📈" if coef > 0 else "📉"
            print(f"  {effect} {name.replace('text_', '')}: {coef:+.2f} M Ft")
        
        results['text_model'] = {
            'model': model,
            'feature_names': text_feature_names,
            'r2_score': r2,
            'mae': mae,
            'feature_importance': feature_importance
        }
    
    return results

def main():
    """Fő elemzési folyamat"""
    print("🏠 INGATLAN LEÍRÁSOK SZÖVEGELEMZÉSE")
    print("=" * 50)
    
    # Adatok betöltése
    try:
        df = pd.read_csv('ingatlan_reszletes_elado_haz_erd_erdliget_20250820_014506.csv')
        print(f"📊 Betöltött rekordok: {len(df)}")
        print(f"📝 Leírással rendelkezők: {df['leiras'].notna().sum()}")
        
        # Elemzés futtatása
        results = analyze_price_keywords(df)
        
        if results:
            # Szövegalapú feature-k létrehozása
            results = create_text_features(results)
            
            print(f"\n✅ ELEMZÉS BEFEJEZVE!")
            print(f"💾 Eredmények elmentve a results objektumba")
            
            return results
        else:
            print("❌ Az elemzés nem sikerült!")
            return None
            
    except Exception as e:
        print(f"❌ Hiba történt: {e}")
        return None

if __name__ == "__main__":
    results = main()
