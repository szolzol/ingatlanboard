"""
STREAMLIT DASHBOARD TEMPLATE - INGATLAN ELEMZÉS
===============================================

🎯 HASZNÁLAT:
1. Másold le ezt a template fájlt új névvel (pl. dashboard_location.py)
2. Cseréld le a TEMPLATE placeholder-eket:
   - XI. KERÜLET -> "TÖRÖKBÁLINT-TÜKÖRHEGY", "XII. KERÜLET", stb.
   - ingatlan_reszletes_xi_ker_*.csv, ingatlan_lista_xi_ker_*.csv, ingatlan_reszletes_xi_ker_*_koordinatak_*.csv -> konkrét CSV pattern-ek

📋 PÉLDA CSERÉK:
- Törökbálint-Tükörhegy esetén:
  XI. KERÜLET -> "TÖRÖKBÁLINT-TÜKÖRHEGY"
  ingatlan_reszletes_xi_ker_*.csv -> "ingatlan_reszletes_torokbalint_tukorhegy_*.csv"
  
- XII. kerület esetén:
  XI. KERÜLET -> "XII. KERÜLET" 
  ingatlan_reszletes_xi_ker_*.csv -> "ingatlan_reszletes_*xii_ker*.csv"

⚡ Fix lokáció + dinamikus időbélyeg = deployment stable + auto-update!
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

# TEMPLATE PLACEHOLDER - Location név és CSV pattern
# Ezt a részt kell módosítani egyedi dashboard generálásnál
def get_location_from_filename():
    """Fix location név visszaadása - ezt módosítani kell egyedi dashboard-oknál"""
    return "XI. KERÜLET"  # TEMPLATE: pl. "TÖRÖKBÁLINT-TÜKÖRHEGY", "XII. KERÜLET", "BUDAÖRS"

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
    """Adatok betöltése és feldolgozása - TEMPLATE: fix lokáció, dinamikus időbélyeg"""
    try:
        # TEMPLATE PLACEHOLDER - CSV lokáció pattern
        # Ezt a részt kell módosítani egyedi dashboard generálásnál
        location_patterns = [
            "ingatlan_reszletes_xi_ker_*.csv",  # TEMPLATE: pl. "ingatlan_reszletes_torokbalint_tukorhegy_*.csv"
            "ingatlan_lista_xi_ker_*.csv",  # TEMPLATE: pl. "ingatlan_modern_enhanced_budaors_*.csv" 
            "ingatlan_reszletes_xi_ker_*_koordinatak_*.csv"   # TEMPLATE: pl. "ingatlan_reszletes_*budaors*.csv"
        ]
        
        # Fix lokáció pattern keresés - mindig a legfrissebb CSV-t választja
        for pattern in location_patterns:
            if pattern.startswith("{{") and pattern.endswith("}}"):
                continue  # Skip template placeholders
                
            matching_files = glob.glob(pattern)
            if matching_files:
                # Legfrissebb fájl kiválasztása időbélyeg alapján (fájl módosítás ideje szerint)
                latest_file = max(matching_files, key=lambda f: os.path.getmtime(f))
                print(f"📊 Legfrissebb CSV betöltése ({pattern}): {latest_file}")
                
                df = pd.read_csv(latest_file, encoding='utf-8-sig', sep='|')
                
                # Ellenőrizzük, hogy sikerült-e betölteni
                if df.empty:
                    continue  # Próbáljuk a következő pattern-t
                
                print(f"✅ Sikeresen betöltve: {len(df)} sor")
                
                # Numerikus konverziók
                df['teljes_ar_millió'] = df['teljes_ar'].apply(parse_million_ft)
                df['terulet_szam'] = df['terulet'].apply(parse_area)
                df['szobak_szam'] = df['szobak'].apply(parse_rooms)
                
                # Családbarát pontszám számítása
                df['csaladbarati_pontszam'] = df.apply(create_family_score, axis=1)
                
                return df
        
        # Ha egyik pattern sem működött
        st.error("HIBA: Nincs található CSV fájl a megadott pattern-ekhez!")
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

def create_clickable_link(text, url):
    """Kattintható link létrehozása Streamlit-ben"""
    if url:
        return f"[{text}]({url})"
    return text

def main():
    """Főalkalmazás"""
    
    # Fejléc
    st.title(f"👨‍👩‍👧‍👦 Ingatlan Dashboard - {location_name} - {timestamp}")
    st.markdown("**Több gyerekes családok számára optimalizált ingatlankeresés**")
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
                value=(min_area, max_area),  # VÁLTOZÁS: teljes tartomány alapértelmezett
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
                value=(min_rooms, max_rooms)  # VÁLTOZÁS: teljes tartomány alapértelmezett
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
        # Átlagos m² ár számítása
        valid_data = filtered_df.dropna(subset=['teljes_ar_millió', 'terulet_szam'])
        if not valid_data.empty:
            avg_price_per_sqm = (valid_data['teljes_ar_millió'] * 1000000 / valid_data['terulet_szam']).mean()
            st.metric("� Átlagos m² ár", f"{avg_price_per_sqm:,.0f} Ft/m²")
        else:
            st.metric("💰 Átlagos m² ár", "N/A")

    # 🗺️ INTERAKTÍV TÉRKÉP - szűrt adatokkal
    create_interactive_map(filtered_df, location_name)
    
    # Vizualizációk
    st.header("📊 Vizualizációk")
        
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
        column_labels['szobak_szam'] = 'Szobaszám'
    
    if 'csaladbarati_pontszam' in filtered_df.columns:
        numeric_columns.append('csaladbarati_pontszam')
        column_labels['csaladbarati_pontszam'] = 'Családbarát Pont'
    
    if 'modern_netto_pont' in filtered_df.columns:
        numeric_columns.append('modern_netto_pont')
        column_labels['modern_netto_pont'] = 'Modern Pont'
    
    if 'kepek_szama' in filtered_df.columns:
        numeric_columns.append('kepek_szama')
        column_labels['kepek_szama'] = 'Képek Száma'
    
    # Modern funkciók (boolean -> numeric)
    modern_features = ['van_zold_energia', 'van_wellness_luxury', 'van_smart_tech', 'van_premium_design']
    for feature in modern_features:
        if feature in filtered_df.columns:
            numeric_columns.append(feature)
            feature_labels = {
                'van_zold_energia': 'Zöld Energia (0/1)',
                'van_wellness_luxury': 'Wellness (0/1)',
                'van_smart_tech': 'Smart Tech (0/1)',
                'van_premium_design': 'Premium Design (0/1)'
            }
            column_labels[feature] = feature_labels.get(feature, feature)
    
    # Kategorikus változók számérték konverziója
    categorical_vars = []
    if 'ingatlan_allapota' in filtered_df.columns:
        # Állapot numerikus értékké - javított mapping
        condition_mapping = {'újépítésű': 5, 'új': 5, 'újszerű': 5, 'felújított': 4, 'kitűnő': 4, 'jó': 3, 'közepes': 2, 'felújítandó': 1, 'rossz': 1}
        if 'allapot_numeric' not in filtered_df.columns:
            filtered_df = filtered_df.copy()
            def map_condition_improved(x):
                if pd.notna(x):
                    x_str = str(x).lower()
                    matched_values = []
                    for key, value in condition_mapping.items():
                        if key.lower() in x_str:
                            matched_values.append(value)
                    if matched_values:
                        return max(matched_values)
                    else:
                        return 2  # Default középérték
                return 2
            filtered_df['allapot_numeric'] = filtered_df['ingatlan_allapota'].apply(map_condition_improved)
        numeric_columns.append('allapot_numeric')
        column_labels['allapot_numeric'] = 'Állapot (1=rossz, 5=új)'
        categorical_vars.append('allapot_numeric')
    
    if 'hirdeto_tipus' in filtered_df.columns:
        if 'hirdeto_numeric' not in filtered_df.columns:
            filtered_df = filtered_df.copy()
            # Hirdető típus: 1=magánszemély, 2=ingatlaniroda - javított mapping
            def map_hirdeto_improved(x):
                if pd.notna(x):
                    x_str = str(x).lower()
                    if 'maganszemely' in x_str or 'magán' in x_str:
                        return 1
                    elif 'ingatlaniroda' in x_str or 'iroda' in x_str:
                        return 2
                    else:
                        return 1  # Default: magánszemély, mert ritkább
                return 1
            filtered_df['hirdeto_numeric'] = filtered_df['hirdeto_tipus'].apply(map_hirdeto_improved)
        numeric_columns.append('hirdeto_numeric')
        column_labels['hirdeto_numeric'] = 'Hirdető (1=magán, 2=iroda)'
        categorical_vars.append('hirdeto_numeric')
    
    if len(numeric_columns) > 0 and 'teljes_ar_millió' in filtered_df.columns:
        # Felhasználói választás a magyarázó változóra
        explanatory_var = st.selectbox(
            "📊 Válassz magyarázó változót (X tengely)",
            options=numeric_columns,
            index=0,
            format_func=lambda x: column_labels.get(x, x)
        )
        
        if explanatory_var:
            # Scatter plot
            fig_scatter = px.scatter(
                filtered_df.dropna(subset=[explanatory_var, 'teljes_ar_millió']),
                x=explanatory_var,
                y='teljes_ar_millió',
                color='csaladbarati_pontszam' if 'csaladbarati_pontszam' in filtered_df.columns else None,
                title=f"Teljes Ár vs. {column_labels.get(explanatory_var, explanatory_var)}",
                labels={
                    explanatory_var: column_labels.get(explanatory_var, explanatory_var),
                    'teljes_ar_millió': 'Teljes Ár (M Ft)',
                    'csaladbarati_pontszam': 'Családbarát Pont'
                },
                hover_data=['cim'] if 'cim' in filtered_df.columns else None
            )
            
            # Trendvonal hozzáadása
            import numpy as np
            clean_data = filtered_df.dropna(subset=[explanatory_var, 'teljes_ar_millió'])
            if len(clean_data) > 1:
                x_vals = clean_data[explanatory_var].values
                y_vals = clean_data['teljes_ar_millió'].values
                
                # Manuális lineáris regresszió
                n = len(x_vals)
                sum_x = np.sum(x_vals)
                sum_y = np.sum(y_vals)
                sum_xy = np.sum(x_vals * y_vals)
                sum_x2 = np.sum(x_vals * x_vals)
                
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                intercept = (sum_y - slope * sum_x) / n
                
                # R² számítás
                y_pred = slope * x_vals + intercept
                ss_res = np.sum((y_vals - y_pred) ** 2)
                ss_tot = np.sum((y_vals - np.mean(y_vals)) ** 2)
                r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                
                # Trendvonal
                x_trend = [clean_data[explanatory_var].min(), clean_data[explanatory_var].max()]
                y_trend = [slope * x + intercept for x in x_trend]
                
                fig_scatter.add_scatter(
                    x=x_trend, y=y_trend, mode='lines', name=f'Trendvonal (R²={r_squared:.3f})',
                    line=dict(color='red', dash='dash')
                )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Korrelációs statisztika
            correlation = filtered_df[explanatory_var].corr(filtered_df['teljes_ar_millió'])
            st.metric(
                f"Korreláció: {column_labels.get(explanatory_var, explanatory_var)} ↔ Ár",
                f"{correlation:.3f}"
            )
            
            # Interpretáció
            if abs(correlation) > 0.7:
                strength = "erős"
            elif abs(correlation) > 0.4:
                strength = "közepes"
            elif abs(correlation) > 0.2:
                strength = "gyenge"
            else:
                strength = "nagyon gyenge"
            
            direction = "pozitív" if correlation > 0 else "negatív"
            st.write(f"**Interpretáció:** {strength} {direction} kapcsolat az ár és a {column_labels.get(explanatory_var, explanatory_var).lower()} között.")
    else:
        st.warning("Nincs elég numerikus változó az elemzéshez, vagy hiányzik az ár adat.")
    
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
        condition_stats = filtered_df['ingatlan_allapota'].value_counts()
        for condition, count in condition_stats.head(5).items():
            categorical_cols.append('Állapot')
            categorical_data.append({
                'Kategória': condition,
                'Darabszám': count,
                'Arány (%)': round(count / len(filtered_df) * 100, 1),
                'Átlag Ár (M Ft)': round(filtered_df[filtered_df['ingatlan_allapota'] == condition]['teljes_ar_millió'].mean(), 1),
                'Átlag Családbarát Pont': round(filtered_df[filtered_df['ingatlan_allapota'] == condition]['csaladbarati_pontszam'].mean(), 1)
            })
    
    # Modern funkciók elemzése
    modern_features = ['van_zold_energia', 'van_wellness_luxury', 'van_smart_tech', 'van_premium_design']
    feature_names = ['🌞 Zöld Energia', '🏊 Wellness & Luxury', '🏠 Smart Technology', '💎 Premium Design']
    
    for feature, name in zip(modern_features, feature_names):
        if feature in filtered_df.columns:
            has_feature = filtered_df[feature] == True
            count = has_feature.sum()
            categorical_cols.append('Modern Funkciók')
            categorical_data.append({
                'Kategória': name,
                'Darabszám': count,
                'Arány (%)': round(count / len(filtered_df) * 100, 1),
                'Átlag Ár (M Ft)': round(filtered_df[has_feature]['teljes_ar_millió'].mean(), 1) if count > 0 else 0,
                'Átlag Családbarát Pont': round(filtered_df[has_feature]['csaladbarati_pontszam'].mean(), 1) if count > 0 else 0
            })
    
    # 🏢 Hirdető típus elemzés
    if 'hirdeto_tipus' in filtered_df.columns:
        hirdeto_stats = filtered_df['hirdeto_tipus'].value_counts()
        for hirdeto, count in hirdeto_stats.head(3).items():
            categorical_cols.append('🏢 Hirdető Típus')
            categorical_data.append({
                'Kategória': str(hirdeto),
                'Darabszám': count,
                'Arány (%)': round(count / len(filtered_df) * 100, 1),
                'Átlag Ár (M Ft)': round(filtered_df[filtered_df['hirdeto_tipus'] == hirdeto]['teljes_ar_millió'].mean(), 1),
                'Átlag Családbarát Pont': round(filtered_df[filtered_df['hirdeto_tipus'] == hirdeto]['csaladbarati_pontszam'].mean(), 1)
            })
    
    # 🏗️ Emelet/Szint elemzés (lakásoknál)
    if 'szint' in filtered_df.columns:
        szint_stats = filtered_df['szint'].value_counts()
        for szint, count in szint_stats.head(5).items():
            if pd.notna(szint) and count >= 2:  # Csak ha legalább 2 ingatlan van
                categorical_cols.append('🏗️ Emelet/Szint')
                categorical_data.append({
                    'Kategória': str(szint),
                    'Darabszám': count,
                    'Arány (%)': round(count / len(filtered_df) * 100, 1),
                    'Átlag Ár (M Ft)': round(filtered_df[filtered_df['szint'] == szint]['teljes_ar_millió'].mean(), 1),
                    'Átlag Családbarát Pont': round(filtered_df[filtered_df['szint'] == szint]['csaladbarati_pontszam'].mean(), 1)
                })
    
    # 🌿 Erkély elemzés
    if 'erkely' in filtered_df.columns:
        erkely_stats = filtered_df['erkely'].value_counts()
        for erkely, count in erkely_stats.head(3).items():
            if pd.notna(erkely) and count >= 2:
                categorical_cols.append('🌿 Erkély')
                categorical_data.append({
                    'Kategória': str(erkely),
                    'Darabszám': count,
                    'Arány (%)': round(count / len(filtered_df) * 100, 1),
                    'Átlag Ár (M Ft)': round(filtered_df[filtered_df['erkely'] == erkely]['teljes_ar_millió'].mean(), 1),
                    'Átlag Családbarát Pont': round(filtered_df[filtered_df['erkely'] == erkely]['csaladbarati_pontszam'].mean(), 1)
                })
    
    # 🚗 Parkolás elemzés
    parkolas_cols = ['parkolas', 'parkolo']
    for park_col in parkolas_cols:
        if park_col in filtered_df.columns:
            park_stats = filtered_df[park_col].value_counts()
            for park, count in park_stats.head(3).items():
                if pd.notna(park) and count >= 2:
                    categorical_cols.append('🚗 Parkolás')
                    categorical_data.append({
                        'Kategória': str(park),
                        'Darabszám': count,
                        'Arány (%)': round(count / len(filtered_df) * 100, 1),
                        'Átlag Ár (M Ft)': round(filtered_df[filtered_df[park_col] == park]['teljes_ar_millió'].mean(), 1),
                        'Átlag Családbarát Pont': round(filtered_df[filtered_df[park_col] == park]['csaladbarati_pontszam'].mean(), 1)
                    })
            break  # Csak az első megtalált oszlopot használjuk
    
    # 🏗️ Építési év elemzés (évtized szerint)
    if 'epitesi_ev' in filtered_df.columns:
        # Évtized kategóriák létrehozása
        filtered_df_copy = filtered_df.copy()
        def get_decade(year_str):
            try:
                if pd.notna(year_str):
                    year = int(str(year_str).split('.')[0])  # pl. "2010.0" -> 2010
                    if year >= 2020:
                        return '2020-as évek'
                    elif year >= 2010:
                        return '2010-es évek'
                    elif year >= 2000:
                        return '2000-es évek'
                    elif year >= 1990:
                        return '1990-es évek'
                    elif year >= 1980:
                        return '1980-as évek'
                    elif year >= 1970:
                        return '1970-es évek'
                    else:
                        return 'Korábbi építés'
                return 'Nincs adat'
            except:
                return 'Nincs adat'
        
        filtered_df_copy['epitesi_evtized'] = filtered_df_copy['epitesi_ev'].apply(get_decade)
        decade_stats = filtered_df_copy['epitesi_evtized'].value_counts()
        for decade, count in decade_stats.head(5).items():
            if count >= 2 and decade != 'Nincs adat':
                categorical_cols.append('🏗️ Építési Évtized')
                categorical_data.append({
                    'Kategória': decade,
                    'Darabszám': count,
                    'Arány (%)': round(count / len(filtered_df) * 100, 1),
                    'Átlag Ár (M Ft)': round(filtered_df_copy[filtered_df_copy['epitesi_evtized'] == decade]['teljes_ar_millió'].mean(), 1),
                    'Átlag Családbarát Pont': round(filtered_df_copy[filtered_df_copy['epitesi_evtized'] == decade]['csaladbarati_pontszam'].mean(), 1)
                })
    
    # ❄️ Légkondícionáló elemzés
    if 'legkondicionalas' in filtered_df.columns:
        klima_stats = filtered_df['legkondicionalas'].value_counts()
        for klima, count in klima_stats.head(3).items():
            if pd.notna(klima) and count >= 2:
                categorical_cols.append('❄️ Légkondícionáló')
                categorical_data.append({
                    'Kategória': str(klima),
                    'Darabszám': count,
                    'Arány (%)': round(count / len(filtered_df) * 100, 1),
                    'Átlag Ár (M Ft)': round(filtered_df[filtered_df['legkondicionalas'] == klima]['teljes_ar_millió'].mean(), 1),
                    'Átlag Családbarát Pont': round(filtered_df[filtered_df['legkondicionalas'] == klima]['csaladbarati_pontszam'].mean(), 1)
                })
    
    # 🏠 Komfort szint elemzés
    if 'komfort' in filtered_df.columns:
        komfort_stats = filtered_df['komfort'].value_counts()
        for komfort, count in komfort_stats.head(4).items():
            if pd.notna(komfort) and count >= 2:
                categorical_cols.append('🏠 Komfort')
                categorical_data.append({
                    'Kategória': str(komfort),
                    'Darabszám': count,
                    'Arány (%)': round(count / len(filtered_df) * 100, 1),
                    'Átlag Ár (M Ft)': round(filtered_df[filtered_df['komfort'] == komfort]['teljes_ar_millió'].mean(), 1),
                    'Átlag Családbarát Pont': round(filtered_df[filtered_df['komfort'] == komfort]['csaladbarati_pontszam'].mean(), 1)
                })
    
    # 🔥 Fűtés típus elemzés
    if 'futes' in filtered_df.columns:
        futes_stats = filtered_df['futes'].value_counts()
        for futes, count in futes_stats.head(4).items():
            if pd.notna(futes) and count >= 2:
                categorical_cols.append('🔥 Fűtés')
                categorical_data.append({
                    'Kategória': str(futes)[:30],  # Max 30 karakter
                    'Darabszám': count,
                    'Arány (%)': round(count / len(filtered_df) * 100, 1),
                    'Átlag Ár (M Ft)': round(filtered_df[filtered_df['futes'] == futes]['teljes_ar_millió'].mean(), 1),
                    'Átlag Családbarát Pont': round(filtered_df[filtered_df['futes'] == futes]['csaladbarati_pontszam'].mean(), 1)
                })
    
    # 🌅 Kilátás elemzés
    if 'kilatas' in filtered_df.columns:
        kilatas_stats = filtered_df['kilatas'].value_counts()
        for kilatas, count in kilatas_stats.head(4).items():
            if pd.notna(kilatas) and count >= 2:
                categorical_cols.append('🌅 Kilátás')
                categorical_data.append({
                    'Kategória': str(kilatas),
                    'Darabszám': count,
                    'Arány (%)': round(count / len(filtered_df) * 100, 1),
                    'Átlag Ár (M Ft)': round(filtered_df[filtered_df['kilatas'] == kilatas]['teljes_ar_millió'].mean(), 1),
                    'Átlag Családbarát Pont': round(filtered_df[filtered_df['kilatas'] == kilatas]['csaladbarati_pontszam'].mean(), 1)
                })
    
    # 🌳 Kert elemzés (házaknál)
    if 'kert' in filtered_df.columns:
        kert_stats = filtered_df['kert'].value_counts()
        for kert, count in kert_stats.head(3).items():
            if pd.notna(kert) and count >= 2:
                categorical_cols.append('🌳 Kert')
                categorical_data.append({
                    'Kategória': str(kert),
                    'Darabszám': count,
                    'Arány (%)': round(count / len(filtered_df) * 100, 1),
                    'Átlag Ár (M Ft)': round(filtered_df[filtered_df['kert'] == kert]['teljes_ar_millió'].mean(), 1),
                    'Átlag Családbarát Pont': round(filtered_df[filtered_df['kert'] == kert]['csaladbarati_pontszam'].mean(), 1)
                })
    
    # 🏗️ Épület szintjei elemzés (házaknál)
    if 'epulet_szintjei' in filtered_df.columns:
        szintek_stats = filtered_df['epulet_szintjei'].value_counts()
        for szintek, count in szintek_stats.head(4).items():
            if pd.notna(szintek) and count >= 2:
                categorical_cols.append('🏗️ Épület Szintjei')
                categorical_data.append({
                    'Kategória': str(szintek),
                    'Darabszám': count,
                    'Arány (%)': round(count / len(filtered_df) * 100, 1),
                    'Átlag Ár (M Ft)': round(filtered_df[filtered_df['epulet_szintjei'] == szintek]['teljes_ar_millió'].mean(), 1),
                    'Átlag Családbarát Pont': round(filtered_df[filtered_df['epulet_szintjei'] == szintek]['csaladbarati_pontszam'].mean(), 1)
                })
    
    # ☀️ Napelem elemzés (házaknál)
    if 'napelem' in filtered_df.columns:
        napelem_stats = filtered_df['napelem'].value_counts()
        for napelem, count in napelem_stats.head(2).items():
            if pd.notna(napelem) and count >= 2:
                categorical_cols.append('☀️ Napelem')
                categorical_data.append({
                    'Kategória': str(napelem),
                    'Darabszám': count,
                    'Arány (%)': round(count / len(filtered_df) * 100, 1),
                    'Átlag Ár (M Ft)': round(filtered_df[filtered_df['napelem'] == napelem]['teljes_ar_millió'].mean(), 1),
                    'Átlag Családbarát Pont': round(filtered_df[filtered_df['napelem'] == napelem]['csaladbarati_pontszam'].mean(), 1)
                })
    
    if categorical_data:
        categorical_df = pd.DataFrame(categorical_data)
        categorical_df.insert(0, 'Típus', categorical_cols)
        st.dataframe(categorical_df, use_container_width=True)
    
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
            if pd.notna(link) and 'ingatlan.com/' in str(link):
                return str(link).split('/')[-1]
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
            'URL': ingatlan_url if ingatlan_url else 'N/A',  # Sima URL szöveg
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
    st.markdown("- A családbarát pontszám Több gyerekes családok igényeit figyelembe véve készült")
    st.markdown("- 150+ m² és 4+ szoba ideális nagyobb családok számára")  
    st.markdown("- A modern pontszám további kényelmi és technológiai elemeket értékel")
    st.markdown("- Az adatok 2025.08.21-i állapot szerint frissültek")

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
            return '#95A5A6'  # Szürke, ha nincs ár
        elif price <= 100:
            return '#2ECC71'  # Zöld - olcsó
        elif price <= 200:
            return '#F39C12'  # Narancs - közepes
        elif price <= 300:
            return '#E74C3C'  # Piros - drága  
        else:
            return '#8E44AD'  # Lila - nagyon drága
    
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
            
            # Nettó pontszám (Enhanced AI feature)
            netto_pont = row.get('netto_szoveg_pont', 0)
            
            # Színkód meghatározása ár szerint
            price_value = row.get('teljes_ar_millió', None)
            color = get_price_color(price_value)
            
            # Tooltip HTML tartalma
            tooltip_html = f"""
            <div style='width: 250px; font-family: Arial;'>
                <h4 style='margin: 0; color: #2E86AB;'>🏠 {cim}</h4>
                <hr style='margin: 5px 0;'>
                <p style='margin: 2px 0;'><b>💰 Ár:</b> {ar}</p>
                <p style='margin: 2px 0;'><b>📐 Terület:</b> {terulet}</p>
                <p style='margin: 2px 0;'><b>🏗️ Állapot:</b> {allapot}</p>
                <p style='margin: 2px 0;'><b>⭐ AI Pontszám:</b> {netto_pont:.1f}</p>
                <p style='margin: 5px 0;'><a href='{url}' target='_blank' style='color: #2E86AB;'>🔗 Hirdetés megnyitása</a></p>
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
    
    # Legenda hozzáadása - ár alapú színkódolás (DARK MODE kompatibilis)
    legend_html = f"""
    <div style='position: fixed; 
                top: 10px; right: 10px; width: 180px; height: auto; 
                background-color: rgba(40, 40, 40, 0.9); border:2px solid #666; z-index:9999; 
                font-size:12px; padding: 10px; color: white;'>
    <h4 style='margin-top:0; color: white;'>� Árszínkódolás</h4>
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
    st_folium(m, width=900, height=500, key=f"map_{location_name.lower().replace(' ', '_')}")

if __name__ == "__main__":
    main()
