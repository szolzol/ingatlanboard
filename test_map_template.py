"""
STREAMLIT DASHBOARD - XII. KERÜLET (KOORDINÁTÁS TÉRKÉP TESZT)
============================================================

Teszteli a bővített streamlit template-t a koordinátás XII. kerületi adatokkal
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

# XII. kerület lokáció beállítás
def get_location_from_filename():
    """XII. kerület fix lokáció név"""
    return "XII. KERÜLET (TÉRKÉP TESZT)"

location_name = get_location_from_filename()
timestamp = datetime.now().strftime("%Y.%m.%d %H:%M")

# Streamlit konfiguráció
st.set_page_config(
    page_title=f"Ingatlan Dashboard - {location_name} - {timestamp}",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_and_process_data():
    """XII. kerületi koordinátás CSV betöltése"""
    try:
        # XII. kerületi koordinátás CSV keresése
        coord_files = glob.glob("ingatlan_reszletes_XII_KERÜLET_koordinatak_*.csv")
        
        if not coord_files:
            st.error("❌ Nincs XII. kerületi koordinátás CSV fájl!")
            return pd.DataFrame()
        
        # Legfrissebb fájl
        latest_file = max(coord_files, key=os.path.getmtime)
        st.info(f"📂 Koordinátás CSV: {latest_file}")
        
        # CSV betöltése
        df = pd.read_csv(latest_file, encoding='utf-8', sep='|', on_bad_lines='skip')
        st.success(f"✅ Betöltve: {len(df)} rekord, {len(df.columns)} oszlop")
        
        # Koordináta ellenőrzés
        coord_count = df[['geo_latitude', 'geo_longitude']].notna().all(axis=1).sum()
        st.info(f"🗺️ Koordinátával: {coord_count}/{len(df)} rekord")
        
        # Numerikus konverziók
        df['teljes_ar_millió'] = df['teljes_ar'].apply(parse_million_ft)
        df['terulet_szam'] = df['terulet'].apply(parse_area)
        df['szobak_szam'] = df['szobak'].apply(parse_rooms)
        
        return df
        
    except Exception as e:
        st.error(f"❌ Betöltési hiba: {e}")
        return pd.DataFrame()

def parse_million_ft(text):
    """Millió Ft konverzió"""
    if pd.isna(text):
        return None
    
    text = str(text).lower().replace(',', '.').replace(' ', '')
    
    try:
        if 'mrd' in text or 'milliárd' in text:
            number = float(re.findall(r'[0-9.,]+', text)[0])
            return number * 1000
        elif 'm ft' in text or 'millió' in text:
            number = float(re.findall(r'[0-9.,]+', text)[0])
            return number
        else:
            # Ha csak szám van (pl. "125000000"), akkor elosztjuk millióval
            if text.replace('.', '').isdigit():
                return float(text) / 1_000_000
            return None
    except:
        return None

def parse_area(text):
    """Terület szám kinyerése"""
    if pd.isna(text):
        return None
    try:
        numbers = re.findall(r'\d+', str(text))
        return int(numbers[0]) if numbers else None
    except:
        return None

def parse_rooms(text):
    """Szobaszám kinyerése"""
    if pd.isna(text):
        return None
    try:
        # Formátumok: "3+1", "4", "1+1", stb.
        text = str(text).replace(' ', '')
        if '+' in text:
            parts = text.split('+')
            return int(parts[0]) + 1  # Nappali + hálószobák
        else:
            numbers = re.findall(r'\d+', text)
            return int(numbers[0]) if numbers else None
    except:
        return None

def create_interactive_map(df, location_name):
    """🗺️ INTERAKTÍV TÉRKÉP - GPS koordináták alapján"""
    
    # Koordináta oszlopok ellenőrzése
    has_coordinates = all(col in df.columns for col in ['geo_latitude', 'geo_longitude'])
    
    if not has_coordinates:
        st.warning("🗺️ Térképes megjelenítés nem elérhető - nincs GPS koordináta az adatokban")
        return
    
    # Koordinátákkal rendelkező rekordok szűrése
    map_df = df.dropna(subset=['geo_latitude', 'geo_longitude']).copy()
    
    if map_df.empty:
        st.warning("🗺️ Térképes megjelenítés nem elérhető - nincs GPS adat a rekordokban")
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
    
    # Színkódolás enhanced lokáció szerint
    district_colors = {
        'Orbánhegy': '#FF6B6B',      # Piros
        'Svábhegy': '#4ECDC4',       # Türkiz  
        'Virányos': '#45B7D1',       # Kék
        'Krisztinaváros': '#96CEB4', # Zöld
        'Zugliget': '#FECA57',       # Sárga
        'Rózsadomb': '#FF9FF3',      # Pink
        'Ismeretlen': '#95A5A6'      # Szürke
    }
    
    # Enhanced lokáció oszlop meghatározása
    district_col = 'enhanced_keruleti_resz' if 'enhanced_keruleti_resz' in map_df.columns else 'varosresz_kategoria'
    
    # Markerek hozzáadása
    for idx, row in map_df.iterrows():
        try:
            # Ingatlan adatok
            lat = float(row['geo_latitude'])
            lng = float(row['geo_longitude'])
            cim = row.get('cim', 'N/A')[:50]
            ar = row.get('teljes_ar', 'N/A')
            terulet = row.get('terulet', 'N/A')
            allapot = row.get('ingatlan_allapota', 'N/A')
            url = row.get('link', '#')
            district = row.get(district_col, 'Ismeretlen')
            
            # Nettó pontszám (Enhanced AI feature)
            netto_pont = row.get('netto_szoveg_pont', 0)
            
            # Színkód meghatározása
            color = district_colors.get(district, '#95A5A6')
            
            # Tooltip HTML tartalma
            tooltip_html = f"""
            <div style='width: 250px; font-family: Arial;'>
                <h4 style='margin: 0; color: #2E86AB;'>🏠 {cim}</h4>
                <hr style='margin: 5px 0;'>
                <p style='margin: 2px 0;'><b>💰 Ár:</b> {ar}</p>
                <p style='margin: 2px 0;'><b>📐 Terület:</b> {terulet}</p>
                <p style='margin: 2px 0;'><b>🏗️ Állapot:</b> {allapot}</p>
                <p style='margin: 2px 0;'><b>🗺️ Lokáció:</b> {district}</p>
                <p style='margin: 2px 0;'><b>⭐ AI Pontszám:</b> {netto_pont:.1f}</p>
                <p style='margin: 5px 0;'><a href='{url}' target='_blank' style='color: #2E86AB;'>🔗 Részletek</a></p>
            </div>
            """
            
            # Marker hozzáadása
            folium.CircleMarker(
                location=[lat, lng],
                radius=8,
                popup=folium.Popup(tooltip_html, max_width=300),
                tooltip=f"{cim} - {ar}",
                color='white',
                weight=2,
                fillColor=color,
                fillOpacity=0.8
            ).add_to(m)
            
        except Exception as e:
            st.warning(f"Marker hiba: {e}")
            continue
    
    # Legenda hozzáadása
    legend_html = f"""
    <div style='position: fixed; 
                top: 10px; right: 10px; width: 180px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px'>
    <h4 style='margin-top:0;'>🗺️ Kerületi Részek</h4>
    """
    
    # District statisztikák a legendához
    if district_col in map_df.columns:
        district_stats = map_df[district_col].value_counts()
        for district, count in district_stats.items():
            color = district_colors.get(district, '#95A5A6')
            legend_html += f"""
            <p style='margin: 3px 0;'>
                <span style='color:{color}; font-size: 16px;'>●</span> 
                {district}: {count} db
            </p>
            """
    
    legend_html += """
    <hr style='margin: 8px 0;'>
    <p style='margin: 3px 0; font-size: 10px;'>
        🔗 Kattints a markerekre<br/>részletes információkért
    </p>
    </div>
    """
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Térkép megjelenítése Streamlit-ben
    st_folium(m, width=900, height=500)
    
    # Térkép statisztikák
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📍 Térképen", f"{len(map_df)} ingatlan")
    with col2:
        st.metric("🎯 Térkép központ", f"{center_lat:.4f}, {center_lng:.4f}")
    with col3:
        if district_col in map_df.columns:
            top_district = map_df[district_col].value_counts().index[0]
            top_count = map_df[district_col].value_counts().iloc[0]
            st.metric("🏆 Legnépszerűbb", f"{top_district} ({top_count} db)")

def main():
    """Térkép teszt alkalmazás"""
    
    st.title("🗺️ XII. KERÜLET - INTERAKTÍV TÉRKÉP TESZT")
    st.markdown("**Koordinátás térkép a frissen bővített XII. kerületi adatokkal**")
    
    # Adatok betöltése
    df = load_and_process_data()
    if df.empty:
        st.error("❌ Nincs adat a térkép megjelenítéséhez!")
        return
    
    # Enhanced lokáció statisztikák
    if 'enhanced_keruleti_resz' in df.columns:
        st.markdown("### 🏘️ Enhanced Lokáció Megoszlás:")
        district_counts = df['enhanced_keruleti_resz'].value_counts()
        
        col1, col2 = st.columns(2)
        with col1:
            for i, (district, count) in enumerate(district_counts.head(4).items()):
                percent = count/len(df)*100
                st.metric(f"{district}", f"{count} db ({percent:.1f}%)")
        
        with col2:
            for i, (district, count) in enumerate(district_counts.tail(3).items()):
                percent = count/len(df)*100
                st.metric(f"{district}", f"{count} db ({percent:.1f}%)")
    
    # Interaktív térkép megjelenítése
    create_interactive_map(df, location_name)
    
    # Enhanced AI features statisztikák
    if 'netto_szoveg_pont' in df.columns:
        st.markdown("### ⭐ Enhanced AI Pontszám Statisztikák:")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Átlag", f"{df['netto_szoveg_pont'].mean():.1f}")
        with col2:
            st.metric("🏆 Maximum", f"{df['netto_szoveg_pont'].max():.1f}")
        with col3:
            st.metric("📉 Minimum", f"{df['netto_szoveg_pont'].min():.1f}")
        with col4:
            top_10_pct = (df['netto_szoveg_pont'] > df['netto_szoveg_pont'].quantile(0.9)).sum()
            st.metric("🌟 Top 10%", f"{top_10_pct} ingatlan")

if __name__ == "__main__":
    main()
