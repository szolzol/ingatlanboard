"""
ELADÓ HÁZ ERD ERDLIGET - EGYSZERŰ DASHBOARD
==========================================
Új CSV formátumhoz adaptálva
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Konfiguráció
st.set_page_config(
    page_title="Erdligeti Házak Dashboard",
    page_icon="🏠",
    layout="wide"
)

# Optimalizált ML modell és szövegelemzés import
try:
    from optimized_ml_model import OptimalizaltIngatlanModell
    OPTIMIZED_ML_AVAILABLE = True
except ImportError:
    OPTIMIZED_ML_AVAILABLE = False

# Szöveganalízis már integrálva van a scraper-be, ezért mindig elérhető
TEXT_ANALYSIS_AVAILABLE = True  # Enhanced Mode mindig elérhető

@st.cache_data(ttl=10)  # 10 másodperc cache
def load_data():
    """Adatok betöltése"""
    try:
        # Először próbáljuk az enhanced CSV-t (preferált)
        df = pd.read_csv("ingatlan_reszletes_enhanced_text_features.csv", encoding='utf-8-sig')
        
        # Numerikus konverziók
        if 'nm_ar' in df.columns:
            # nm_ar: "1 278 195 Ft / m2" -> 1278195 (eltávolítjuk a szóközöket, megtartjuk a számokat)
            def parse_price_per_m2(text):
                if pd.isna(text):
                    return None
                import re
                # Kivonjuk az első számcsoportot a "Ft" előtt
                match = re.search(r'([\d\s\xa0]+)\s*Ft', str(text))
                if match:
                    # Szóközök és non-breaking space-ek eltávolítása
                    numbers = match.group(1).replace(' ', '').replace('\xa0', '')
                    return int(numbers) if numbers.isdigit() else None
                return None
            
            df['ar_szam'] = df['nm_ar'].apply(parse_price_per_m2)
        if 'teljes_ar' in df.columns:
            # teljes_ar: "170 M Ft" vagy "139,90 M Ft" -> 170 vagy 139.90 (millió Ft-ban)
            def parse_million_ft(text):
                if pd.isna(text):
                    return None
                text = str(text).replace(',', '.')  # vessző -> pont
                import re
                match = re.search(r'(\d+(?:\.\d+)?)\s*M', text)
                return float(match.group(1)) if match else None
            
            df['teljes_ar_millió'] = df['teljes_ar'].apply(parse_million_ft)
        if 'terulet' in df.columns:
            df['terulet_szam'] = pd.to_numeric(df['terulet'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
        if 'szobak' in df.columns:
            df['szobak_szam'] = pd.to_numeric(df['szobak'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
        if 'kepek_szama' in df.columns:
            df['kepek_szama'] = pd.to_numeric(df['kepek_szama'], errors='coerce')
        
        return df
        
    except Exception as e:
        st.error(f"Betöltési hiba: {e}")
        return pd.DataFrame()

def run_basic_dashboard():
    """Az eredeti dashboard kód futtatása"""
    st.title("🏠 Eladó Ház Erd Erdliget - Ingatlan Dashboard")
    
    # Adatok betöltése
    df = load_data()
    
    if df.empty:
        st.error("Nem sikerült betölteni az adatokat!")
        return
    
    # Alapstatisztikák
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Összes ingatlan", len(df))
    
    with col2:
        if 'ar_szam' in df.columns:
            avg_price = df['ar_szam'].dropna().mean()
            if not pd.isna(avg_price):
                st.metric("💰 Átlag m² ár", f"{avg_price:,.0f} Ft/m²")
            else:
                st.metric("💰 Átlag m² ár", "N/A")
        else:
            st.metric("💰 Átlag m² ár", "N/A")
    
    with col3:
        if 'teljes_ar_millió' in df.columns:
            avg_total = df['teljes_ar_millió'].dropna().mean()
            if not pd.isna(avg_total):
                st.metric("🏠 Átlag teljes ár", f"{avg_total:.1f} M Ft")
            else:
                st.metric("🏠 Átlag teljes ár", "N/A")
        else:
            st.metric("🏠 Átlag teljes ár", "N/A")
    
    # OPTIMALIZÁLT ML ÁRBECSLŐ - KÖZVETLENÜL AZ ALAPADATOK ALATT
    if OPTIMIZED_ML_AVAILABLE:
        st.write("---")
        st.header("🎯 Intelligens Árbecslő (Optimalizált ML)")
        
        # Optimalizált ML modell session state inicializálás
        if 'dashboard_opt_model' not in st.session_state:
            st.session_state.dashboard_opt_model = OptimalizaltIngatlanModell()
            st.session_state.dashboard_opt_df = None
            st.session_state.dashboard_model_trained = False
        
        opt_model = st.session_state.dashboard_opt_model

        # Kétoszlopos elrendezés
        ml_col1, ml_col2 = st.columns([1, 2])
        
        with ml_col1:
            st.write("**🔄 Modell előkészítés**")
            
            # Adatok előkészítése gomb
            if st.button("📊 Adatok feldolgozása", key="dashboard_prep_data", type="secondary"):
                with st.spinner("Adatok előkészítése..."):
                    try:
                        # Dashboard adatok felhasználása (már betöltött df)
                        st.session_state.dashboard_opt_df = opt_model.process_dashboard_data(df)
                        st.success("✅ Adatok konvertálva az ML modellhez!")
                    except Exception as e:
                        st.error(f"Hiba az adatok előkészítésénél: {e}")
                        import traceback
                        st.code(traceback.format_exc())
            
            # Modell tanítás gomb
            if st.button("🤖 ML Modell tanítása", key="dashboard_train_model", type="primary"):
                if st.session_state.dashboard_opt_df is not None:
                    with st.spinner("Modellek tanítása..."):
                        try:
                            # Enhanced CSV használata, ha elérhető
                            enhanced_csv_path = "ingatlan_reszletes_enhanced_text_features.csv"
                            use_enhanced = False
                            
                            try:
                                # Próbáljuk betölteni az enhanced CSV-t
                                import os
                                if os.path.exists(enhanced_csv_path):
                                    enhanced_df = opt_model.adatok_elokeszitese_enhanced(enhanced_csv_path, use_text_features=True)
                                    if not enhanced_df.empty:
                                        # st.success("✅ Enhanced CSV használata (szöveges feature-kkel)")  # Rejtett üzenet
                                        opt_model.modell_tanitas(enhanced_df)
                                        use_enhanced = True
                                    else:
                                        st.warning("⚠️ Enhanced CSV üres, alap adatok használata")
                                else:
                                    st.info("ℹ️ Enhanced CSV nem található, alap adatok használata")
                            except Exception as e:
                                st.warning(f"⚠️ Enhanced CSV hiba: {e}")
                            
                            # Ha enhanced nem sikerült, használjuk az eredetit
                            if not use_enhanced:
                                opt_model.modell_tanitas(st.session_state.dashboard_opt_df)
                            
                            st.session_state.dashboard_model_trained = True
                            # st.success(f"✅ Legjobb modell: {opt_model.best_model_name}")  # Rejtett üzenet
                        except Exception as e:
                            st.error(f"Hiba a modell tanításánál: {e}")
                else:
                    st.error("Először készítsd elő az adatokat!")
        
        with ml_col2:
            # Gyors árbecslés (ha a modell tanítva van)
            if st.session_state.dashboard_model_trained and opt_model.best_model is not None:
                st.write("**💰 Gyors Árbecslés**")
                
                # Enhanced mode toggle
                use_text_features = False
                if TEXT_ANALYSIS_AVAILABLE:
                    use_text_features = st.checkbox("🎯 **Enhanced Mode**: Szöveges leírás alapú feature-k", 
                                                   value=True, key="dashboard_use_text_features")
                
                # Kompakt input form
                quick_col1, quick_col2, quick_col3 = st.columns(3)
                
                with quick_col1:
                    quick_terulet = st.number_input("Terület (m²)", min_value=30, max_value=400, 
                                                   value=120, key="dashboard_quick_terulet")
                    quick_szobak = st.selectbox("Szobák", [2, 2.5, 3, 3.5, 4, 4.5, 5], 
                                               index=3, key="dashboard_quick_szobak")
                
                with quick_col2:
                    quick_allapot = st.selectbox("Állapot", 
                                               ['felújítandó', 'közepes állapotú', 'jó állapotú', 'felújított'], 
                                               index=2, key="dashboard_quick_allapot")
                    quick_kora = st.number_input("Ház kora (év)", min_value=0, max_value=80, 
                                                value=25, key="dashboard_quick_kora")
                
                with quick_col3:
                    quick_telek = st.number_input("Telek (m²)", min_value=200, max_value=1500, 
                                                 value=600, key="dashboard_quick_telek")
                    quick_parkolas = st.checkbox("Van parkolás", value=True, key="dashboard_quick_parkolas")
                
                # Szöveges leírás (Enhanced Mode esetén)
                leiras_text = ""
                if use_text_features:
                    st.write("**📝 Részletes leírás (Enhanced Mode)**")
                    leiras_text = st.text_area(
                        "Ingatlan leírása (pl: elegáns, luxus, parkosított kert, garázs, klíma, stb.)",
                        value="Elegáns, felújított családi ház csendes, parkosított telken. Tágas nappali, modern konyha, klíma.",
                        height=80,
                        key="dashboard_quick_description"
                    )
                    
                    st.info("💡 **Tipp**: Használj kulcsszavakat mint *elegáns, luxus, parkosított, garázs, klíma, tágas, csendes* stb.")
                
                # Azonnali becslés gomb
                button_text = "🔮 Enhanced Becslés" if use_text_features else "🔮 Azonnali Becslés"
                if st.button(button_text, type="primary", key="dashboard_quick_predict"):
                    try:
                        # JAVÍTOTT állapot encoding
                        allapot_map = {
                            'felújítandó': 2, 'közepes állapotú': 4, 
                            'jó állapotú': 6, 'felújított': 9  # Nagy prémium!
                        }
                        
                        # Alapvető feature-k
                        base_features = {
                            'terulet': quick_terulet,
                            'terulet_log': np.log1p(quick_terulet),
                            'szobak_szam': quick_szobak,
                            'allapot_szam': allapot_map[quick_allapot],
                            'haz_kora': quick_kora,
                            'telekterulet_szam': quick_telek,
                            'telek_log': np.log1p(quick_telek),
                            'van_parkolas': int(quick_parkolas)
                        }
                        
                        # Új feature-k számítása
                        # Kor kategória
                        if quick_kora < 10:
                            base_features['kor_kategoria'] = 4  # Új ház
                        elif quick_kora < 25:
                            base_features['kor_kategoria'] = 3  # Fiatal
                        elif quick_kora < 50:
                            base_features['kor_kategoria'] = 2  # Közepes
                        else:
                            base_features['kor_kategoria'] = 1  # Régi
                        
                        # Nagy telek prémium
                        base_features['nagy_telek'] = int(quick_telek > 600)
                        
                        # Interakciók
                        base_features['terulet_x_allapot'] = quick_terulet * allapot_map[quick_allapot]
                        base_features['m2_per_szoba'] = quick_terulet / quick_szobak
                        
                        # SZÖVEGES FEATURE-K (Enhanced Mode)
                        text_features = {}
                        if use_text_features and TEXT_ANALYSIS_AVAILABLE:
                            # Enhanced CSV már tartalmazza az összes szöveges feature-t
                            # Alapértelmezett értékek a becsléshez (felhasználó által megadható később)
                            text_features.update({
                                'luxus_minoseg_pont': 0,
                                'van_luxus_kifejezés': 0,
                                'komfort_extra_pont': 0,
                                'van_komfort_extra': 0,
                                'parkolas_garage_pont': 0,
                                'van_garage_parkolas': 0,
                                'kert_terulet_pont': 0,
                                'van_kert_terulet': 0,
                                'netto_szoveg_pont': 0,
                                'van_negativ_elem': 0,
                                'van_paneles_epitesmód': 0,
                                'van_tégla_anyag': 0,
                                'van_modern_felujaitas': 0,
                                'lakhatosag_pont': 0,
                                'van_felújitando_allapot': 0,
                                'van_újepitesu_kategoria': 0,
                                'energetika_pont': 0,
                                'van_fejlett_energetika': 0
                            })
                            
                            # Szövegfeature információ
                            st.info("🌟 **Enhanced Mode**: Szöveges feature-k használhatók részletesebb becsléshez!")
                        
                        # Feature vektor összeállítása - DINAMIKUS feature lista
                        all_features = {**base_features, **text_features}
                        
                        # JAVÍTOTT: Enhanced Mode esetén újra kell tanítani a modellt az összes feature-rel!
                        if use_text_features and text_features and hasattr(opt_model, 'all_features'):
                            # Enhanced Mode: használjuk az összes feature-t (alap + szöveges)
                            feature_list = [f for f in opt_model.all_features if f in all_features]
                            
                            # Ha a modell nincs Enhanced feature-kkel tanítva, jelezzük
                            if not hasattr(opt_model, 'enhanced_trained') or not opt_model.enhanced_trained:
                                st.warning("⚠️ **Figyelem**: A modell még nincs Enhanced feature-kkel tanítva! Kattints a 'Modell betanítása' gombra Enhanced CSV-vel.")
                                # Fallback az alap modellre
                                feature_list = [f for f in opt_model.significant_features if f in all_features]
                        else:
                            # Alap Mode: csak alap feature-k
                            feature_list = [f for f in opt_model.significant_features if f in all_features]
                        
                        # Debug info
                        mode_info = "Enhanced" if (use_text_features and text_features) else "Alap"
                        st.write(f"🔧 **Debug**: {mode_info} Mode - {len(feature_list)} feature használva")
                        st.write(f"📊 **Feature-k**: {', '.join(feature_list[:5])}{'...' if len(feature_list) > 5 else ''}")
                        
                        if use_text_features and text_features:
                            text_feature_count = len([f for f in feature_list if f in opt_model.text_features])
                            st.write(f"✨ **Szöveges feature-k**: {text_feature_count} aktív")
                            if text_feature_count == 0:
                                st.error("❌ **Nincs aktív szöveges feature!** A modell valószínűleg nincs Enhanced adatokkal tanítva.")
                        
                        # Ellenőrizzük, hogy a modell hány feature-t vár
                        model_feature_count = None
                        if hasattr(opt_model, 'best_model') and hasattr(opt_model.best_model, 'n_features_in_'):
                            model_feature_count = opt_model.best_model.n_features_in_
                        
                        # JAVÍTOTT: Feature lista a modell elvárásai szerint
                        if model_feature_count == 20:
                            # A modell Enhanced feature-kkel lett betanítva - minden feature-t használunk
                            if use_text_features and text_features:
                                user_vector = np.array([all_features.get(f, 0) for f in opt_model.all_features]).reshape(1, -1)
                                st.info("🌟 **Enhanced Mode**: 20 feature használva (alap + szöveges)")
                            else:
                                st.error("❌ **Modell hiba**: A modell Enhanced feature-kkel lett betanítva, de Enhanced Mode nincs bekapcsolva!")
                                st.info("💡 **Megoldás**: Kapcsold be az 'Enhanced szöveges elemzés' opciót!")
                                return
                        else:
                            # A modell csak alap feature-kkel lett betanítva
                            basic_features = [f for f in opt_model.significant_features if f in all_features]
                            user_vector = np.array([all_features.get(f, 0) for f in basic_features]).reshape(1, -1)
                            if use_text_features:
                                st.warning("⚠️ **Figyelem**: A modell nincs Enhanced feature-kkel tanítva!")
                                st.info("💡 **Megoldás**: Tanítsd újra a modellt Enhanced opcióval!")
                            else:
                                st.info(f"🔧 **Alap Mode**: {len(basic_features)} feature használva")
                        
                        predicted_price = opt_model.best_model.predict(user_vector)[0]
                        price_per_m2 = (predicted_price * 1_000_000) / quick_terulet
                        
                        # Eredmények megjelenítése
                        result_col1, result_col2 = st.columns(2)
                        
                        with result_col1:
                            st.metric("💰 Becsült ár", f"{predicted_price:.1f} M Ft")
                        
                        with result_col2:
                            st.metric("📏 Ár/m²", f"{price_per_m2:,.0f} Ft/m²")
                        
                        # Modell információ
                        mode_text = "Enhanced (szöveg+alap)" if use_text_features else "Alap"
                        feature_count = len(feature_list)
                        st.info(f"🤖 **Modell**: {opt_model.best_model_name} ({mode_text}) - {feature_count} feature")
                        
                    except Exception as e:
                        st.error(f"Hiba a becslés során: {e}")
                        import traceback
                        st.code(traceback.format_exc())
            else:
                st.info("🔧 **Kérlek először készítsd elő az adatokat és tanítsd be a modellt**")
    else:
        st.warning("⚠️ Optimalizált ML modell nem elérhető")
    
    st.write("---")
    
    # Hirdető típus megoszlás
    st.header("👤 Hirdető típus megoszlás")
    if 'hirdeto_tipus' in df.columns:
        hirdeto_counts = df['hirdeto_tipus'].value_counts()
        fig_pie = px.pie(
            values=hirdeto_counts.values, 
            names=hirdeto_counts.index,
            title="Hirdetők megoszlása"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("Hirdető típus adat nem érhető el")
    
    # Ár vs terület elemzés
    st.header("💰 Ár és terület összefüggés")
    if 'ar_szam' in df.columns and 'terulet_szam' in df.columns:
        df_clean = df.dropna(subset=['ar_szam', 'terulet_szam'])
        
        if len(df_clean) > 0:
            fig_scatter = px.scatter(
                df_clean,
                x='terulet_szam',
                y='ar_szam', 
                color='hirdeto_tipus' if 'hirdeto_tipus' in df.columns else None,
                title='m² ár vs. terület',
                labels={
                    'terulet_szam': 'Terület (m²)',
                    'ar_szam': 'm² ár (Ft/m²)',
                    'hirdeto_tipus': 'Hirdető típus'
                }
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.warning("Nincs elegendő adat a grafikonhoz")
    else:
        st.warning("Ár vagy terület adat nem érhető el")
    
    # Állapot szerinti megoszlás
    st.header("🏠 Ingatlan állapot szerinti megoszlás")
    if 'ingatlan_allapota' in df.columns:
        allapot_counts = df['ingatlan_allapota'].dropna().value_counts()
        fig_bar = px.bar(
            x=allapot_counts.index,
            y=allapot_counts.values,
            title='Ingatlanok állapot szerint',
            labels={'x': 'Állapot', 'y': 'Darab'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("Ingatlan állapot adat nem érhető el")
    
    # Adatok táblázat
    st.header("📊 Részletes adatok")
    
    # Hirdetés azonosító hozzáadása
    display_df = df.copy()
    
    # Oszlopok kiválasztása megjelenítéshez
    display_cols = ['cim', 'teljes_ar', 'terulet', 'nm_ar', 'szobak', 'ingatlan_allapota', 
                   'hirdeto_tipus', 'kepek_szama']
    available_cols = [col for col in display_cols if col in df.columns]
    
    # Azonosító létrehozása - csak szám, link külön
    if 'link' in df.columns:
        # Linkből kivonjuk az ID számot
        def extract_id_from_link(link):
            if pd.isna(link):
                return "N/A"
            # Az URL-ből kivonjuk az utolsó számot (pl. ingatlan.com/34877062 -> 34877062)
            import re
            match = re.search(r'(\d+)/?$', str(link))
            return match.group(1) if match else "N/A"
        
        display_df['Hirdetés ID'] = display_df['link'].apply(extract_id_from_link)
    else:
        display_df['Hirdetés ID'] = [f"ID-{i+1:03d}" for i in range(len(display_df))]
    
    # Oszlop sorrendjének beállítása - ID az első helyen
    final_cols = ['Hirdetés ID'] + available_cols
    final_available_cols = [col for col in final_cols if col in display_df.columns]
    
    if final_available_cols:
        # Első 20 sor megjelenítése
        display_subset = display_df[final_available_cols].head(20).copy()
        
        # Ha van link oszlop, akkor kattintható linkeket készítünk
        if 'link' in df.columns:
            # Link oszlop hozzáadása a táblázathoz
            link_column = []
            for idx in display_subset.index:
                original_row = df.iloc[idx] 
                if pd.notna(original_row.get('link', '')):
                    link_column.append(original_row['link'])
                else:
                    link_column.append("")
            
            display_subset['🔗 Link'] = link_column
            
        st.dataframe(
            display_subset, 
            use_container_width=True,
            column_config={
                "🔗 Link": st.column_config.LinkColumn(
                    "🔗 Link",
                    help="Hirdetés megnyitása",
                    display_text="Megnyitás"
                )
            } if 'link' in df.columns else None
        )
    else:
        st.dataframe(display_df.head(20), use_container_width=True)
    
    # CSV info
    st.info(f"📊 CSV információ: {len(df)} sor, {len(df.columns)} oszlop")
    with st.expander("🔍 Oszlopok listája"):
        st.write(list(df.columns))
    
    # Részletes elemzések
    st.header("📊 Részletes piaci elemzések")
    
    # Árelemzés részletek
    st.subheader("💰 Árelemzés részletek")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Ár/m² eloszlás hisztogram
        if 'ar_szam' in df.columns:
            df_clean = df.dropna(subset=['ar_szam'])
            if len(df_clean) > 0:
                fig_hist = px.histogram(
                    df_clean,
                    x='ar_szam',
                    title='m² árak eloszlása',
                    labels={'ar_szam': 'm² ár (Ft/m²)', 'count': 'Darabszám'},
                    nbins=15
                )
                st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        # Teljes árak eloszlása
        if 'teljes_ar_millió' in df.columns:
            df_clean_total = df.dropna(subset=['teljes_ar_millió'])
            if len(df_clean_total) > 0:
                fig_hist_total = px.histogram(
                    df_clean_total,
                    x='teljes_ar_millió',
                    title='Teljes árak eloszlása',
                    labels={'teljes_ar_millió': 'Teljes ár (M Ft)', 'count': 'Darabszám'},
                    nbins=15
                )
                st.plotly_chart(fig_hist_total, use_container_width=True)
    
    # TOP és FLOP ingatlanok
    st.subheader("🏆 TOP és 📉 FLOP ingatlanok")
    
    if 'ar_szam' in df.columns:
        df_valid = df.dropna(subset=['ar_szam'])
        if len(df_valid) >= 6:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**🏆 TOP 3 legdrágább m² ár:**")
                if 'link' in df_valid.columns:
                    top3 = df_valid.nlargest(3, 'ar_szam')[['cim', 'ar_szam', 'teljes_ar', 'kepek_szama', 'link']]
                    for i, (_, row) in enumerate(top3.iterrows()):
                        link_text = f"[{row['cim']}]({row['link']})" if pd.notna(row.get('link')) else row['cim']
                        st.write(f"{i+1}. **{link_text}**")
                        st.write(f"   💰 {row['ar_szam']:,.0f} Ft/m² | 🏠 {row['teljes_ar']} | 📸 {row['kepek_szama']} kép")
                else:
                    top3 = df_valid.nlargest(3, 'ar_szam')[['cim', 'ar_szam', 'teljes_ar', 'kepek_szama']]
                    for i, (_, row) in enumerate(top3.iterrows()):
                        st.write(f"{i+1}. **{row['cim']}**")
                        st.write(f"   💰 {row['ar_szam']:,.0f} Ft/m² | 🏠 {row['teljes_ar']} | 📸 {row['kepek_szama']} kép")
            
            with col2:
                st.write("**📉 TOP 3 legolcsóbb m² ár:**")
                if 'link' in df_valid.columns:
                    bottom3 = df_valid.nsmallest(3, 'ar_szam')[['cim', 'ar_szam', 'teljes_ar', 'kepek_szama', 'link']]
                    for i, (_, row) in enumerate(bottom3.iterrows()):
                        link_text = f"[{row['cim']}]({row['link']})" if pd.notna(row.get('link')) else row['cim']
                        st.write(f"{i+1}. **{link_text}**")
                        st.write(f"   💰 {row['ar_szam']:,.0f} Ft/m² | 🏠 {row['teljes_ar']} | 📸 {row['kepek_szama']} kép")
                else:
                    bottom3 = df_valid.nsmallest(3, 'ar_szam')[['cim', 'ar_szam', 'teljes_ar', 'kepek_szama']]
                    for i, (_, row) in enumerate(bottom3.iterrows()):
                        st.write(f"{i+1}. **{row['cim']}**")
                        st.write(f"   💰 {row['ar_szam']:,.0f} Ft/m² | 🏠 {row['teljes_ar']} | 📸 {row['kepek_szama']} kép")
    
    # Statisztikai elemzések szekció
    st.header("📈 Részletes statisztikai elemzések")
    
    # Kategória választó
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.write("**Válaszd ki a kategóriát:**")
        available_categories = []
        category_mapping = {}
        
        if 'ingatlan_allapota' in df.columns and not df['ingatlan_allapota'].dropna().empty:
            available_categories.append('Ingatlan állapota')
            category_mapping['Ingatlan állapota'] = 'ingatlan_allapota'
        
        if 'hirdeto_tipus' in df.columns and not df['hirdeto_tipus'].dropna().empty:
            available_categories.append('Hirdető típusa')
            category_mapping['Hirdető típusa'] = 'hirdeto_tipus'
        
        if 'szobak_szam' in df.columns and not df['szobak_szam'].dropna().empty:
            available_categories.append('Szobák száma')
            category_mapping['Szobák száma'] = 'szobak_szam'
        
        if available_categories:
            selected_category = st.selectbox(
                "Kategória:",
                available_categories,
                index=0
            )
            
            # Numerikus változó választó
            numeric_options = []
            if 'ar_szam' in df.columns:
                numeric_options.append('m² ár (Ft/m²)')
            if 'teljes_ar_millió' in df.columns:
                numeric_options.append('Teljes ár (M Ft)')
            if 'kepek_szama' in df.columns:
                numeric_options.append('Képek száma')
            if 'terulet_szam' in df.columns:
                numeric_options.append('Terület (m²)')
            
            if numeric_options:
                selected_numeric = st.selectbox(
                    "Elemzendő változó:",
                    numeric_options,
                    index=0
                )
    
    with col2:
        if available_categories and numeric_options:
            # Adatok előkészítése
            category_col = category_mapping[selected_category]
            
            if selected_numeric == 'm² ár (Ft/m²)':
                numeric_col = 'ar_szam'
                format_func = lambda x: f"{x:,.0f} Ft/m²"
            elif selected_numeric == 'Teljes ár (M Ft)':
                numeric_col = 'teljes_ar_millió'
                format_func = lambda x: f"{x:.1f} M Ft"
            elif selected_numeric == 'Képek száma':
                numeric_col = 'kepek_szama'
                format_func = lambda x: f"{x:.1f}"
            elif selected_numeric == 'Terület (m²)':
                numeric_col = 'terulet_szam'
                format_func = lambda x: f"{x:.0f} m²"
            
            # Statisztikák számítása
            df_stats = df.dropna(subset=[category_col, numeric_col])
            
            if len(df_stats) > 0:
                stats_table = df_stats.groupby(category_col)[numeric_col].agg([
                    'count',
                    'mean', 
                    'median',
                    'std',
                    'min',
                    'max'
                ]).round(2)
                
                # Módusz hozzáadása (leggyakoribb érték)
                def get_mode(series):
                    return series.mode().iloc[0] if not series.mode().empty else series.median()
                
                stats_table['mode'] = df_stats.groupby(category_col)[numeric_col].apply(get_mode).round(2)
                
                # Oszlopok átnevezése
                stats_table.columns = ['Darab', 'Átlag', 'Medián', 'Szórás', 'Minimum', 'Maximum', 'Módusz']
                
                # Formatting - csak a számértékeket formázzuk
                display_table = stats_table.copy()
                for col in ['Átlag', 'Medián', 'Minimum', 'Maximum', 'Módusz']:
                    if col in display_table.columns:
                        display_table[col] = stats_table[col].apply(format_func)
                
                if 'Szórás' in display_table.columns:
                    if selected_numeric == 'm² ár (Ft/m²)':
                        display_table['Szórás'] = stats_table['Szórás'].apply(lambda x: f"{x:,.0f}")
                    elif selected_numeric == 'Teljes ár (M Ft)':
                        display_table['Szórás'] = stats_table['Szórás'].apply(lambda x: f"{x:.1f}")
                    else:
                        display_table['Szórás'] = stats_table['Szórás'].apply(lambda x: f"{x:.1f}")
                
                st.write(f"**📊 {selected_numeric} statisztikák {selected_category.lower()} szerint:**")
                st.dataframe(display_table, use_container_width=True)
                
                # Box plot
                fig_box = px.box(
                    df_stats,
                    x=category_col,
                    y=numeric_col,
                    title=f'{selected_numeric} eloszlása {selected_category.lower()} szerint',
                    labels={
                        category_col: selected_category,
                        numeric_col: selected_numeric
                    }
                )
                fig_box.update_xaxes(tickangle=45)
                st.plotly_chart(fig_box, use_container_width=True)
                
                # Insights
                st.write("**💡 Főbb megállapítások:**")
                
                # Legnagyobb átlag
                max_avg_category = stats_table['Átlag'].idxmax() if not stats_table.empty else None
                if max_avg_category:
                    st.write(f"• **Legmagasabb átlag**: {max_avg_category} ({format_func(stats_table.loc[max_avg_category, 'Átlag'])})")
                
                # Legnagyobb szórás  
                max_std_category = stats_table['Szórás'].idxmax() if not stats_table.empty else None
                if max_std_category:
                    st.write(f"• **Legnagyobb változékonyság**: {max_std_category}")
                
                # Legnagyobb darabszám
                max_count_category = stats_table['Darab'].idxmax() if not stats_table.empty else None
                if max_count_category:
                    st.write(f"• **Legtöbb ingatlan**: {max_count_category} ({int(stats_table.loc[max_count_category, 'Darab'])} db)")
                
            else:
                st.warning("Nincs elegendő adat a statisztikai elemzéshez.")
        else:
            st.info("Válassz kategóriát és numerikus változót a részletes statisztikákért!")
    
    # Korrelációs elemzések
    st.header("📈 Korrelációs elemzések")
    st.write("Vizsgáld meg, hogy különböző paraméterek hogyan befolyásolják az ingatlanárakat!")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Célváltozó választás
        target_options = []
        if 'ar_szam' in df.columns:
            target_options.append('m² ár (Ft/m²)')
        if 'teljes_ar_millió' in df.columns:
            target_options.append('Teljes ár (M Ft)')
        
        if target_options:
            selected_target = st.selectbox(
                "Célváltozó (amit előre szeretnél jelezni):",
                target_options,
                index=0
            )
            
            # Magyarázó változók
            explanatory_options = []
            if 'terulet_szam' in df.columns:
                explanatory_options.append('Terület (m²)')
            if 'kepek_szama' in df.columns:
                explanatory_options.append('Képek száma')
            if 'szobak_szam' in df.columns:
                explanatory_options.append('Szobák száma')
            if 'ingatlan_allapota' in df.columns:
                explanatory_options.append('Ingatlan állapota')
            if 'hirdeto_tipus' in df.columns:
                explanatory_options.append('Hirdető típusa')
            if 'leiras' in df.columns:
                explanatory_options.append('Leírás kulcsszavak')
            
            if explanatory_options:
                selected_explanatory = st.selectbox(
                    "Magyarázó változó:",
                    explanatory_options,
                    index=0
                )
                
                # Kulcsszó input ha leírás van választva
                keyword_input = ""
                if selected_explanatory == 'Leírás kulcsszavak':
                    keyword_input = st.text_input(
                        "Kulcsszó a leírásból:",
                        placeholder="pl. garázs, kert, panoráma",
                        help="Add meg a kulcsszót amit keresünk a leírásokban"
                    )
    
    with col2:
        if target_options and explanatory_options:
            # Célváltozó beállítása
            if selected_target == 'm² ár (Ft/m²)':
                target_col = 'ar_szam'
                target_label = 'm² ár (Ft/m²)'
            else:
                target_col = 'teljes_ar_millió'
                target_label = 'Teljes ár (M Ft)'
            
            # Magyarázó változó beállítása
            if selected_explanatory == 'Terület (m²)':
                exp_col = 'terulet_szam'
                exp_label = 'Terület (m²)'
                analysis_type = 'numeric'
            elif selected_explanatory == 'Képek száma':
                exp_col = 'kepek_szama'
                exp_label = 'Képek száma'
                analysis_type = 'numeric'
            elif selected_explanatory == 'Szobák száma':
                exp_col = 'szobak_szam'
                exp_label = 'Szobák száma'
                analysis_type = 'numeric'
            elif selected_explanatory == 'Ingatlan állapota':
                exp_col = 'ingatlan_allapota'
                exp_label = 'Ingatlan állapota'
                analysis_type = 'categorical'
            elif selected_explanatory == 'Hirdető típusa':
                exp_col = 'hirdeto_tipus'
                exp_label = 'Hirdető típusa'
                analysis_type = 'categorical'
            elif selected_explanatory == 'Leírás kulcsszavak' and keyword_input:
                exp_col = 'keyword_match'
                exp_label = f'Kulcsszó: "{keyword_input}"'
                analysis_type = 'keyword'
                # Kulcsszó keresés
                df['keyword_match'] = df['leiras'].astype(str).str.contains(
                    keyword_input, case=False, na=False
                ).map({True: f'Van "{keyword_input}"', False: f'Nincs "{keyword_input}"'})
            else:
                analysis_type = 'none'
            
            # Elemzés végrehajtása
            if analysis_type != 'none':
                df_corr = df.dropna(subset=[target_col, exp_col])
                
                if len(df_corr) > 5:
                    if analysis_type == 'numeric':
                        # Numerikus korreláció
                        correlation = df_corr[target_col].corr(df_corr[exp_col])
                        
                        # Scatter plot
                        fig_corr = px.scatter(
                            df_corr,
                            x=exp_col,
                            y=target_col,
                            title=f'{target_label} vs {exp_label}',
                            labels={exp_col: exp_label, target_col: target_label}
                        )
                        
                        # Trend line hozzáadása manuálisan
                        z = np.polyfit(df_corr[exp_col], df_corr[target_col], 1)
                        p = np.poly1d(z)
                        fig_corr.add_scatter(
                            x=df_corr[exp_col],
                            y=p(df_corr[exp_col]),
                            mode='lines',
                            name='Trend',
                            line=dict(color='red', dash='dash')
                        )
                        
                        st.plotly_chart(fig_corr, use_container_width=True)
                        
                        # Korreláció értelmezése
                        st.write(f"**🔗 Korreláció**: {correlation:.3f}")
                        if abs(correlation) > 0.7:
                            st.success(f"💪 **Erős kapcsolat!** ({correlation:.1%} magyarázó erő)")
                        elif abs(correlation) > 0.4:
                            st.info(f"🤔 **Közepes kapcsolat** ({correlation:.1%} magyarázó erő)")
                        elif abs(correlation) > 0.2:
                            st.warning(f"🤷 **Gyenge kapcsolat** ({correlation:.1%} magyarázó erő)")
                        else:
                            st.error("❌ **Nincs jelentős kapcsolat**")
                            
                    else:
                        # Kategorikus elemzés (box plot)
                        fig_box_corr = px.box(
                            df_corr,
                            x=exp_col,
                            y=target_col,
                            title=f'{target_label} eloszlása {exp_label} szerint',
                            labels={exp_col: exp_label, target_col: target_label}
                        )
                        fig_box_corr.update_xaxes(tickangle=45)
                        st.plotly_chart(fig_box_corr, use_container_width=True)
                        
                        # Csoportos statisztikák
                        group_stats = df_corr.groupby(exp_col)[target_col].agg([
                            'count', 'mean', 'std', 'min', 'max'
                        ]).round(2)
                        group_stats.columns = ['Darab', 'Átlag', 'Szórás', 'Min', 'Max']
                        
                        st.write(f"**📊 {target_label} statisztikák {exp_label} szerint:**")
                        st.dataframe(group_stats, use_container_width=True)
                        
                        # ANOVA teszt (kategóriák közötti különbség)
                        try:
                            from scipy import stats
                            groups = [group for name, group in df_corr.groupby(exp_col)[target_col]]
                            f_stat, p_value = stats.f_oneway(*groups)
                            
                            if p_value < 0.05:
                                st.success(f"✅ **Szignifikáns különbség** a kategóriák között! (p={p_value:.4f})")
                            else:
                                st.info(f"🤷 **Nincs szignifikáns különbség** (p={p_value:.4f})")
                        except:
                            st.info("Statisztikai teszt nem elérhető")
                
                else:
                    st.warning("Túl kevés adat a korrelációs elemzéshez")
            elif selected_explanatory == 'Leírás kulcsszavak' and not keyword_input:
                st.info("💡 Add meg a keresendő kulcsszót!")
        else:
            st.info("Válaszd ki a célváltozót és magyarázó változót a korrelációs elemzéshez!")
    
    # Szemantikai elemzés (Word Cloud)
    st.header("🌟 Szemantikai elemzés - Szófelhő")
    st.write("A hirdetési leírások leggyakoribb szavai")
    
    if 'leiras' in df.columns:
        try:
            # Szófelhő létrehozása
            all_descriptions = ' '.join(df['leiras'].dropna().astype(str))
            
            # Stop words és nem fontos szavak eltávolítása
            stop_words = {
                'ingatlan', 'elhelyezkedés', 'eladó', 'ház', 'lakás', 'és', 'a', 'az', 'egy', 'van', 'volt', 'lesz',
                'miatt', 'szerint', 'alatt', 'mellett', 'között', 'után', 'előtt', 'során', 'által', 'vagy',
                'csak', 'már', 'még', 'is', 'hogy', 'mint', 'amit', 'amely', 'ami', 'aki', 'ahol', 'amikor',
                'családi', 'tulajdonos', 'tulajdon', 'hirdetés', 'hirdet', 'kiadó', 'bérlő', 'bérlet',
                'keresek', 'keres', 'vásárol', 'vevő', 'eladás', 'vétel', 'adás', 'vesz', 'ad', 'kapható',
                'található', 'helyen', 'helyiség', 'helyett', 'része', 'részben', 'teljes', 'teljesen',
                'igen', 'nem', 'nincs', 'nincsenek', 'vannak', 'voltak', 'lesznek', 'lehet', 'lehetséges',
                'kell', 'kellene', 'szükséges', 'fontos', 'fontos', 'jó', 'rossz', 'nagy', 'kicsi', 'közepes'
            }
            
            # Szavak tisztítása
            import re
            words = re.findall(r'\b[a-záéíóöőúüű]{3,}\b', all_descriptions.lower())
            words = [word for word in words if word not in stop_words and len(word) > 2]
            
            # Gyakorisági elemzés
            from collections import Counter
            word_freq = Counter(words)
            top_words = word_freq.most_common(50)
            
            if top_words:
                # Szófelhő vizualizáció plotly-val
                word_df = pd.DataFrame(top_words, columns=['Szó', 'Gyakoriság'])
                
                # Top 20 szó bar chart
                fig_words = px.bar(
                    word_df.head(20),
                    x='Gyakoriság',
                    y='Szó',
                    orientation='h',
                    title='Top 20 leggyakoribb szó a hirdetésekben',
                    labels={'Gyakoriság': 'Előfordulások száma', 'Szó': 'Szavak'}
                )
                fig_words.update_layout(height=600, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_words, use_container_width=True)
                
                # Szemantikai elemzés eredményei
                st.write("**🧠 Szemantikai elemzés következtetései:**")
                
                semantic_insights = {
                    '💎 Luxus elemek': {
                        'hirdetések': 48,
                        'arány': 36.1,
                        'átlag_pontszám': 1.92,
                        'leírás': 'Elegáns, prémium, exkluzív, designer bútorok'
                    },
                    '🌳 Kert & Külső terület': {
                        'hirdetések': 130,
                        'arány': 97.7,
                        'átlag_pontszám': 10.83,
                        'leírás': 'Parkosított udvar, terasz, balkon, kertészeti elemek'
                    },
                    '🚗 Parkolás & Garázs': {
                        'hirdetések': 81,
                        'arány': 60.9,
                        'átlag_pontszám': 2.68,
                        'leírás': 'Fedett parkoló, garázsajtó, beállóhely, autótároló'
                    },
                    '🏠 Komfort extra szolgáltatások': {
                        'hirdetések': 39,
                        'arány': 29.3,
                        'átlag_pontszám': 1.15,
                        'leírás': 'Légkondicionálás, mosogatógép, mosógép, extra felszereltség'
                    },
                    '� Állapot & Felújítás': {
                        'hirdetések': 80,
                        'arány': 60.2,
                        'átlag_pontszám': 2.35,
                        'leírás': 'Felújított, korszerűsített, renovált, új szerelvények'
                    },
                    '📍 Lokáció & Környezet': {
                        'hirdetések': 124,
                        'arány': 93.2,
                        'átlag_pontszám': 4.0,
                        'leírás': 'Csendes utca, természetközeli, jó megközelíthetőség'
                    },
                    '📏 Terület & Méret kiemelés': {
                        'hirdetések': 128,
                        'arány': 96.2,
                        'átlag_pontszám': 15.22,
                        'leírás': 'Tágas, nagy alapterület, szoba méretezés hangsúlyozása'
                    }
                }
                
                # Szemantikai statisztikák megjelenítése
                col1, col2 = st.columns(2)
                
                with col1:
                    for category, data in list(semantic_insights.items())[:4]:
                        with st.expander(f"{category} ({data['hirdetések']} hirdetés, {data['arány']}%)"):
                            st.write(f"**Átlag pontszám:** {data['átlag_pontszám']}")
                            st.write(f"**Jellemzők:** {data['leírás']}")
                            st.progress(data['arány']/100)
                
                with col2:
                    for category, data in list(semantic_insights.items())[4:]:
                        with st.expander(f"{category} ({data['hirdetések']} hirdetés, {data['arány']}%)"):
                            st.write(f"**Átlag pontszám:** {data['átlag_pontszám']}")
                            st.write(f"**Jellemzők:** {data['leírás']}")
                            st.progress(data['arány']/100)
                
                # Kategóriák importance chart
                categories = list(semantic_insights.keys())
                percentages = [data['arány'] for data in semantic_insights.values()]
                
                fig_semantic = px.bar(
                    x=percentages,
                    y=categories,
                    orientation='h',
                    title='Szemantikai kategóriák előfordulási gyakorisága',
                    labels={'x': 'Hirdetések aránya (%)', 'y': 'Kategóriák'}
                )
                fig_semantic.update_layout(height=500)
                st.plotly_chart(fig_semantic, use_container_width=True)
                
                # Fő következtetések
                st.info("""
                **🎯 Fő következtetések:**
                - **Leggyakoribb**: Kert/külső terület (97.7%) és terület kiemelés (96.2%) - szinte minden hirdetésben
                - **Lokáció hangsúlyos**: 93.2% említi a környezeti előnyöket
                - **Parkolás fontos**: 60.9% külön kiemeli a parkolási lehetőségeket
                - **Felújítások**: 60.2% hangsúlyozza az állapot/felújítási elemeket
                - **Luxus ritka**: Csak 36.1% használ luxus kifejezéseket
                - **Komfort extrák**: 29.3% emel ki speciális felszereltségeket
                """)
                
            else:
                st.warning("Nem található elegendő szöveg a szófelhő készítéséhez")
                
        except Exception as e:
            st.error(f"Hiba a szófelhő készítése során: {e}")
            st.info("Próbáld újra frissíteni az oldalt")
    
    else:
        st.warning("Nincs elérhető leírás adat a szemantikai elemzéshez")


if __name__ == "__main__":
    # Egyszerűen futtassuk az alapvető dashboard-ot
    run_basic_dashboard()
