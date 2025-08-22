"""
BUDAÖRS INGATLAN DASHBOARD - KOORDINÁTÁS VERZIÓ
===============================================

🎯 Budaörs ingatlanok interaktív térkép-alapú elemzése
📍 GPS koordináták: 100% lefedettség
🗺️ Interaktív folium térkép ár-alapú színkódolással

Generated from streamlit_app.py template on: 2025.08.22
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re
import os
from datetime import datetime
import glob
import warnings
import folium
from streamlit_folium import st_folium
warnings.filterwarnings('ignore')

# BUDAÖRS SPECIFIKUS BEÁLLÍTÁSOK
def get_location_from_filename():
    """Fix location név visszaadása - Budaörs esetére"""
    return "BUDAÖRS"

location_name = get_location_from_filename()
timestamp = datetime.now().strftime("%Y.%m.%d %H:%M")

# Streamlit konfiguráció
st.set_page_config(
    page_title=f"Ingatlan Dashboard - {location_name} - {timestamp}",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_and_process_data():
    """Adatok betöltése és feldolgozása - Budaörs koordinátás CSV prioritással"""
    try:
        # Budaörs CSV pattern - koordinátás verzió prioritással
        location_patterns = [
            "ingatlan_reszletes_budaors_*_koordinatak_*.csv",  # Koordinátás verzió - prioritás
            "ingatlan_reszletes_budaors_*.csv",                # Eredeti verzió fallback
            "ingatlan_*budaors*.csv"                           # Általános pattern
        ]
        
        # Fix lokáció pattern keresés - mindig a legfrissebb CSV-t választja
        for pattern in location_patterns:
            matching_files = glob.glob(pattern)
            if matching_files:
                # Legfrissebb fájl kiválasztása időbélyeg alapján (fájl módosítás ideje szerint)
                latest_file = max(matching_files, key=lambda f: os.path.getmtime(f))
                print(f"📊 Legfrissebb CSV betöltése ({pattern}): {latest_file}")
                
                df = pd.read_csv(latest_file, encoding='utf-8-sig', sep='|')
                
                # Ellenőrizzük, hogy sikerült-e betölteni
                if df.empty:
                    continue  # Próbáljuk a következő pattern-t
                
                # Numerikus konverziók - hibakezelő módon
                if 'teljes_ar' in df.columns:
                    df['teljes_ar_millió'] = df['teljes_ar'].apply(parse_million_ft)
                
                if 'terulet' in df.columns:
                    df['terulet_szam'] = df['terulet'].apply(parse_area)
                
                if 'szobak' in df.columns:
                    df['szobak_szam'] = df['szobak'].apply(parse_rooms)
                
                # Családbarát pontszám számítása
                df['csaladbarati_pontszam'] = df.apply(create_family_score, axis=1)
                
                # Modern nettó pont számítás
                modern_columns = ['zold_energia_premium_pont', 'wellness_luxury_pont', 'smart_technology_pont', 'premium_design_pont']
                available_modern_cols = [col for col in modern_columns if col in df.columns]
                if available_modern_cols:
                    df['modern_netto_pont'] = df[available_modern_cols].fillna(0).sum(axis=1)
                else:
                    df['modern_netto_pont'] = 0
                
                print(f"✅ Betöltve: {len(df)} rekord")
                return df
        
        # Ha egyik pattern sem működött
        st.error("HIBA: Nincs található Budaörs CSV fájl!")
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Adatbetöltési hiba: {e}")
        return pd.DataFrame()

def parse_million_ft(text):
    """Millió Ft konvertálása számra"""
    if pd.isna(text):
        return None
    text_str = str(text).replace(',', '.')
    # "159 M Ft" -> 159, "263,80 M Ft" -> 263.80
    match = re.search(r'(\d+(?:\.\d+)?)\s*M', text_str)
    return float(match.group(1)) if match else None

def parse_area(text):
    """Terület konvertálása számra"""
    if pd.isna(text):
        return None
    text_str = str(text)
    # "133 m2" -> 133
    match = re.search(r'(\d+)', text_str)
    return int(match.group(1)) if match else None

def parse_rooms(text):
    """Szobaszám konvertálása számra"""
    if pd.isna(text):
        return None
    text_str = str(text)
    # "5 + 1 fél" -> 5, "4 + 1 fél" -> 4, "3" -> 3
    match = re.search(r'(\d+)', text_str)
    return int(match.group(1)) if match else None

def create_family_score(row):
    """Családbarát pontszám számítása (0-100)"""
    score = 0
    
    # Terület pontszám (max 25 pont)
    if pd.notna(row.get('terulet_szam')):
        area = row['terulet_szam']
        if area >= 200:
            score += 25
        elif area >= 150:
            score += 20
        elif area >= 120:
            score += 15
        elif area >= 100:
            score += 10
        else:
            score += 5
    
    # Szobaszám pontszám (max 25 pont)
    if pd.notna(row.get('szobak_szam')):
        rooms = row['szobak_szam']
        if rooms >= 5:
            score += 25
        elif rooms >= 4:
            score += 20
        elif rooms >= 3:
            score += 15
        else:
            score += 10
    else:
        # Ha nincs szobaszám adat, átlag pontot adunk (15 pont)
        score += 15
    
    # Állapot pontszám (max 25 pont)
    condition_raw = row.get('ingatlan_allapota', '')
    condition = str(condition_raw).lower() if pd.notna(condition_raw) else ''
    if 'új' in condition or 'újépítésű' in condition:
        score += 25
    elif 'felújított' in condition or 'kitűnő' in condition:
        score += 20
    elif 'jó' in condition:
        score += 15
    elif 'közepes' in condition:
        score += 10
    else:
        score += 5
    
    # Modern funkciók pontszám (max 25 pont)
    modern_score = 0
    modern_features = ['van_zold_energia', 'van_wellness_luxury', 'van_smart_tech', 'van_premium_design']
    for feature in modern_features:
        if row.get(feature, False):
            modern_score += 6.25
    score += modern_score
    
    return min(100, max(0, score))

def generate_ingatlan_url(row):
    """Ingatlan.com URL kinyerése a link oszlopból"""
    try:
        # Próbáljuk meg a link oszlopból
        if pd.notna(row.get('link')):
            return row['link']
        elif pd.notna(row.get('id')):
            return f"https://ingatlan.com/szukites/{row['id']}"
        return None
    except (KeyError, AttributeError, TypeError):
        # Ha valami hiba lenne, fallback
        if pd.notna(row.get('id')):
            return f"https://ingatlan.com/szukites/{row['id']}"
        return None

def create_clickable_link(text, url):
    """Kattintható link létrehozása Streamlit-ben"""
    if url:
        return f"[{text}]({url})"
    return text

def main():
    """Főalkalmazás"""
    
    # Fejléc
    st.title(f"👨‍👩‍👧‍👦 Ingatlan Dashboard - {location_name} - {timestamp}")
    st.markdown("**3 gyerekes családok számára optimalizált ingatlankeresés**")
    st.markdown("*Nagy méret, remek állapot, modern funkciók, mégis jó ár/érték arány*")
    
    # Adatok betöltése
    df = load_and_process_data()
    if df.empty:
        return
    
    # Sidebar filterek
    st.sidebar.header("🎯 Szűrők")
    
    # Ár szűrő
    if 'teljes_ar_millió' in df.columns and df['teljes_ar_millió'].notna().any():
        min_price = float(df['teljes_ar_millió'].min())
        max_price = float(df['teljes_ar_millió'].max())
        
        # Ha min és max azonos, akkor nem csinálunk slider-t
        if min_price == max_price:
            price_range = None
            st.sidebar.write(f"💰 Ár: {min_price} M Ft (fix)")
        else:
            price_range = st.sidebar.slider(
                "💰 Ár (millió Ft)",
                min_value=min_price,
                max_value=max_price,
                value=(min_price, max_price),
                step=1.0
            )
    else:
        price_range = None
    
    # Terület szűrő
    if 'terulet_szam' in df.columns and df['terulet_szam'].notna().any():
        min_area = int(df['terulet_szam'].min())
        max_area = int(df['terulet_szam'].max())
        
        # Ha min és max azonos, akkor nem csinálunk slider-t
        if min_area == max_area:
            area_range = None
            st.sidebar.write(f"📏 Terület: {min_area} m² (fix)")
        else:
            area_range = st.sidebar.slider(
                "📏 Terület (m²)",
                min_value=min_area,
                max_value=max_area,
                value=(min_area, max_area),
                step=5
            )
    else:
        area_range = None
    
    # Szobaszám szűrő
    if 'szobak_szam' in df.columns and df['szobak_szam'].notna().any():
        min_rooms = int(df['szobak_szam'].min())
        max_rooms = int(df['szobak_szam'].max())
        
        # Ha min és max azonos, akkor nem csinálunk slider-t
        if min_rooms == max_rooms:
            rooms_range = None
            st.sidebar.write(f"🛏️ Szobák: {min_rooms} (fix)")
        else:
            rooms_range = st.sidebar.slider(
                "🛏️ Szobák száma",
                min_value=min_rooms,
                max_value=max_rooms,
                value=(min_rooms, max_rooms),
                step=1
            )
    else:
        rooms_range = None
    
    # Állapot szűrő
    if 'ingatlan_allapota' in df.columns:
        conditions = df['ingatlan_allapota'].dropna().unique()
        selected_conditions = st.sidebar.multiselect(
            "🔧 Állapot",
            options=conditions,
            default=conditions
        )
    else:
        selected_conditions = None
    
    # Modern funkciók szűrő
    st.sidebar.subheader("⭐ Modern Funkciók")
    filter_green = st.sidebar.checkbox("🌞 Zöld energia", value=False)
    filter_wellness = st.sidebar.checkbox("🏊 Wellness & Luxury", value=False)
    filter_smart = st.sidebar.checkbox("🏠 Smart Technology", value=False)
    filter_premium = st.sidebar.checkbox("💎 Premium Design", value=False)
    
    # Szűrés alkalmazása
    filtered_df = df.copy()
    
    if price_range:
        filtered_df = filtered_df[
            (filtered_df['teljes_ar_millió'].isna()) |
            ((filtered_df['teljes_ar_millió'] >= price_range[0]) &
             (filtered_df['teljes_ar_millió'] <= price_range[1]))
        ]
    
    if area_range:
        filtered_df = filtered_df[
            (filtered_df['terulet_szam'].isna()) |
            ((filtered_df['terulet_szam'] >= area_range[0]) &
             (filtered_df['terulet_szam'] <= area_range[1]))
        ]
    
    if rooms_range:
        # Csak azokat szűrjük, amelyeknél van szobaszám adat
        filtered_df = filtered_df[
            (filtered_df['szobak_szam'].isna()) |
            ((filtered_df['szobak_szam'] >= rooms_range[0]) &
             (filtered_df['szobak_szam'] <= rooms_range[1]))
        ]
    
    if selected_conditions:
        filtered_df = filtered_df[filtered_df['ingatlan_allapota'].isin(selected_conditions)]
    
    if filter_green:
        filtered_df = filtered_df[filtered_df['van_zold_energia'] == True]
    if filter_wellness:
        filtered_df = filtered_df[filtered_df['van_wellness_luxury'] == True]
    if filter_smart:
        filtered_df = filtered_df[filtered_df['van_smart_tech'] == True]
    if filter_premium:
        filtered_df = filtered_df[filtered_df['van_premium_design'] == True]
    
    # Eredmények megjelenítése
    st.header(f"🏠 Találatok: {len(filtered_df)} ingatlan")
    
    if len(filtered_df) == 0:
        st.warning("❌ Nincs találat a szűrési feltételeknek megfelelően. Módosítsd a szűrőket!")
        return
    
    # Általános statisztikák
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_price = filtered_df['teljes_ar_millió'].mean()
        st.metric("💰 Átlagár", f"{avg_price:.1f} M Ft" if pd.notna(avg_price) else "N/A")
    
    with col2:
        avg_area = filtered_df['terulet_szam'].mean()
        st.metric("📏 Átlag terület", f"{avg_area:.0f} m²" if pd.notna(avg_area) else "N/A")
    
    with col3:
        avg_family = filtered_df['csaladbarati_pontszam'].mean()
        st.metric("👨‍👩‍👧‍👦 Átlag családbarát pont", f"{avg_family:.0f}" if pd.notna(avg_family) else "N/A")
    
    with col4:
        coord_count = filtered_df[['geo_latitude', 'geo_longitude']].dropna().shape[0]
        st.metric("🗺️ GPS koordinátával", f"{coord_count}/{len(filtered_df)}")
    
    # Top 5 legjobb ingatlan
    st.header("🏆 TOP 5 Legcsaládbarátabb Ingatlan")
    
    top_5 = filtered_df.nlargest(5, 'csaladbarati_pontszam')
    
    for idx, (_, row) in enumerate(top_5.iterrows(), 1):
        with st.expander(f"#{idx} | {row['cim']} | {row['csaladbarati_pontszam']:.0f} pont"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"💰 **Ár:** {row.get('teljes_ar', 'N/A')}")
                st.write(f"📏 **Terület:** {row.get('terulet', 'N/A')}")
                st.write(f"🛏️ **Szobák:** {row.get('szobak', 'N/A')}")
                st.write(f"🔧 **Állapot:** {row.get('ingatlan_allapota', 'N/A')}")
            
            with col2:
                url = generate_ingatlan_url(row)
                if url:
                    st.markdown(f"🔗 **[Megtekintés ingatlan.com-on]({url})**")
                
                # Modern funkciók
                modern_features = []
                if row.get('van_zold_energia'): modern_features.append("🌞 Zöld energia")
                if row.get('van_wellness_luxury'): modern_features.append("🏊 Wellness")
                if row.get('van_smart_tech'): modern_features.append("🏠 Smart tech")
                if row.get('van_premium_design'): modern_features.append("💎 Premium design")
                
                if modern_features:
                    st.write("⭐ **Modern funkciók:**")
                    for feature in modern_features:
                        st.write(f"  - {feature}")

    # 🗺️ INTERAKTÍV TÉRKÉP - szűrt adatokkal
    create_interactive_map(filtered_df, location_name)
    
    # Vizualizációk
    st.header("📊 Vizualizációk")
    
    # Ár vs Terület scatter plot családbarát pontszám szerint
    fig1 = px.scatter(
        filtered_df, 
        x='terulet_szam', 
        y='teljes_ar_millió',
        color='csaladbarati_pontszam',
        hover_data=['cim', 'ingatlan_allapota'],
        title="Ár vs Terület (színkód: családbarát pontszám)",
        labels={'terulet_szam': 'Terület (m²)', 'teljes_ar_millió': 'Ár (M Ft)'}
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Scatter Plot Elemzés
    st.subheader("📈 Ár vs. Egyéb Változók Elemzése")
    
    # Numerikus oszlopok kigyűjtése
    numeric_columns = []
    column_labels = {}
    
    # Alapvető numerikus változók
    if 'terulet_szam' in filtered_df.columns:
        numeric_columns.append('terulet_szam')
        column_labels['terulet_szam'] = 'Terület (m²)'
    
    if 'szobak_szam' in filtered_df.columns:
        numeric_columns.append('szobak_szam')
        column_labels['szobak_szam'] = 'Szobák száma'
    
    if 'csaladbarati_pontszam' in filtered_df.columns:
        numeric_columns.append('csaladbarati_pontszam')
        column_labels['csaladbarati_pontszam'] = 'Családbarát pontszám'
    
    if 'modern_netto_pont' in filtered_df.columns:
        numeric_columns.append('modern_netto_pont')
        column_labels['modern_netto_pont'] = 'Modern nettó pont'
    
    if 'kepek_szama' in filtered_df.columns:
        numeric_columns.append('kepek_szama')
        column_labels['kepek_szama'] = 'Képek száma'
    
    # Modern funkciók (boolean -> numeric)
    modern_features = ['van_zold_energia', 'van_wellness_luxury', 'van_smart_tech', 'van_premium_design']
    for feature in modern_features:
        if feature in filtered_df.columns:
            numeric_columns.append(feature)
            feature_names = {
                'van_zold_energia': '🌞 Zöld energia (van/nincs)',
                'van_wellness_luxury': '🏊 Wellness & Luxury (van/nincs)',
                'van_smart_tech': '🏠 Smart Technology (van/nincs)',
                'van_premium_design': '💎 Premium Design (van/nincs)'
            }
            column_labels[feature] = feature_names[feature]
    
    # Kategorikus változók számérték konverziója
    categorical_vars = []
    if 'ingatlan_allapota' in filtered_df.columns:
        categorical_vars.append('ingatlan_allapota')
        column_labels['ingatlan_allapota'] = 'Ingatlan állapota (kódolva)'
    
    if 'hirdeto_tipus' in filtered_df.columns:
        categorical_vars.append('hirdeto_tipus')
        column_labels['hirdeto_tipus'] = 'Hirdető típusa (kódolva)'
    
    if len(numeric_columns) > 0 and 'teljes_ar_millió' in filtered_df.columns:
        selected_x = st.selectbox(
            "Válassz X-tengely változót az ár elemzéshez:",
            options=numeric_columns,
            format_func=lambda x: column_labels.get(x, x)
        )
        
        fig_scatter = px.scatter(
            filtered_df,
            x=selected_x,
            y='teljes_ar_millió',
            color='csaladbarati_pontszam',
            hover_data=['cim'],
            title=f"Ár vs {column_labels.get(selected_x, selected_x)}",
            labels={
                selected_x: column_labels.get(selected_x, selected_x),
                'teljes_ar_millió': 'Ár (M Ft)',
                'csaladbarati_pontszam': 'Családbarát pontszám'
            }
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Nincs elegendő numerikus adat a scatter plot elemzéshez.")
    
    # Modern funkciók eloszlás
    if all(col in filtered_df.columns for col in ['van_zold_energia', 'van_wellness_luxury', 'van_smart_tech', 'van_premium_design']):
        st.subheader("⭐ Modern Funkciók Eloszlása")
        
        modern_counts = {
            '🌞 Zöld energia': filtered_df['van_zold_energia'].sum(),
            '🏊 Wellness & Luxury': filtered_df['van_wellness_luxury'].sum(),
            '🏠 Smart Technology': filtered_df['van_smart_tech'].sum(),
            '💎 Premium Design': filtered_df['van_premium_design'].sum()
        }
        
        fig_modern = px.bar(
            x=list(modern_counts.keys()),
            y=list(modern_counts.values()),
            title="Modern funkciók megoszlása",
            labels={'x': 'Funkció típusa', 'y': 'Ingatlanok száma'}
        )
        st.plotly_chart(fig_modern, use_container_width=True)
    
    # Statisztikai összefoglaló táblázat
    st.header("📊 Statisztikai Összefoglaló")
    
    # Numerikus változók statisztikái
    st.subheader("🔢 Numerikus Változók")
    
    numeric_stats = pd.DataFrame({
        'Változó': ['Ár (M Ft)', 'Terület (m²)', 'Szobaszám', 'Családbarát Pont'],
        'Átlag': [
            filtered_df['teljes_ar_millió'].mean(),
            filtered_df['terulet_szam'].mean(),
            filtered_df['szobak_szam'].mean(),
            filtered_df['csaladbarati_pontszam'].mean()
        ],
        'Medián': [
            filtered_df['teljes_ar_millió'].median(),
            filtered_df['terulet_szam'].median(), 
            filtered_df['szobak_szam'].median(),
            filtered_df['csaladbarati_pontszam'].median()
        ],
        'Szórás': [
            filtered_df['teljes_ar_millió'].std(),
            filtered_df['terulet_szam'].std(),
            filtered_df['szobak_szam'].std(), 
            filtered_df['csaladbarati_pontszam'].std()
        ],
        'Minimum': [
            filtered_df['teljes_ar_millió'].min(),
            filtered_df['terulet_szam'].min(),
            filtered_df['szobak_szam'].min(),
            filtered_df['csaladbarati_pontszam'].min()
        ],
        'Maximum': [
            filtered_df['teljes_ar_millió'].max(),
            filtered_df['terulet_szam'].max(),
            filtered_df['szobak_szam'].max(),
            filtered_df['csaladbarati_pontszam'].max()
        ]
    }).round(2)
    
    st.dataframe(numeric_stats, use_container_width=True)
    
    # Kategorikus változók statisztikái
    st.subheader("🏷️ Kategorikus Változók")
    
    categorical_cols = []
    categorical_data = []
    
    # Állapot elemzés
    if 'ingatlan_allapota' in filtered_df.columns:
        condition_counts = filtered_df['ingatlan_allapota'].value_counts()
        for condition, count in condition_counts.items():
            categorical_data.append({
                'Kategória': '🔧 Ingatlan állapot',
                'Érték': condition,
                'Darabszám': count,
                'Arány (%)': round(count/len(filtered_df)*100, 1)
            })
    
    # Modern funkciók elemzése
    modern_features = ['van_zold_energia', 'van_wellness_luxury', 'van_smart_tech', 'van_premium_design']
    feature_names = ['🌞 Zöld Energia', '🏊 Wellness & Luxury', '🏠 Smart Technology', '💎 Premium Design']
    
    for feature, name in zip(modern_features, feature_names):
        if feature in filtered_df.columns:
            count_yes = filtered_df[feature].sum()
            count_no = len(filtered_df) - count_yes
            categorical_data.append({
                'Kategória': name,
                'Érték': 'Van',
                'Darabszám': count_yes,
                'Arány (%)': round(count_yes/len(filtered_df)*100, 1)
            })
            categorical_data.append({
                'Kategória': name,
                'Érték': 'Nincs',
                'Darabszám': count_no,
                'Arány (%)': round(count_no/len(filtered_df)*100, 1)
            })
    
    if categorical_data:
        categorical_df = pd.DataFrame(categorical_data)
        st.dataframe(categorical_df, use_container_width=True, hide_index=True)
    
    # Részletes adattábla
    st.header("📋 Részletes Lista")
    st.markdown("**Minden szűrt ingatlan részletei kattintható linkekkel:**")
    
    display_columns = [
        'cim', 'teljes_ar', 'terulet', 'szobak', 'ingatlan_allapota', 'csaladbarati_pontszam', 'modern_netto_pont', 'link'
    ]
    
    available_columns = [col for col in display_columns if col in filtered_df.columns]
    
    display_df = filtered_df[available_columns].copy()
    display_df = display_df.sort_values('csaladbarati_pontszam', ascending=False)
    
    # Valódi ingatlan.com ID kinyerése a linkből + URL generálás
    def extract_ingatlan_id(link):
        if pd.isna(link):
            return "N/A"
        try:
            # https://ingatlan.com/szukites/elado+haz+budaors-kertvaros-ganztelep+119-m2+4-szoba+263-8-millió-ft/lista/12345 -> 12345
            match = re.search(r'/lista/(\d+)', str(link))
            if match:
                return match.group(1)
            # Alternatív pattern: /12345 a végén
            match = re.search(r'/(\d+)/?$', str(link))
            if match:
                return match.group(1)
            return "Link"
        except:
            return "Link"
    
    # Hozzáadjuk a valódi ID-t - JAVÍTOTT verzió Streamlit-kompatibilis
    display_df_with_links = []
    for idx, (_, row) in enumerate(display_df.iterrows(), 1):
        row_dict = {
            'Sorszám': idx,
            'Cím': row.get('cim', 'N/A'),
            'Ár': row.get('teljes_ar', 'N/A'),
            'Terület': row.get('terulet', 'N/A'),
            'Szobák': row.get('szobak', 'N/A'),
            'Állapot': row.get('ingatlan_allapota', 'N/A'),
            'Családbarát pont': int(row.get('csaladbarati_pontszam', 0)),
            'Modern pont': round(row.get('modern_netto_pont', 0), 1),
            'Link': create_clickable_link(extract_ingatlan_id(row.get('link')), row.get('link'))
        }
        display_df_with_links.append(row_dict)
    
    # DataFrame létrehozása
    final_display_df = pd.DataFrame(display_df_with_links)
    
    # Dataframe megjelenítése
    st.dataframe(final_display_df, use_container_width=True, hide_index=True)
    
    # Záró információk
    st.markdown("---")
    st.markdown("**📝 Családbarát Pontszám Számítási Módszer:**")
    st.markdown("""
    A **Családbarát Pontszám** 0-100 pontos skálán értékeli az ingatlanokat, négy fő kategóriában:
    
    **🏠 Terület pontszám (max 25 pont):**
    - 200+ m²: 25 pont
    - 150-199 m²: 20 pont  
    - 120-149 m²: 15 pont
    - 100-119 m²: 10 pont
    - 100 m² alatt: 5 pont
    
    **🛏️ Szobaszám pontszám (max 25 pont):**
    - 5+ szoba: 25 pont
    - 4 szoba: 20 pont
    - 3 szoba: 15 pont
    - 2 vagy kevesebb szoba: 10 pont
    - Hiányzó adat esetén: 15 pont (átlag)
    
    **🔧 Állapot pontszám (max 25 pont):**
    - Új/Újépítésű: 25 pont
    - Felújított/Kitűnő: 20 pont
    - Jó: 15 pont
    - Közepes: 10 pont
    - Egyéb/Rossz: 5 pont
    
    **⚡ Modern funkciók pontszám (max 25 pont):**
    - Minden modern funkció 6,25 pontot ér:
      - 🌞 Zöld energia (napelem, hőszivattyú)
      - 🏊 Wellness & Luxury (medence, szauna)
      - 🏠 Smart Technology (okos otthon)
      - 💎 Premium Design (modern dizájn)
    """)
    st.markdown("---")
    st.markdown("**📊 További Megjegyzések:**")
    st.markdown("- A családbarát pontszám 3 gyerekes családok igényeit figyelembe véve készült")
    st.markdown("- 150+ m² és 4+ szoba ideális nagyobb családok számára")  
    st.markdown("- A modern pontszám további kényelmi és technológiai elemeket értékel")
    st.markdown(f"- Az adatok {timestamp} állapot szerint frissültek")
    st.markdown(f"- **🗺️ GPS koordináták:** {coord_count}/{len(filtered_df)} ingatlanhoz érhetőek el térképes megjelenítéshez")

def create_interactive_map(df, location_name):
    """🗺️ INTERAKTÍV TÉRKÉP - GPS koordináták alapján"""
    
    # Koordináta oszlopok ellenőrzése
    has_coordinates = all(col in df.columns for col in ['geo_latitude', 'geo_longitude'])
    
    if not has_coordinates:
        st.warning("⚠️ Nincs GPS koordináta adat a térképhez. Koordináták nélküli CSV betöltve.")
        return
    
    # Koordinátákkal rendelkező rekordok szűrése
    map_df = df.dropna(subset=['geo_latitude', 'geo_longitude']).copy()
    
    if map_df.empty:
        st.warning("⚠️ Nincsenek érvényes GPS koordináták az aktuális szűréshez.")
        return
    
    st.markdown("---")
    st.markdown("## 🗺️ **INTERAKTÍV TÉRKÉP**")
    st.markdown(f"**📍 Lokáció:** {location_name} | **🏠 Ingatlanok:** {len(map_df)} db GPS koordinátával")
    
    # Térkép alapbeállítások
    center_lat = map_df['geo_latitude'].mean()
    center_lng = map_df['geo_longitude'].mean()
    
    # Folium térkép létrehozása
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Színkódolás ár szerint
    def get_price_color(price):
        if pd.isna(price):
            return '#95A5A6'  # Szürke - nincs ár adat
        elif price <= 100:
            return '#2ECC71'  # Zöld - olcsó (≤100M)
        elif price <= 200:
            return '#F39C12'  # Narancssárga - közepes (101-200M)
        elif price <= 300:
            return '#E74C3C'  # Piros - drága (201-300M)
        else:
            return '#8E44AD'  # Lila - nagyon drága (300M+)
    
    # Enhanced lokáció oszlop meghatározása (már nem használjuk színkódolásra)
    district_col = 'enhanced_keruleti_resz' if 'enhanced_keruleti_resz' in map_df.columns else 'varosresz_kategoria'
    
    # Markerek hozzáadása
    for idx, row in map_df.iterrows():
        # Popup tartalom
        price = row.get('teljes_ar_millió', 'N/A')
        popup_content = f"""
        <b>{row.get('cim', 'N/A')}</b><br/>
        💰 Ár: {row.get('teljes_ar', 'N/A')}<br/>
        📏 Terület: {row.get('terulet', 'N/A')}<br/>
        🛏️ Szobák: {row.get('szobak', 'N/A')}<br/>
        🔧 Állapot: {row.get('ingatlan_allapota', 'N/A')}<br/>
        👨‍👩‍👧‍👦 Családbarát pont: {row.get('csaladbarati_pontszam', 0):.0f}<br/>
        🏢 Városrész: {row.get(district_col, 'N/A')}
        """
        
        # Marker hozzáadása
        folium.Marker(
            location=[row['geo_latitude'], row['geo_longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=f"{row.get('cim', 'N/A')} - {row.get('teljes_ar', 'N/A')}",
            icon=folium.Icon(color='white', icon_color=get_price_color(price))
        ).add_to(m)
    
    # Térkép megjelenítése Streamlit-ben
    st_folium(m, width=900, height=500, key=f"map_{location_name.lower().replace(' ', '_')}")

if __name__ == "__main__":
    main()
