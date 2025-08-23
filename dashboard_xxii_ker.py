"""
STREAMLIT DASHBOARD - XXII KERÜLET INGATLAN ELEMZÉS (GPS koordinátákkal)
========================================================================

🎯 Egyedi dashboard XXII kerületi ingatlanokhoz koordináta alapú térképpel
📊 Adatforrás: ingatlan_reszletes_xxii_ker_20250823_011409_koordinatak_20250823_101741.csv
⚡ Template alapján generálva - dinamikus időbélyeg + fix lokáció
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import folium
from streamlit_folium import st_folium
import glob
import re
import warnings
import os
from datetime import datetime

warnings.filterwarnings('ignore')

# FIX lokáció és timestamp
def get_location_from_filename():
    """Fix location név visszaadása"""
    return "XXII. KERÜLET"

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
    """Adatok betöltése és feldolgozása - XXII kerületi koordinátás CSV"""
    try:
        # Koordinátás CSV pattern keresés - XXII kerület specifikus
        location_patterns = [
            "ingatlan_reszletes_xxii_ker_*_koordinatak_*.csv",  # Koordinátás változat prioritás
            "ingatlan_reszletes_xxii_ker_*.csv",                # Fallback basic
            "ingatlan_*xxii_ker*.csv"                           # Wildcard fallback
        ]
        
        # Fix lokáció pattern keresés - mindig a legfrissebb koordinátás CSV-t választja
        for pattern in location_patterns:
            matching_files = glob.glob(pattern)
            if matching_files:
                latest_file = max(matching_files, key=lambda x: os.path.getmtime(x))
                st.info(f"📂 Betöltött adatforrás: **{latest_file}** ({len(matching_files)} találat közül)")
                
                # CSV betöltés pipe elválasztóval
                df = pd.read_csv(latest_file, sep='|', encoding='utf-8')
                
                # Adatfeldolgozás
                df['teljes_ar_millió'] = df['teljes_ar'].apply(parse_million_ft)
                df['terulet_szam'] = df['terulet'].apply(parse_area)
                df['szobak_szam'] = df['szobak'].apply(parse_rooms)
                
                # Családbarát pontszám számítása
                df['csaladbarati_pontszam'] = df.apply(create_family_score, axis=1)
                
                # Modern pontszám hozzáadása ha létezik
                if 'netto_szoveg_pont' in df.columns:
                    df['modern_netto_pont'] = df['netto_szoveg_pont']
                else:
                    df['modern_netto_pont'] = 0
                
                return df
        
        # Ha egyik pattern sem működött
        st.error("HIBA: Nincs található XXII kerületi CSV fájl!")
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
            return str(row['link'])
        # Fallback: generált URL (de ez nem lesz pontos)
        elif pd.notna(row.get('id')):
            return f"https://ingatlan.com/elado+haz/{int(row['id'])}"
        return None
    except (KeyError, AttributeError, TypeError):
        # Ha valami hiba lenne, fallback
        if pd.notna(row.get('id')):
            return f"https://ingatlan.com/elado+haz/{int(row['id'])}"
        return None

def main():
    """Főalkalmazás"""
    
    # Fejléc
    st.title(f"👨‍👩‍👧‍👦 Ingatlan Dashboard - {location_name} - {timestamp}")
    st.markdown("**3 gyerekes családok számára optimalizált ingatlankeresés - GPS térképpel**")
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
            st.sidebar.write(f"💰 **Ár:** {min_price:.1f} M Ft")
            price_range = (min_price, max_price)
        else:
            price_range = st.sidebar.slider(
                "💰 Ár (M Ft)", 
                min_value=min_price, 
                max_value=max_price, 
                value=(min_price, max_price),
                step=5.0
            )
    else:
        price_range = None
    
    # Terület szűrő
    if 'terulet_szam' in df.columns and df['terulet_szam'].notna().any():
        min_area = int(df['terulet_szam'].min())
        max_area = int(df['terulet_szam'].max())
        
        # Ha min és max azonos, akkor nem csinálunk slider-t
        if min_area == max_area:
            st.sidebar.write(f"📐 **Terület:** {min_area} m²")
            area_range = (min_area, max_area)
        else:
            area_range = st.sidebar.slider(
                "📐 Terület (m²)", 
                min_value=min_area, 
                max_value=max_area, 
                value=(min_area, max_area),
                step=10
            )
    else:
        area_range = None
    
    # Szobaszám szűrő
    if 'szobak_szam' in df.columns and df['szobak_szam'].notna().any():
        min_rooms = int(df['szobak_szam'].min())
        max_rooms = int(df['szobak_szam'].max())
        
        # Ha min és max azonos, akkor nem csinálunk slider-t
        if min_rooms == max_rooms:
            st.sidebar.write(f"🏠 **Szobaszám:** {min_rooms}")
            rooms_range = (min_rooms, max_rooms)
        else:
            rooms_range = st.sidebar.slider(
                "🏠 Szobaszám", 
                min_value=min_rooms, 
                max_value=max_rooms, 
                value=(min_rooms, max_rooms)
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
            (filtered_df['szobak_szam'].isna()) |  # Megtartjuk a NaN értékeket
            ((filtered_df['szobak_szam'] >= rooms_range[0]) &
             (filtered_df['szobak_szam'] <= rooms_range[1]))
        ]
    
    if selected_conditions:
        filtered_df = filtered_df[filtered_df['ingatlan_allapota'].isin(selected_conditions)]
    
    if filter_green:
        filtered_df = filtered_df[filtered_df.get('van_zold_energia', False) == True]
    if filter_wellness:
        filtered_df = filtered_df[filtered_df.get('van_wellness_luxury', False) == True]
    if filter_smart:
        filtered_df = filtered_df[filtered_df.get('van_smart_tech', False) == True]
    if filter_premium:
        filtered_df = filtered_df[filtered_df.get('van_premium_design', False) == True]
    
    # Eredmények megjelenítése
    st.header(f"🏠 Találatok: {len(filtered_df)} ingatlan")
    
    if len(filtered_df) == 0:
        st.warning("Nincs a szűrőknek megfelelő ingatlan. Próbáljon lazítani a feltételeken!")
        return
    
    # Általános statisztikák
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_price = filtered_df['teljes_ar_millió'].mean()
        st.metric("💰 Átlagár", f"{avg_price:.1f} M Ft")
    
    with col2:
        avg_area = filtered_df['terulet_szam'].mean()
        st.metric("📐 Átlag terület", f"{avg_area:.0f} m²")
    
    with col3:
        avg_rooms = filtered_df['szobak_szam'].mean()
        st.metric("🏠 Átlag szobaszám", f"{avg_rooms:.1f}")
    
    with col4:
        avg_family_score = filtered_df['csaladbarati_pontszam'].mean()
        st.metric("👨‍👩‍👧‍👦 Átlag családbarát pont", f"{avg_family_score:.1f}")
    
    # Top 5 legjobb ingatlan
    st.header("🏆 TOP 5 Legcsaládbarátabb Ingatlan")
    
    top_5 = filtered_df.nlargest(5, 'csaladbarati_pontszam')
    
    for idx, (_, row) in enumerate(top_5.iterrows(), 1):
        # URL generálása
        ingatlan_url = generate_ingatlan_url(row)
        title_text = f"#{idx} - {row.get('cim', 'Cím hiányzik')} - {row['csaladbarati_pontszam']:.1f} pont"
        
        # Link hozzáadása ha van URL
        if ingatlan_url:
            title_with_link = f"{title_text} | [🔗 Megtekintés]({ingatlan_url})"
        else:
            title_with_link = title_text
            
        with st.expander(title_with_link):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"💰 **Ár:** {row.get('teljes_ar', 'N/A')}")
                st.write(f"📐 **Terület:** {row.get('terulet', 'N/A')}")
                st.write(f"🏠 **Szobák:** {row.get('szobak', 'N/A')}")
                st.write(f"🔧 **Állapot:** {row.get('ingatlan_allapota', 'N/A')}")
            
            with col2:
                st.write(f"📊 **Családbarát pont:** {row['csaladbarati_pontszam']:.1f}")
                if 'modern_netto_pont' in row.index and pd.notna(row['modern_netto_pont']):
                    st.write(f"⭐ **Modern pont:** {row['modern_netto_pont']:.1f}")
                
                # GPS koordináták megjelenítése ha vannak
                if 'geo_latitude' in row.index and pd.notna(row['geo_latitude']):
                    st.write(f"🗺️ **GPS:** ({row['geo_latitude']:.4f}, {row['geo_longitude']:.4f})")

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
    
    # Modern funkciók eloszlás
    if all(col in filtered_df.columns for col in ['van_zold_energia', 'van_wellness_luxury', 'van_smart_tech', 'van_premium_design']):
        modern_stats = {
            'Zöld Energia': filtered_df['van_zold_energia'].sum(),
            'Wellness & Luxury': filtered_df['van_wellness_luxury'].sum(),
            'Smart Technology': filtered_df['van_smart_tech'].sum(),
            'Premium Design': filtered_df['van_premium_design'].sum()
        }
        
        fig3 = px.bar(
            x=list(modern_stats.keys()),
            y=list(modern_stats.values()),
            title="Modern Funkciók Gyakorisága a Szűrt Ingatlanoknál"
        )
        st.plotly_chart(fig3, use_container_width=True)
    
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
        """Valódi ingatlan.com ID kinyerése a linkből"""
        try:
            if pd.notna(link) and 'ingatlan.com' in str(link):
                match = re.search(r'/(\d+)/?$', str(link))
                return match.group(1) if match else 'N/A'
            return 'N/A'
        except:
            return 'N/A'
    
    # Hozzáadjuk a valódi ID-t - JAVÍTOTT verzió Streamlit-kompatibilis
    display_df_with_links = []
    for idx, (_, row) in enumerate(display_df.iterrows(), 1):
        # URL generálása ugyanúgy, mint a TOP 5-ben
        ingatlan_url = generate_ingatlan_url(row)
        ingatlan_id = extract_ingatlan_id(row.get('link'))
        
        row_data = {
            'Ingatlan ID': ingatlan_id,
            'URL': ingatlan_url if ingatlan_url else 'N/A',
            'Cím': row.get('cim', 'N/A'),
            'Ár': row.get('teljes_ar', 'N/A'),
            'Terület': row.get('terulet', 'N/A'),
            'Szobák': row.get('szobak', 'N/A'),
            'Állapot': row.get('ingatlan_allapota', 'N/A'),
            'Családbarát Pont': f"{row.get('csaladbarati_pontszam', 0):.1f}"
        }
        
        # Modern pont hozzáadása, ha létezik
        if 'modern_netto_pont' in row.index and pd.notna(row['modern_netto_pont']):
            row_data['Modern Pont'] = f"{row['modern_netto_pont']:.1f}"
            
        display_df_with_links.append(row_data)
    
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
    st.markdown(f"- Az adatok GPS koordinátákkal bővítve: {timestamp} állapot szerint frissültek")

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
    
    # Színkódolás ár szerint
    def get_price_color(price):
        """Ár alapú színkódolás"""
        if pd.isna(price):
            return 'gray'
        elif price <= 100:
            return 'green'
        elif price <= 200:
            return 'orange'
        elif price <= 300:
            return 'red'
        else:
            return 'purple'
    
    # Markerek hozzáadása
    for idx, row in map_df.iterrows():
        try:
            lat = row['geo_latitude']
            lng = row['geo_longitude']
            
            # Popup tartalma
            popup_content = f"""
            <b>{row.get('cim', 'Cím hiányzik')}</b><br>
            💰 Ár: {row.get('teljes_ar', 'N/A')}<br>
            📐 Terület: {row.get('terulet', 'N/A')}<br>
            🏠 Szobák: {row.get('szobak', 'N/A')}<br>
            🔧 Állapot: {row.get('ingatlan_allapota', 'N/A')}<br>
            👨‍👩‍👧‍👦 Családbarát pont: {row.get('csaladbarati_pontszam', 0):.1f}<br>
            🗺️ GPS: ({lat:.4f}, {lng:.4f})
            """
            
            # URL hozzáadása ha van
            ingatlan_url = generate_ingatlan_url(row)
            if ingatlan_url:
                popup_content += f"<br><a href='{ingatlan_url}' target='_blank'>🔗 Megtekintés</a>"
            
            folium.Marker(
                [lat, lng],
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color=get_price_color(row.get('teljes_ar_millió')), icon='home')
            ).add_to(m)
            
        except Exception as e:
            continue
    
    # Legenda hozzáadása - ár alapú színkódolás
    legend_html = f"""
    <div style='position: fixed; 
                top: 10px; right: 10px; width: 180px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px'>
    <h4 style='margin-top:0;'>🏠 Árszínkódolás</h4>
    <p style='margin: 3px 0;'>
        <span style='color:#2ECC71; font-size: 16px;'>●</span> 
        ≤100 M Ft: olcsó
    </p>
    <p style='margin: 3px 0;'>
        <span style='color:#F39C12; font-size: 16px;'>●</span> 
        101-200 M Ft: közepes
    </p>
    <p style='margin: 3px 0;'>
        <span style='color:#E74C3C; font-size: 16px;'>●</span> 
        201-300 M Ft: drága
    </p>
    <p style='margin: 3px 0;'>
        <span style='color:#8E44AD; font-size: 16px;'>●</span> 
        300+ M Ft: nagyon drága
    </p>
    <p style='margin: 3px 0;'>
        <span style='color:#95A5A6; font-size: 16px;'>●</span> 
        Nincs ár adat
    </p>
    <hr style='margin: 8px 0;'>
    <p style='margin: 3px 0; font-size: 10px;'>
        🔗 Kattints a markerekre<br/>részletes információkért
    </p>
    </div>
    """
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Térkép megjelenítése Streamlit-ben
    st_folium(m, width=900, height=500, key=f"map_{location_name.lower().replace(' ', '_').replace('.', '')}")

if __name__ == "__main__":
    main()
