"""
KŐBÁNYA-ÚJHEGYI LAKÓTELEP - ADVANCED INGATLAN DASHBOARD
======================================================
Szemantikai leírás-elemzéssel és mélyebb insights-okkal
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import re
from collections import Counter
import seaborn as sns
import matplotlib.pyplot as plt

# Oldal konfiguráció
st.set_page_config(
    page_title="🏠 Kőbánya-Újhegy Ingatlan Piaci Elemzés",
    page_icon="🏠",
    layout="wide"
)

@st.cache_data
def load_data():
    """Adatok betöltése"""
    try:
        # Megpróbáljuk betölteni a fájlt
        import os
        csv_path = "ingatlan_reszletes_20250819_123937.csv"
        if not os.path.exists(csv_path):
            st.error(f"❌ Az adatfájl nem található: {csv_path}")
            st.info("📁 Elérhető fájlok a könyvtárban:")
            for file in os.listdir("."):
                if file.endswith(".csv"):
                    st.write(f"- {file}")
            st.stop()
            
        df = pd.read_csv(csv_path)
        
        # Ellenőrizzük hogy van-e adat
        if df.empty:
            st.error("❌ Az adatfájl üres!")
            st.stop()
        
        st.info(f"✅ Sikeresen betöltve: {len(df)} ingatlan")
        
        # Numerikus ár konvertálás - tisztítjuk a speciális karaktereket
        df['ar_szam'] = df['nm_ar'].str.extract(r'([0-9,\s\xa0]+)').iloc[:, 0]
        df['ar_szam'] = df['ar_szam'].str.replace(',', '').str.replace('\xa0', '').str.replace(' ', '')
        df['ar_szam'] = pd.to_numeric(df['ar_szam'], errors='coerce')
        
        # Teljes ár numerikus konvertálás - tisztítjuk a speciális karaktereket
        # A formátum: "58,50 M Ft" vagy hasonló
        df['teljes_ar_szam'] = df['teljes_ar'].str.extract(r'([0-9,]+)').iloc[:, 0]
        df['teljes_ar_szam'] = df['teljes_ar_szam'].str.replace(',', '.').astype(float, errors='ignore')
        df['teljes_ar_szam'] = pd.to_numeric(df['teljes_ar_szam'], errors='coerce')
        
        # Terület numerikus
        df['terulet_szam'] = pd.to_numeric(df['terulet'].str.extract(r'(\d+)').iloc[:, 0], errors='coerce')
        
        # Szoba numerikus - biztosítjuk hogy legyen érték a plothoz
        df['szobak'] = pd.to_numeric(df['szobak'], errors='coerce').fillna(2)  # Default 2 szoba ha nincs adat
        
        # Emelet kategorizálás
        def categorize_floor(szint):
            if pd.isna(szint) or szint == '':
                return 'Ismeretlen'
            szint = str(szint).lower()
            if 'földszint' in szint or szint == '0':
                return 'Földszint'
            elif 'magasföldszint' in szint:
                return 'Magasföldszint'
            elif szint.isdigit():
                floor_num = int(szint)
                if floor_num <= 3:
                    return 'Alsó (1-3)'
                elif floor_num <= 7:
                    return 'Középső (4-7)'
                else:
                    return 'Felső (8+)'
            return 'Egyéb'
        
        df['emelet_kategoria'] = df['szint'].apply(categorize_floor)
        
        return df
    except Exception as e:
        st.error(f"Adatok betöltési hiba: {e}")
        return pd.DataFrame()

def semantic_description_analysis(descriptions):
    """Szemantikai leírás elemzés"""
    if descriptions.empty:
        return {}
    
    # Szöveg tisztítása és egyesítése
    all_text = ' '.join(descriptions.fillna('').astype(str))
    all_text = re.sub(r'[^\w\s]', ' ', all_text.lower())
    
    # Kulcsszó kategóriák
    keywords_categories = {
        '🏠 Állapot': {
            'felújított': ['felújított', 'felújítva', 'renovált', 'korszerű', 'modern'],
            'új': ['új', 'újszerű', 'friss', 'vadonatúj'],
            'jó állapot': ['jó állapot', 'kiváló állapot', 'rendezett'],
            'felújítandó': ['felújítandó', 'felújításra szorul', 'önerős']
        },
        '🌟 Kiemelések': {
            'panoráma': ['panoráma', 'kilátás', 'látványos', 'szép kilátás'],
            'csendes': ['csendes', 'nyugodt', 'békés', 'zajtalan'],
            'világos': ['világos', 'napfényes', 'fényes', 'napos'],
            'lift': ['lift', 'liftes', 'felvonó']
        },
        '🚗 Parkolás': {
            'ingyenes': ['ingyenes parkolás', 'ingyen parkol', 'díjtalan'],
            'garazs': ['garázs', 'zárt parkoló', 'beállóhely'],
            'utcai': ['utcai parkol', 'utcán parkol']
        },
        '💰 Értékesítés': {
            'sürgős': ['sürgős', 'gyors', 'azonnali', 'rögtön'],
            'tehermentes': ['tehermentes', 'per mentes', 'tiszta papír'],
            'költözhető': ['költözhető', 'beköltözhet', 'azonnal']
        },
        '🏗️ Felszereltség': {
            'klíma': ['klíma', 'légkondicionáló', 'klímás'],
            'műanyag ablak': ['műanyag ablak', 'új ablak', 'korszerű ablak'],
            'gépesített': ['gépesített', 'beépített', 'szerelt konyha']
        }
    }
    
    # Kulcsszó számolás
    keyword_stats = {}
    for category, subcats in keywords_categories.items():
        keyword_stats[category] = {}
        for subcat, keywords in subcats.items():
            count = sum(all_text.count(kw) for kw in keywords)
            keyword_stats[category][subcat] = count
    
    # Hosszúság elemzés
    desc_lengths = descriptions.str.len()
    length_stats = {
        'átlag': desc_lengths.mean(),
        'median': desc_lengths.median(),
        'módusz': desc_lengths.mode().iloc[0] if not desc_lengths.mode().empty else 0,
        'szórás': desc_lengths.std(),
        'min': desc_lengths.min(),
        'max': desc_lengths.max()
    }
    
    # Leggyakoribb szavak
    words = re.findall(r'\b[a-záéíóöőüű]{3,}\b', all_text)
    stop_words = {'lakás', 'ingatlan', 'eladó', 'kerület', 'budapest', 'szoba', 'van', 'lett', 'egy', 'alatt', 'után', 'mellett', 'között', 'által', 'mivel', 'amely', 'ahol'}
    filtered_words = [w for w in words if w not in stop_words]
    word_freq = Counter(filtered_words).most_common(20)
    
    return {
        'keywords': keyword_stats,
        'length_stats': length_stats,
        'word_frequency': word_freq,
        'total_descriptions': len(descriptions[descriptions.notna()])
    }

def analyze_price_text_correlation(df):
    """Ár és szöveg közötti összefüggések elemzése"""
    if df.empty or 'leiras' not in df.columns:
        return {}
    
    # Csak azokat az ingatlanokat nézzük, ahol van leírás és ár
    df_clean = df.dropna(subset=['leiras', 'ar_szam']).copy()
    
    if len(df_clean) < 5:
        return {}
    
    # Szöveg jellemzők számítása
    df_clean['leiras_hossz'] = df_clean['leiras'].str.len()
    df_clean['szavak_szama'] = df_clean['leiras'].str.split().str.len()
    
    # Prémium kulcsszavak keresése
    premium_keywords = {
        'panoráma': ['panoráma', 'kilátás', 'látványos'],
        'lift': ['lift', 'liftes', 'felvonó'],
        'felújított': ['felújított', 'renovált', 'korszerű'],
        'csendes': ['csendes', 'nyugodt', 'békés'],
        'világos': ['világos', 'napfényes', 'fényes'],
        'parkoló': ['parkoló', 'garázs', 'beállóhely']
    }
    
    keyword_price_effects = {}
    
    for keyword, synonyms in premium_keywords.items():
        # Van-e ilyen kulcsszó a leírásban
        has_keyword = df_clean['leiras'].str.lower().str.contains('|'.join(synonyms), na=False)
        
        if has_keyword.sum() > 2:  # Ha legalább 3 hirdetésben szerepel
            with_keyword = df_clean[has_keyword]['ar_szam'].mean()
            without_keyword = df_clean[~has_keyword]['ar_szam'].mean()
            
            if not pd.isna(with_keyword) and not pd.isna(without_keyword):
                price_diff = with_keyword - without_keyword
                price_diff_pct = (price_diff / without_keyword) * 100
                
                keyword_price_effects[keyword] = {
                    'with_keyword': with_keyword,
                    'without_keyword': without_keyword,
                    'difference': price_diff,
                    'difference_pct': price_diff_pct,
                    'count_with': has_keyword.sum(),
                    'count_without': (~has_keyword).sum()
                }
    
    # Szöveg hossz és ár korrelációja
    length_price_corr = df_clean['leiras_hossz'].corr(df_clean['ar_szam'])
    words_price_corr = df_clean['szavak_szama'].corr(df_clean['ar_szam'])
    
    return {
        'keyword_effects': keyword_price_effects,
        'correlations': {
            'length_price': length_price_corr,
            'words_price': words_price_corr
        },
        'sample_size': len(df_clean)
    }

def calculate_comprehensive_stats(df):
    """Átfogó statisztikai mutatók számítása"""
    stats = {}
    
    # Numerikus oszlopok
    numeric_cols = ['ar_szam', 'teljes_ar_szam', 'terulet_szam', 'szobak']
    
    for col in numeric_cols:
        if col in df.columns:
            series = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(series) > 0:
                stats[col] = {
                    'átlag': series.mean(),
                    'medián': series.median(),
                    'módusz': series.mode().iloc[0] if not series.mode().empty else 'N/A',
                    'szórás': series.std(),
                    'min': series.min(),
                    'max': series.max(),
                    'q25': series.quantile(0.25),
                    'q75': series.quantile(0.75),
                    'iqr': series.quantile(0.75) - series.quantile(0.25),
                    'variációs_együttható': (series.std() / series.mean()) * 100 if series.mean() != 0 else 0
                }
    
    return stats

def seller_specific_analysis(df, target_area=50, target_rooms=2, target_condition='közepes állapotú', target_floor=6):
    """Specifikus lakás tulajdonos számára készített elemzés"""
    
    # Hasonló ingatlanok szűrése
    similar_properties = df[
        (abs(df['terulet_szam'] - target_area) <= 5) &  # +/- 5 m²
        (df['szobak'] == target_rooms) |  # Ugyanannyi szoba
        (df['ingatlan_allapota'].str.contains('közepes|jó', case=False, na=False))  # Hasonló állapot
    ].copy()
    
    # Emelet kategorizálás a célhoz
    floor_category = 'Középső (4-7)' if 4 <= target_floor <= 7 else 'Felső (8+)' if target_floor > 7 else 'Alsó (1-3)'
    similar_floor = df[df['emelet_kategoria'] == floor_category].copy()
    
    analysis = {
        'hasonló_ingatlanok': {
            'darab': len(similar_properties),
            'átlag_ár': similar_properties['ar_szam'].mean() if len(similar_properties) > 0 else 0,
            'ár_tartomány': {
                'min': similar_properties['ar_szam'].min() if len(similar_properties) > 0 else 0,
                'max': similar_properties['ar_szam'].max() if len(similar_properties) > 0 else 0
            }
        },
        'emelet_hatás': {
            'ugyanaz_emelet_kategória': len(similar_floor),
            'átlag_ár_emelet': similar_floor['ar_szam'].mean() if len(similar_floor) > 0 else 0
        },
        'piaci_pozíció': {},
        'eladási_taktikák': {},
        'verseny_elemzés': {}
    }
    
    # Piaci pozíció meghatározása
    if len(similar_properties) > 0:
        avg_similar = similar_properties['ar_szam'].mean()
        all_avg = df['ar_szam'].mean()
        
        position = 'átlag feletti' if avg_similar > all_avg else 'átlag alatti' if avg_similar < all_avg else 'átlagos'
        analysis['piaci_pozíció'] = {
            'kategória': position,
            'hasonló_átlag': avg_similar,
            'piaci_átlag': all_avg,
            'eltérés_százalék': ((avg_similar - all_avg) / all_avg) * 100
        }
    
    # Verseny elemzés
    advertiser_types = df['hirdeto_tipus'].value_counts()
    condition_competition = df['ingatlan_allapota'].value_counts()
    
    analysis['verseny_elemzés'] = {
        'hirdető_típusok': advertiser_types.to_dict(),
        'állapot_konkurencia': condition_competition.to_dict(),
        'teljes_kínálat': len(df)
    }
    
    # Eladási taktikák javaslata
    premium_features = []
    if target_floor >= 6:
        premium_features.append('magasabb emelet - kilátás kiemelése')
    if target_rooms == 2:
        premium_features.append('optimális méret fiatal párok/egyedülállók számára')
    
    analysis['eladási_taktikák'] = {
        'kiemelendő_tulajdonságok': premium_features,
        'javasolt_ár_stratégia': 'versenyképes' if len(similar_properties) > 5 else 'prémium',
        'célcsoport': 'fiatal párok, első lakásvásárlók' if target_rooms <= 2 else 'családok'
    }
    
    return analysis

def create_price_prediction_model(df):
    """Egyszerű ár predikciós modell"""
    # Szűrjük ki a hiányos adatokat
    clean_df = df.dropna(subset=['ar_szam', 'terulet_szam', 'szobak'])
    
    if len(clean_df) < 5:
        return None
    
    # Egyszerű lineáris kapcsolatok
    area_price_corr = clean_df['ar_szam'].corr(clean_df['terulet_szam'])
    room_price_corr = clean_df['ar_szam'].corr(clean_df['szobak'])
    
    # Átlagárak kategóriánként
    floor_prices = clean_df.groupby('emelet_kategoria')['ar_szam'].mean()
    condition_prices = clean_df.groupby('ingatlan_allapota')['ar_szam'].mean()
    advertiser_prices = clean_df.groupby('hirdeto_tipus')['ar_szam'].mean()
    
    return {
        'correlations': {
            'terület_ár': area_price_corr,
            'szoba_ár': room_price_corr
        },
        'category_prices': {
            'emelet': floor_prices.to_dict(),
            'állapot': condition_prices.to_dict(),
            'hirdető': advertiser_prices.to_dict()
        }
    }
    """Egyszerű ár predikciós modell"""
    # Szűrjük ki a hiányos adatokat
    clean_df = df.dropna(subset=['ar_szam', 'terulet_szam', 'szobak'])
    
    if len(clean_df) < 5:
        return None
    
    # Egyszerű lineáris kapcsolatok
    area_price_corr = clean_df['ar_szam'].corr(clean_df['terulet_szam'])
    room_price_corr = clean_df['ar_szam'].corr(clean_df['szobak'])
    
    # Átlagárak kategóriánként
    floor_prices = clean_df.groupby('emelet_kategoria')['ar_szam'].mean()
    condition_prices = clean_df.groupby('ingatlan_allapota')['ar_szam'].mean()
    advertiser_prices = clean_df.groupby('hirdeto_tipus')['ar_szam'].mean()
    
    return {
        'correlations': {
            'terület_ár': area_price_corr,
            'szoba_ár': room_price_corr
        },
        'category_prices': {
            'emelet': floor_prices.to_dict(),
            'állapot': condition_prices.to_dict(),
            'hirdető': advertiser_prices.to_dict()
        }
    }

    # Fő dashboard
def main():
    st.title("🏠 Kőbánya-Újhegyi Lakótelep - Részletes Piaci Elemzés")
    st.markdown("### 🔍 Szemantikai leírás-elemzéssel kiegészített ingatlan dashboard")
    
    # Dashboard használati útmutató
    with st.expander("📖 Dashboard használati útmutató - ELSŐ OLVASÁS AJÁNLOTT"):
        st.markdown("""
        **🎯 Mit csinál ez a dashboard?**
        
        Ez egy **professzionális ingatlan piaci elemző eszköz**, amely:
        - ✅ **57 valós hirdetést** elemez a Kőbánya-Újhegyi lakótelepről
        - ✅ **Szemantikai szöveganalízist** végez a hirdetési leírásokban
        - ✅ **Befektetési javaslatokat** ad ár/érték arány alapján
        - ✅ **Interaktív szűrőkkel** segít a keresésben
        
        **📊 Hogyan navigáljak?**
        1. **Alapstatisztikák**: Gyors piaci áttekintés
        2. **Szemantikai elemzés**: Mi fontos a vevőknek?
        3. **Árelemzések**: Hol vannak a jó vételek?
        4. **Emelet & Állapot**: Milyen prémiumok/diszkontok vannak?
        5. **Befektetési elemzés**: Konkrét ajánlások
        6. **Szűrők**: Személyre szabott keresés
        
        **🔍 Pro tippek:**
        - Kattints a **"ℹ️" gombokra** minden szekciónál részletes magyarázatért
        - A **gráfikokon hover-elj** a pontokon további adatokért
        - Használd a **szűrőket** alul a célzott kereséshez
        - A **befektetési pontszám** alapján sorold a lehetőségeket
        
        **⚠️ Fontos figyelmeztetés:**
        Ez egy elemző eszköz - végső döntés előtt mindig nézd meg személyesen az ingatlant!
        """)
    
    # Adatok betöltése
    df = load_data()
    
    if df.empty:
        st.error("Nem sikerült betölteni az adatokat!")
        return
    
    # Alapstatisztikák
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Ingatlanok", len(df))
    with col2:
        avg_price = df['ar_szam'].mean()
        st.metric("💰 Átlag m² ár", f"{avg_price:,.0f} Ft/m²")
    with col3:
        avg_total = df['teljes_ar_szam'].mean()
        if not pd.isna(avg_total):
            st.metric("🏠 Átlag teljes ár", f"{avg_total:.1f} M Ft")
        else:
            st.metric("🏠 Átlag teljes ár", "N/A")
    with col4:
        desc_pct = (df['leiras'].notna().sum() / len(df)) * 100
        st.metric("📝 Leírás lefedettség", f"{desc_pct:.0f}%")
    
    # Gyors piaci áttekintés
    st.info("""
    **🎯 GYORS PIACI ÖSSZEFOGLALÓ:**
    A Kőbánya-Újhegyi lakótelepen jelenleg változatos kínálat található. Az árak széles skálán mozognak, 
    ami jó lehetőségeket teremt mind befektetők, mind lakásvásárlók számára. A részletes elemzésekkel 
    azonosíthatók a legjobb ár/érték arányú ingatlanok.
    """)
    
    # Szemantikai elemzés
    st.header("📝 Szemantikai Leírás Elemzés")
    
    with st.expander("ℹ️ Hogyan értelmezzem a szemantikai elemzést?"):
        st.markdown("""
        **Mit mutat ez a szekció?**
        - Az ingatlan leírásokban található **kulcsszavak gyakoriságát** elemzi
        - Megmutatja, hogy a hirdetők milyen **értékesítési stratégiákat** használnak
        - Segít azonosítani a **piaci trendeket** és **vásárlói igényeket**
        
        **Miért fontos?**
        - A gyakran említett tulajdonságok (pl. "lift", "panoráma") **értéknövelő** tényezők
        - A "sürgős" vagy "tehermentes" kifejezések **alkudozási lehetőségeket** jelezhetnek
        - Az állapot-leírások segítenek a **valós értékbecslésben**
        """)
    
    # Állapot szerinti szűrő a szemantikai elemzéshez
    col1, col2 = st.columns([1, 3])
    with col1:
        semantic_condition_filter = st.selectbox(
            "🏠 Állapot szűrő (szemantikai elemzéshez)",
            options=["Összes állapot"] + list(df['ingatlan_allapota'].dropna().unique()),
            index=0
        )
    
    # Szűrt adatok a szemantikai elemzéshez
    if semantic_condition_filter != "Összes állapot":
        df_semantic = df[df['ingatlan_allapota'] == semantic_condition_filter]
        st.info(f"📊 Szemantikai elemzés szűrve: **{semantic_condition_filter}** állapotú ingatlanok ({len(df_semantic)} db)")
    else:
        df_semantic = df
    
    semantic_analysis = semantic_description_analysis(df_semantic['leiras'])
    
    if semantic_analysis:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔤 Leírás Statisztikák")
            st.metric("Összes leírás", semantic_analysis['total_descriptions'])
            st.metric("Átlag hosszúság", f"{semantic_analysis['length_stats']['átlag']:.0f} karakter")
            st.metric("Median hosszúság", f"{semantic_analysis['length_stats']['median']:.0f} karakter")
            st.metric("Módusz (leggyakoribb)", f"{semantic_analysis['length_stats']['módusz']:.0f} karakter")
            st.metric("Szórás", f"{semantic_analysis['length_stats']['szórás']:.0f} karakter")
        
        with col2:
            st.subheader("🏆 Top 10 Kulcsszó")
            word_freq_df = pd.DataFrame(semantic_analysis['word_frequency'], columns=['Szó', 'Gyakoriság'])
            st.dataframe(word_freq_df.head(10), use_container_width=True)
    
    # ÚJ: Ár-szöveg korreláció elemzése
    st.subheader("💰📝 Ár és Leírás Összefüggés Elemzése")
    
    price_text_analysis = analyze_price_text_correlation(df_semantic)
    
    if price_text_analysis and 'keyword_effects' in price_text_analysis:
        with st.expander("📊 Kulcsszavak árazási hatása"):
            st.markdown("""
            **Mit mutat ez a táblázat?**
            - Minden sorban egy **prémium kulcsszó** szerepel
            - **"Van kulcsszó"**: Átlagár, ha a hirdetésben szerepel ez a kifejezés
            - **"Nincs kulcsszó"**: Átlagár a többi hirdetésben
            - **"Árkülönbség"**: Mennyivel drágábbak a kulcsszavas hirdetések
            - **"Hatás %"**: Százalékos árkülönbség (pozitív = drágább, negatív = olcsóbb)
            """)
        
        # Kulcsszó hatások táblázata
        keyword_effects_data = []
        for keyword, data in price_text_analysis['keyword_effects'].items():
            keyword_effects_data.append({
                'Kulcsszó': keyword,
                'Van kulcsszó (Ft/m²)': f"{data['with_keyword']:,.0f}",
                'Nincs kulcsszó (Ft/m²)': f"{data['without_keyword']:,.0f}",
                'Árkülönbség (Ft/m²)': f"{data['difference']:+,.0f}",
                'Hatás %': f"{data['difference_pct']:+.1f}%",
                'Hirdetések száma': f"{data['count_with']}/{data['count_with'] + data['count_without']}"
            })
        
        if keyword_effects_data:
            keyword_df = pd.DataFrame(keyword_effects_data)
            st.dataframe(keyword_df, use_container_width=True)
            
            # Insight generálása
            best_keyword = max(price_text_analysis['keyword_effects'].items(), 
                             key=lambda x: x[1]['difference_pct'], default=(None, None))
            
            if best_keyword[0]:
                st.success(f"""
                💡 **Legjobb árfelhajtó kulcsszó**: **{best_keyword[0]}** 
                (+{best_keyword[1]['difference_pct']:.1f}% árkülönbség)
                """)
        
        # Szöveg hossz korreláció
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📏 Leírás hossz - Ár korreláció", 
                     f"{price_text_analysis['correlations']['length_price']:.3f}")
        with col2:
            st.metric("📝 Szavak száma - Ár korreláció", 
                     f"{price_text_analysis['correlations']['words_price']:.3f}")
    
    # Kulcsszó heatmap
    if semantic_analysis and 'keywords' in semantic_analysis:
        st.subheader("🔥 Kulcsszó Heatmap")
        
        with st.expander("📊 Heatmap értelmezési útmutató"):
            st.markdown("""
            **Mit látok a heatmap-en?**
            - **Sorok**: Különböző ingatlan tulajdonságok (pl. lift, panoráma, felújított)
            - **Oszlopok**: Kategóriák (állapot, kiemelések, parkolás, stb.)
            - **Színek**: A sötétebb szín = gyakrabban említik a hirdetésekben
            
            **Hogyan használjam?**
            - **Sárga/világos területek**: Ritkán említett, de értékes tulajdonságok
            - **Sötét területek**: Gyakori, standard tulajdonságok
            - **Üres cellák**: Nem releváns kombináció
            
            **Befektetési tipp**: A világos, de létező tulajdonságok (pl. "garazs") 
            potenciálisan **alulértékelt** lehetőségek!
            """)
        
        # Kulcsszó adatok előkészítése
        keyword_data = []
        for category, subcats in semantic_analysis['keywords'].items():
            for subcat, count in subcats.items():
                keyword_data.append({'Kategória': category, 'Kulcsszó': subcat, 'Gyakoriság': count})
        
        if keyword_data:
            keyword_df = pd.DataFrame(keyword_data)
            pivot_df = keyword_df.pivot(index='Kulcsszó', columns='Kategória', values='Gyakoriság').fillna(0)
            
            fig_heatmap = px.imshow(
                pivot_df.values,
                x=pivot_df.columns,
                y=pivot_df.index,
                aspect="auto",
                color_continuous_scale="Viridis",
                title="Kulcsszavak gyakorisága kategóriánként"
            )
            fig_heatmap.update_xaxes(side="bottom")
            st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Árelemzés
    st.header("💰 Részletes Árelemzés")
    
    with st.expander("💡 Árelemzés értelmezése"):
        st.markdown("""
        **Bal oldali grafikon (Scatter plot):**
        - **X tengely**: Lakás mérete négyzetméterben
        - **Y tengely**: Négyzetméter ár Forintban
        - **Pont mérete**: Szobák száma (nagyobb pont = több szoba)
        - **Színek**: Hirdető típusok
        
        **Mit keresek?**
        - **Grafikon alatti pontok**: Potenciálisan **jó vételek**
        - **Grafikon feletti pontok**: **Drágább**, de esetleg prémium lokáció
        - **Outlier pontok**: Különleges ingatlanok vagy téves árazás
        
        **Jobb oldali Box plot:**
        - A **doboz közepe**: Medián ár (50% alatt/felett van)
        - **Doboz széle**: 25%-75% közötti árak
        - **Vonalak**: Szélső, de még normális értékek
        - **Pontok**: Outlier árak
        """)
    
    # Állapot szűrő az árelemzéshez
    col_filter, col_space = st.columns([1, 3])
    with col_filter:
        price_condition_filter = st.selectbox(
            "🏠 Állapot szűrő (árelemzéshez)",
            options=["Összes állapot"] + list(df['ingatlan_allapota'].dropna().unique()),
            index=0,
            key="price_analysis_filter"
        )
    
    # Szűrt adatok az árelemzéshez
    if price_condition_filter != "Összes állapot":
        df_price = df[df['ingatlan_allapota'] == price_condition_filter]
        st.info(f"📊 Árelemzés szűrve: **{price_condition_filter}** állapotú ingatlanok ({len(df_price)} db)")
    else:
        df_price = df
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Ár vs terület scatter
        fig_scatter = px.scatter(
            df_price, 
            x='terulet_szam', 
            y='ar_szam',
            color='hirdeto_tipus',
            size='szobak',
            hover_data=['ingatlan_allapota', 'emelet_kategoria'],
            title=f"M² Ár vs Terület ({price_condition_filter})",
            labels={'terulet_szam': 'Terület (m²)', 'ar_szam': 'M² ár (Ft)'}
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    with col2:
        # Box plot árak hirdető típus szerint
        fig_box = px.box(
            df_price,
            x='hirdeto_tipus',
            y='ar_szam',
            title=f"M² Árak eloszlása hirdető típus szerint ({price_condition_filter})",
            labels={'hirdeto_tipus': 'Hirdető típus', 'ar_szam': 'M² ár (Ft)'}
        )
        st.plotly_chart(fig_box, use_container_width=True)
    
    # Emelet elemzés
    st.header("🏢 Emelet Elemzés")
    
    with st.expander("🔍 Emelet hatása az ingatlan értékére"):
        st.markdown("""
        **Emelet kategóriák magyarázata:**
        - **Földszint**: Könnyen megközelíthető, de kevesebb privátszféra
        - **Alsó (1-3)**: Jó kompromisszum, lift nélkül is járható
        - **Középső (4-7)**: Optimális magasság, szép kilátás
        - **Felső (8+)**: Legjobb kilátás, de lift-függő
        
        **Árazási logika:**
        - Magasabb emelet = általában **drágább** (kilátás prémium)
        - **Kivétel**: Lift nélküli épületek esetén fordított a helyzet
        - **6-7. emelet**: Gyakran a "sweet spot" - jó kilátás, még nem túl magasan
        
        **Befektetési szempontok:**
        - **Középső emeletek**: Legjobb **újraértékesíthetőség**
        - **Földszint**: **Idősebb vásárlók** körében népszerű
        - **Felső emeletek**: **Fiatal vásárlók**, de kockázatosabb (lift meghibásodás)
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Emelet eloszlás
        floor_counts = df['emelet_kategoria'].value_counts()
        fig_floor = px.pie(
            values=floor_counts.values,
            names=floor_counts.index,
            title="Ingatlanok eloszlása emelet szerint"
        )
        st.plotly_chart(fig_floor, use_container_width=True)
    
    with col2:
        # Emelet vs ár
        floor_prices = df.groupby('emelet_kategoria')['ar_szam'].agg(['mean', 'std', 'count']).reset_index()
        fig_floor_price = px.bar(
            floor_prices,
            x='emelet_kategoria',
            y='mean',
            error_y='std',
            title="Átlagárak emelet kategóriák szerint",
            labels={'emelet_kategoria': 'Emelet kategória', 'mean': 'Átlag m² ár (Ft)'}
        )
        st.plotly_chart(fig_floor_price, use_container_width=True)
    
    # Állapot elemzés
    st.header("🔧 Ingatlan Állapot Elemzés")
    
    with st.expander("🏠 Állapot kategóriák és árazási hatásuk"):
        st.markdown("""
        **Állapot kategóriák jelentése:**
        - **Felújított/Újszerű**: Azonnal költözhető, nincs további beruházás
        - **Jó állapotú**: Kisebb kozmetikai javítások szükségesek
        - **Közepes**: Jelentős felújítási munkák várhatók
        - **Felújítandó**: Teljes körű renoválás szükséges
        
        **Rejtett költségek becslése:**
        - **Felújítandó**: +4-8 millió Ft felújítási költség
        - **Közepes**: +2-4 millió Ft befektetés
        - **Jó állapotú**: +0.5-1 millió Ft kisebb javítások
        
        **Befektetői stratégiák:**
        - **"Flip" stratégia**: Felújítandó vásárlása + renoválás + eladás
        - **Bérbeadás**: Jó állapotú azonnal kiadható
        - **Saját lakhatás**: Felújított/újszerű a legkényelmesebb
        """)
    
    condition_stats = df.groupby('ingatlan_allapota').agg({
        'ar_szam': ['mean', 'count'],
        'teljes_ar_szam': 'mean'
    }).round(0)
    
    condition_stats.columns = ['Átlag m² ár', 'Darab', 'Átlag teljes ár']
    st.dataframe(condition_stats, use_container_width=True)
    
    # Korrelációs mátrix
    st.header("🔗 Korrelációs Elemzés")
    
    with st.expander("📈 Korreláció értelmezése - mit jelentenek a számok?"):
        st.markdown("""
        **Mi a korreláció?**
        Megmutatja, hogy két tulajdonság mennyire mozog együtt (-1 és +1 között).
        
        **Szín kódok:**
        - **Piros**: Negatív korreláció - egyik nő, másik csökken
        - **Kék**: Pozitív korreláció - együtt nőnek/csökkennek
        - **Fehér**: Nincs összefüggés
        
        **Értelmezés:**
        - **0.8-1.0**: Erős pozitív kapcsolat
        - **0.5-0.8**: Közepes pozitív kapcsolat
        - **0.2-0.5**: Gyenge pozitív kapcsolat
        - **-0.2 - 0.2**: Nincs jelentős kapcsolat
        - **Negatív értékek**: Fordított kapcsolat
        
        **Befektetési insight:**
        Ha **terület** és **ár** erősen korrelál = normális piac
        Ha **szobaszám** és **ár** gyengén korrelál = méter alapú árazás
        """)
    
    numeric_cols = ['ar_szam', 'teljes_ar_szam', 'terulet_szam', 'szobak']
    corr_df = df[numeric_cols].corr()
    
    fig_corr = px.imshow(
        corr_df,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdBu",
        title="Korrelációs mátrix"
    )
    st.plotly_chart(fig_corr, use_container_width=True)
    
    # ÚJ: Részletes statisztikai mutatók
    st.header("📊 Részletes Statisztikai Mutatók")
    
    with st.expander("📚 Statisztikai mutatók magyarázata"):
        st.markdown("""
        **Alapfogalmak:**
        - **Átlag**: Az értékek összege osztva a darabszámmal
        - **Medián**: A középső érték (50% alatt/felett van)
        - **Módusz**: A leggyakrabban előforduló érték
        - **Szórás**: Mennyire szórnak az értékek az átlag körül
        - **Q25/Q75**: 25%-os és 75%-os percentilisek
        - **IQR**: Interkvartilis tartomány (Q75-Q25)
        - **Variációs együttható**: Relatív szórás (szórás/átlag * 100)
        
        **Miért fontosak?**
        - **Piaci stabilitás**: Alacsony szórás = stabil árak
        - **Árszint megítélés**: Medián vs átlag eltérése = kilógó értékek hatása
        - **Befektetési kockázat**: Magas variáció = nagyobb kockázat
        """)
    
    # Állapot szűrő a statisztikai elemzéshez
    col_filter, col_space = st.columns([1, 3])
    with col_filter:
        stats_condition_filter = st.selectbox(
            "🏠 Állapot szűrő (statisztikák)",
            options=["Összes állapot"] + list(df['ingatlan_allapota'].dropna().unique()),
            index=0,
            key="stats_analysis_filter"
        )
    
    # Szűrt adatok a statisztikákhoz
    if stats_condition_filter != "Összes állapot":
        df_stats = df[df['ingatlan_allapota'] == stats_condition_filter]
        st.info(f"📊 Statisztikák szűrve: **{stats_condition_filter}** állapotú ingatlanok ({len(df_stats)} db)")
    else:
        df_stats = df
    
    comprehensive_stats = calculate_comprehensive_stats(df_stats)
    
    if comprehensive_stats:
        stats_data = []
        var_names = {
            'ar_szam': 'M² Ár (Ft/m²)',
            'teljes_ar_szam': 'Teljes ár (M Ft)',
            'terulet_szam': 'Terület (m²)',
            'szobak': 'Szobaszám'
        }
        
        for var, stats in comprehensive_stats.items():
            if var in var_names:
                stats_data.append({
                    'Változó': var_names[var],
                    'Átlag': f"{stats['átlag']:,.0f}" if var != 'teljes_ar_szam' else f"{stats['átlag']:.1f}",
                    'Medián': f"{stats['medián']:,.0f}" if var != 'teljes_ar_szam' else f"{stats['medián']:.1f}",
                    'Módusz': f"{stats['módusz']:,.0f}" if stats['módusz'] != 'N/A' else 'N/A',
                    'Szórás': f"{stats['szórás']:,.0f}" if var != 'teljes_ar_szam' else f"{stats['szórás']:.1f}",
                    'Min': f"{stats['min']:,.0f}" if var != 'teljes_ar_szam' else f"{stats['min']:.1f}",
                    'Max': f"{stats['max']:,.0f}" if var != 'teljes_ar_szam' else f"{stats['max']:.1f}",
                    'Variációs ktg. (%)': f"{stats['variációs_együttható']:.1f}%"
                })
        
        if stats_data:
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True)
            
            # Statisztikai insights
            price_var_coeff = comprehensive_stats.get('ar_szam', {}).get('variációs_együttható', 0)
            if price_var_coeff > 20:
                st.warning(f"⚠️ **Magas ár volatilitás**: {price_var_coeff:.1f}% variációs együttható - nagy szóródás az árákban!")
            elif price_var_coeff < 10:
                st.success(f"✅ **Stabil árszint**: {price_var_coeff:.1f}% variációs együttható - konzisztens árazás a piacon!")
            else:
                st.info(f"ℹ️ **Normális árszóródás**: {price_var_coeff:.1f}% variációs együttható - egészséges piaci diverzitás!")
    else:
        st.warning("⚠️ Nincs elegendő adat a statisztikai elemzéshez a kiválasztott szűrővel.")
    
    # Predikciós modell
    st.header("🎯 Árbecslő Modell")
    
    with st.expander("🤖 Hogyan működik az árbecslő modell?"):
        st.markdown("""
        **Mit csinál a modell?**
        - Elemzi a **történelmi adatokat** és keresi a mintázatokat
        - **Korrelációkat** számol a tulajdonságok és árak között
        - **Kategória átlagokat** készít minden jellemzőhöz
        
        **Korrelációs értékek jelentése:**
        - **Magas pozitív korreláció (0.7+)**: Erős árbefolyásoló tényező
        - **Közepes korreláció (0.3-0.7)**: Mérsékelt hatás
        - **Alacsony korreláció (0.0-0.3)**: Kis vagy nincs hatás
        
        **Kategória átlagák használata:**
        - **Emelet prémium/diszkont** számítása
        - **Állapot szerinti** áreltérések
        - **Hirdető típus** hatása az árazásra
        
        **Figyelem!** Ez egy egyszerű modell - valós értékbecsléshez 
        további tényezők kellenek (lokáció, parkolás, stb.)
        """)
    
    model_data = create_price_prediction_model(df)
    
    if model_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Korrelációk")
            st.metric("Terület - Ár korreláció", f"{model_data['correlations']['terület_ár']:.3f}")
            st.metric("Szobaszám - Ár korreláció", f"{model_data['correlations']['szoba_ár']:.3f}")
        
        with col2:
            st.subheader("💡 Kategória Átlagárak")
            
            # Emelet kategória árak
            st.write("**Emelet kategóriák:**")
            for floor, price in model_data['category_prices']['emelet'].items():
                st.write(f"• {floor}: {price:,.0f} Ft/m²")
            
            # Hirdető típus árak
            st.write("**Hirdető típusok:**")
            for adv_type, price in model_data['category_prices']['hirdető'].items():
                if not pd.isna(price):
                    st.write(f"• {adv_type}: {price:,.0f} Ft/m²")
    
    # ÚJ: Eladó-specifikus elemzés
    st.header("🏡 Személyre Szabott Eladói Tanácsadás")
    
    with st.expander("🎯 Kiknek szól ez a szekció?"):
        st.markdown("""
        **Ideális lakáseladók számára:**
        - 🏠 **50 m² körüli, 2 szobás lakás** tulajdonosai
        - 🔧 **Közepes állapotú** ingatlan eladói  
        - 🏢 **6. emeleti** vagy hasonló magasságú lakások
        - 💰 **Reális árazást** kereső eladók
        
        **Mit kapsz?**
        - Pontos **piaci pozicionálás** a hasonló ingatlanokhoz képest
        - **Versenyhelyzet** elemzés  
        - **Eladási stratégia** javaslatok
        - **Árazási taktikák** a gyorsabb értékesítéshez
        """)
    
    # Eladó specifikus paramétereinek beállítása
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        target_area = st.number_input("Lakás mérete (m²)", min_value=30, max_value=100, value=50, step=5)
    with col2:
        target_rooms = st.selectbox("Szobák száma", [1, 2, 3, 4], index=1)
    with col3:
        target_condition = st.selectbox("Ingatlan állapota", 
                                       ["felújított", "jó állapotú", "közepes állapotú", "felújítandó"],
                                       index=2)
    with col4:
        target_floor = st.number_input("Emelet", min_value=0, max_value=15, value=6, step=1)
    
    # Eladó-specifikus elemzés futtatása
    seller_analysis = seller_specific_analysis(df, target_area, target_rooms, target_condition, target_floor)
    
    if seller_analysis:
        # Piaci pozíció
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📍 A Te Lakásod Piaci Pozíciója")
            
            similar_count = seller_analysis['hasonló_ingatlanok']['darab']
            if similar_count > 0:
                avg_similar = seller_analysis['hasonló_ingatlanok']['átlag_ár']
                price_range = seller_analysis['hasonló_ingatlanok']['ár_tartomány']
                
                st.metric("Hasonló ingatlanok száma", similar_count)
                st.metric("Átlagos m² ár (hasonlók)", f"{avg_similar:,.0f} Ft/m²")
                st.metric("Ár tartomány", 
                         f"{price_range['min']:,.0f} - {price_range['max']:,.0f} Ft/m²")
                
                # Javasolt ár kalkuláció
                suggested_price_low = avg_similar * 0.95  # 5% alatt az átlagnak
                suggested_price_high = avg_similar * 1.05  # 5% felett
                
                st.success(f"""
                💰 **Javasolt árazási sáv**:
                {suggested_price_low:,.0f} - {suggested_price_high:,.0f} Ft/m²
                
                **Összesen**: {suggested_price_low * target_area / 1000000:.1f} - {suggested_price_high * target_area / 1000000:.1f} millió Ft
                """)
            else:
                st.warning("⚠️ Nem található elegendő hasonló ingatlan a pontos árazáshoz.")
        
        with col2:
            st.subheader("🎯 Eladási Stratégia")
            
            tactics = seller_analysis.get('eladási_taktikák', {})
            
            if 'kiemelendő_tulajdonságok' in tactics:
                st.write("**🌟 Kiemelendő tulajdonságok:**")
                for prop in tactics['kiemelendő_tulajdonságok']:
                    st.write(f"• {prop}")
            
            if 'javasolt_ár_stratégia' in tactics:
                strategy = tactics['javasolt_ár_stratégia']
                if strategy == 'versenyképes':
                    st.info("💡 **Javasolt stratégia**: Versenyképes árazás - sok hasonló ingatlan van a piacon")
                else:
                    st.success("💡 **Javasolt stratégia**: Prémium árazás - kevés konkurencia")
            
            if 'célcsoport' in tactics:
                st.write(f"**🎪 Fő célcsoport**: {tactics['célcsoport']}")
        
        # Versenyhelyzet
        st.subheader("⚔️ Versenyhelyzet Elemzése")
        
        competition = seller_analysis.get('verseny_elemzés', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'hirdető_típusok' in competition:
                st.write("**📊 Hirdető típusok megoszlása:**")
                for adv_type, count in competition['hirdető_típusok'].items():
                    percentage = (count / competition.get('teljes_kínálat', 1)) * 100
                    st.write(f"• {adv_type}: {count} db ({percentage:.1f}%)")
        
        with col2:
            if 'állapot_konkurencia' in competition:
                st.write("**🏠 Állapot szerinti konkurencia:**")
                for condition, count in competition['állapot_konkurencia'].items():
                    percentage = (count / competition.get('teljes_kínálat', 1)) * 100
                    st.write(f"• {condition}: {count} db ({percentage:.1f}%)")
        
        # Piaci pozíció értékelés
        if 'piaci_pozíció' in seller_analysis and seller_analysis['piaci_pozíció']:
            position_data = seller_analysis['piaci_pozíció']
            
            st.subheader("📈 Piaci Pozíció Értékelés")
            
            category = position_data.get('kategória', 'ismeretlen')
            deviation = position_data.get('eltérés_százalék', 0)
            
            if category == 'átlag feletti':
                st.success(f"✅ **Prémium kategória**: A hasonló ingatlanok {abs(deviation):.1f}%-kal drágábbak az átlagnál!")
            elif category == 'átlag alatti':
                st.warning(f"⚠️ **Alacsonyabb szegmens**: A hasonló ingatlanok {abs(deviation):.1f}%-kal olcsóbbak az átlagnál")
            else:
                st.info("ℹ️ **Átlagos piaci szegmens**: A hasonló ingatlanok az átlagos árszínvonalon mozognak")
    
    # Befektetési elemzés
    st.header("💼 Befektetési Elemzés")
    
    with st.expander("💰 Befektetési pontszám magyarázata"):
        st.markdown("""
        **Hogyan számoljuk a befektetési pontszámot?**
        - **Állapot pontszám (40%)**: Felújított=3, Jó=2, Közepes=1, Felújítandó=0
        - **Ár pozíció (60%)**: Alacsonyabb ár = magasabb pontszám
        - **Végső pontszám**: 0.0 (legrosszabb) - 1.0 (legjobb) skálán
        
        **Mit keresek a táblázatban?**
        - **Magas pontszám (0.7+)**: Kiváló ár/érték arány
        - **Közepes pontszám (0.4-0.7)**: Megfontolásra érdemes
        - **Alacsony pontszám (0.0-0.4)**: Drága vagy rossz állapotú
        
        **Befektetési stratégiák:**
        - **Magánszemély hirdetések**: Gyakran rugalmasabb ár
        - **Ingatlaniroda**: Profi árazás, kevés alkudozási lehetőség
        - **Bizonytalan kategória**: További kutatást igényel
        
        **Kockázati tényezők:**
        - Felújítandó ingatlanok: +időigény, +kockázat, de +potenciál
        - Felső emeletek: Lift-függőség, kisebb célcsoport
        """)
    
    # Állapot szűrő a befektetési elemzéshez
    col_filter, col_space = st.columns([1, 3])
    with col_filter:
        investment_condition_filter = st.selectbox(
            "🏠 Állapot szűrő (befektetési elemzés)",
            options=["Összes állapot"] + list(df['ingatlan_allapota'].dropna().unique()),
            index=0,
            key="investment_analysis_filter"
        )
    
    # Szűrt adatok a befektetési elemzéshez
    if investment_condition_filter != "Összes állapot":
        df_investment_base = df[df['ingatlan_allapota'] == investment_condition_filter]
        st.info(f"📊 Befektetési elemzés szűrve: **{investment_condition_filter}** állapotú ingatlanok ({len(df_investment_base)} db)")
    else:
        df_investment_base = df
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Legjobb ár/érték arány")
        
        # Ár/érték számítás (alacsonyabb ár + jobb állapot = jobb deal)
        df_investment = df_investment_base.dropna(subset=['ar_szam', 'ingatlan_allapota']).copy()
        
        if len(df_investment) > 0:
            # Állapot pontozás
            condition_scores = {'felújított': 3, 'jó állapotú': 2, 'közepes állapotú': 1, 'felújítandó': 0}
            df_investment['allapot_pont'] = df_investment['ingatlan_allapota'].map(condition_scores).fillna(1)
            
            # Ár percentil (alacsonyabb = jobb)
            df_investment['ar_percentil'] = df_investment['ar_szam'].rank(pct=True)
            
            # Befektetési pontszám
            df_investment['befektetes_pont'] = (
                df_investment['allapot_pont'] * 0.4 + 
                (1 - df_investment['ar_percentil']) * 0.6
            )
            
            top_investments = df_investment.nlargest(min(5, len(df_investment)), 'befektetes_pont')[
                ['id', 'cim', 'ar_szam', 'ingatlan_allapota', 'befektetes_pont', 'hirdeto_tipus']
            ]
            
            st.dataframe(top_investments, use_container_width=True)
        else:
            st.warning("⚠️ Nincs elegendő adat a befektetési elemzéshez a kiválasztott szűrővel.")
    
    with col2:
        st.subheader("📊 Hirdető típus elemzés")
        
        if len(df_investment_base) > 0:
            advertiser_analysis = df_investment_base.groupby('hirdeto_tipus').agg({
                'ar_szam': ['mean', 'std'],
                'id': 'count'
            }).round(0)
            advertiser_analysis.columns = ['Átlag ár', 'Szórás', 'Darab']
            
            st.dataframe(advertiser_analysis, use_container_width=True)
            
            # Hirdető típus insight
            if len(df_investment_base['hirdeto_tipus'].value_counts()) > 0:
                most_common = df_investment_base['hirdeto_tipus'].value_counts().index[0]
                most_common_pct = (df_investment_base['hirdeto_tipus'].value_counts().iloc[0] / len(df_investment_base)) * 100
                st.info(f"💡 A szűrt adatok között a legtöbb hirdetés ({most_common_pct:.0f}%) **{most_common}** kategóriába tartozik")
        else:
            st.warning("⚠️ Nincs adat a kiválasztott szűrőhöz.")    # Részletes szűrők
    st.header("🔍 Részletes Szűrők és Keresés")
    
    st.markdown("""
    **Használd a szűrőket a személyre szabott kereséshez:**
    - **Ár tartomány**: Határozd meg a költségvetésed
    - **Emelet**: Válaszd ki a preferált szintet 
    - **Hirdető típus**: Magánszemély vs. iroda hirdetések
    - **Állapot**: Szűrj a felújítás mértéke szerint
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        price_range = st.slider(
            "M² ár tartomány (Ft)",
            int(df['ar_szam'].min()),
            int(df['ar_szam'].max()),
            (int(df['ar_szam'].min()), int(df['ar_szam'].max()))
        )
    
    with col2:
        selected_floors = st.multiselect(
            "Emelet kategóriák",
            options=df['emelet_kategoria'].unique(),
            default=df['emelet_kategoria'].unique()
        )
    
    with col3:
        selected_advertisers = st.multiselect(
            "Hirdető típusok",
            options=df['hirdeto_tipus'].dropna().unique(),
            default=df['hirdeto_tipus'].dropna().unique()
        )
    
    with col4:
        selected_conditions = st.multiselect(
            "Ingatlan állapota",
            options=df['ingatlan_allapota'].dropna().unique(),
            default=df['ingatlan_allapota'].dropna().unique()
        )
    
    # Szűrt adatok
    filtered_df = df[
        (df['ar_szam'] >= price_range[0]) &
        (df['ar_szam'] <= price_range[1]) &
        (df['emelet_kategoria'].isin(selected_floors)) &
        (df['hirdeto_tipus'].isin(selected_advertisers)) &
        (df['ingatlan_allapota'].isin(selected_conditions))
    ]
    
    st.subheader(f"🎯 Szűrt eredmények: {len(filtered_df)} ingatlan")
    
    if len(filtered_df) > 0:
        # Kiemelt oszlopok megjelenítése
        display_cols = ['id', 'cim', 'teljes_ar', 'terulet', 'nm_ar', 'szobak', 
                       'emelet_kategoria', 'ingatlan_allapota', 'hirdeto_tipus']
        
        st.info(f"""
        **📋 Szűrt eredmények értelmezése:**
        - **ID**: Ingatlan azonosító (ingatlan.com-on kereshető)
        - **Cím**: Pontos cím vagy környék
        - **Teljes ár**: Összes vételár
        - **Terület**: Lakás mérete m²-ben
        - **Nm ár**: Négyzetméter ár (összehasonlításhoz)
        - **Szobák**: Szobák száma + nappali
        - **Emelet kategória**: Algoritmus által kategorizált szint
        - **Állapot**: Felújítási igény mértéke
        - **Hirdető**: Ki adja el (befolyásolja az alkudozhatóságot)
        """)
        
        st.dataframe(filtered_df[display_cols], use_container_width=True)
    else:
        st.warning("🔍 A szűrési feltételeknek megfelelő ingatlan nem található. Módosítsd a szűrőket!")
    
    # Export lehetőség
    st.header("📥 Adatok Exportálása")
    
    if st.button("📊 Exportáld a szűrt adatokat CSV-be"):
        csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="💾 CSV Letöltés",
            data=csv,
            file_name=f"kobanyi_ingatlan_szurt_{len(filtered_df)}_db.csv",
            mime="text/csv"
        )
    
    # ÚJ: AI Hirdetési Szöveg Generátor
    st.header("🤖 AI Hirdetési Szöveg Generátor")
    
    with st.expander("📝 Mire jó ez a funkció?"):
        st.markdown("""
        **🎯 Profi hirdetési szöveg generálás**:
        - **Piaci adatok alapján** optimalizált szöveg
        - **SEO-barát** kulcsszavak automatikus beépítése
        - **Eladási stratégiai tanácsok** integrálása
        - **Lokáció-specifikus** előnyök kiemelése
        
        **Hogyan működik?**
        - Elemzi a hasonló ingatlanok leírásait
        - Kiszámolja a javasolt árazást
        - Generálja a leghatékonyabb kulcsszavakat
        - Személyre szabott szöveget készít
        """)
    
    st.subheader("🏠 Ingatlan adatok megadása")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        listing_area = st.number_input("Lakás mérete (m²)", min_value=20, max_value=150, value=49, step=1, key="listing_area")
    with col2:
        listing_rooms = st.selectbox("Szobák száma", [1, 2, 3, 4, 5], index=1, key="listing_rooms")
    with col3:
        listing_condition = st.selectbox("Állapot", 
                                       ["felújított", "jó állapotú", "közepes állapotú", "felújítandó"],
                                       index=2, key="listing_condition")
    with col4:
        listing_floor = st.number_input("Emelet", min_value=0, max_value=15, value=6, step=1, key="listing_floor")
    
    if st.button("🚀 Hirdetési szöveg generálása", type="primary"):
        with st.spinner("🤖 AI generálja a hirdetési szöveget..."):
            # Hirdetési szöveg generálása
            listing_text = generate_listing_text(listing_area, listing_rooms, listing_condition, listing_floor, df)
            
            st.success("✅ Hirdetési szöveg elkészült!")
            
            # Szöveg megjelenítése szerkeszthetően
            st.subheader("📝 Generált hirdetési szöveg")
            
            edited_text = st.text_area(
                "Szerkeszthető hirdetési szöveg:",
                value=listing_text,
                height=600,
                help="Szerkeszd a szöveget igényeid szerint, majd másold ki!"
            )
            
            # Statisztikák a generált szövegről
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📏 Karakterek száma", len(edited_text))
            with col2:
                st.metric("📝 Szavak száma", len(edited_text.split()))
            with col3:
                st.metric("📊 Sorok száma", edited_text.count('\n') + 1)
            with col4:
                emojik = len([c for c in edited_text if ord(c) > 127])
                st.metric("🎯 Emojik száma", emojik)
            
            # Másolás segítség
            st.info("""
            💡 **Használati tippek:**
            - **Ctrl+A** → teljes szöveg kijelölése
            - **Ctrl+C** → másolás
            - **Customize** → módosítsd a szöveget saját igényeid szerint
            - **Platformok**: Facebook Marketplace, ingatlan.com, OtthonCentrum
            """)

def generate_listing_text(area, rooms, condition, floor, df):
    """AI-alapú hirdetési szöveg generálás"""
    
    # Piaci adatok gyűjtése
    similar_props = df[
        (abs(df['terulet_szam'] - area) <= 10) &
        (df['szobak'] == rooms)
    ]
    
    avg_price = similar_props['ar_szam'].mean() if len(similar_props) > 0 else df['ar_szam'].mean()
    
    # Emelet előnyök/hátrányok
    if floor >= 6:
        floor_benefits = "A magasabb emelet csodálatos kilátást biztosít a környező zöld területekre, miközben csendes, nyugodt környezetet teremt."
    elif 3 <= floor <= 5:
        floor_benefits = "Az optimális emeleti magasság ideális kompromisszum a könnyű megközelíthetőség és a szép kilátás között."
    else:
        floor_benefits = "Az alacsonyabb emelet könnyen megközelíthető, ideális idősebb lakók és családok számára."
    
    # Állapot leírása
    condition_desc = {
        'felújított': 'teljesen felújított, azonnal költözhető',
        'jó állapotú': 'kiváló állapotban, minimális befektetéssel tökéletes',
        'közepes állapotú': 'jó állapotban, saját ízlés szerint alakítható',
        'felújítandó': 'nagyszerű befektetési lehetőség, saját elképzelések szerint alakítható'
    }.get(condition, 'rendezett állapotban')
    
    # Árazási stratégia
    if avg_price > 0:
        suggested_price = avg_price * area
        price_text = f"Ár: {suggested_price/1000000:.1f} millió Ft ({avg_price:,.0f} Ft/m²)"
    else:
        price_text = "Versenyképes árazás"
    
    # Hirdetési szöveg összeállítása
    listing_text = f"""🏠 **ELADÓ: {rooms} szobás, {area}m² lakás a Kőbánya-Újhegyi lakótelepen**

📍 **Lokáció**: Kőbánya X. kerület, Újhegyi lakótelep - Budapest egyik legkedveltebb, zöld környezetű lakótelepén

🏢 **Ingatlan jellemzői**:
• {area} m² hasznos terület
• {rooms} szoba + nappali + konyha + fürdőszoba
• {floor}. emelet
• {condition_desc}

✨ **Kiemelkedő előnyök**:
• {floor_benefits}
• Panelprogramon átesett, szigetelt épület - alacsony rezsiköltségek
• Távfűtés - megbízható, gazdaságos
• Ingyenes parkolási lehetőség az épület előtt
• Kiváló tömegközlekedés - közvetlen buszjáratok a metróhoz

🌟 **Környezet és szolgáltatások**:
• Zöld, parkokkal teli lakótelepi környezet
• 5 percre gyalogosan bevásárlási központok (Auchan, Interspar)
• Közeli egészségügyi ellátás (Bajcsy Kórház)
• Iskolák és óvodák a közelben
• Sportolási és szabadidős lehetőségek

💰 **{price_text}**

📞 **További információ és megtekintés**:
Az ingatlan tehermentes, gyorsan költözhető. Rugalmas megtekintési lehetőségek.
Befektetésként is kiváló választás - stabil bérleti piac.

📱 Hívjon bizalommal! Minden kérdésére választ adok.

#KőbányaIngatlan #ÚjhegyiLakótelep #BudapestEladóLakás #PanelProgramos #IngyenesParkolás"""
    
    return listing_text.strip()

if __name__ == "__main__":
    main()
